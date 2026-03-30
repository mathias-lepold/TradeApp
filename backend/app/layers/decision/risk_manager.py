"""
Decision Engine: RiskManager
Berechnet optimale Positionsgrösse unter Berücksichtigung aller Risikoregeln.
"""
from __future__ import annotations

from typing import Optional
from app.domain.recommendation import PositionSizing
from app.domain.regime_state import RegimeState


class RiskManager:
    """
    Berechnet regelkonforme Positionsgrößen.

    Regeln (konfigurierbar):
      - Max 1% Portfoliorisiko pro Trade (Stopp-Distanz)
      - Max 10% des Portfolios in eine Position
      - Regime-abhängiges Maximum
      - Optional: Kelly-Kriterium
    """

    def __init__(
        self,
        max_risk_per_trade_pct: float = 1.0,
        max_position_pct: float = 10.0,
        stamp_tax_rate: float = 0.00075,  # Schweizer Stempelsteuer
    ) -> None:
        self.max_risk_per_trade_pct = max_risk_per_trade_pct
        self.max_position_pct = max_position_pct
        self.stamp_tax_rate = stamp_tax_rate

    def calculate_sizing(
        self,
        entry_price: float,
        stop_loss: float,
        portfolio_value_chf: float,
        regime: RegimeState,
        fx_rate: float = 1.0,  # USD→CHF (1.0 wenn schon CHF)
        win_rate: Optional[float] = None,  # Für Kelly-Kriterium
        avg_win_loss_ratio: Optional[float] = None,
    ) -> PositionSizing:
        """
        Berechnet die optimale Positionsgrösse.

        Args:
            entry_price:         Einstiegspreis
            stop_loss:           Stop-Loss-Preis
            portfolio_value_chf: Gesamtportfolio in CHF
            regime:              Aktuelles Marktregime
            fx_rate:             FX-Rate für Umrechnung in CHF
            win_rate:            Historische Trefferquote (für Kelly)
            avg_win_loss_ratio:  Durschn. Gewinn/Verlust-Ratio (für Kelly)
        """
        risk_per_share = abs(entry_price - stop_loss)
        if risk_per_share == 0:
            risk_per_share = entry_price * 0.05  # Fallback: 5% Abstand

        # 1%-Regel: Max CHF-Risiko pro Trade
        max_risk_chf = portfolio_value_chf * (self.max_risk_per_trade_pct / 100)
        risk_based_shares = max_risk_chf / (risk_per_share * fx_rate)
        risk_based_chf = risk_based_shares * entry_price * fx_rate

        # Regime-Limit
        regime_max_chf = portfolio_value_chf * (regime.max_position_size_pct / 100)

        # Absolutes Maximum
        abs_max_chf = portfolio_value_chf * (self.max_position_pct / 100)

        # Kleinsten Wert nehmen
        suggested_chf = min(risk_based_chf, regime_max_chf, abs_max_chf)
        suggested_shares = suggested_chf / (entry_price * fx_rate)
        suggested_pct = (suggested_chf / portfolio_value_chf) * 100

        # Kelly-Kriterium (optional)
        kelly = None
        if win_rate and avg_win_loss_ratio:
            kelly = max(0.0, win_rate - (1 - win_rate) / avg_win_loss_ratio)
            kelly = round(kelly * 0.5, 3)  # Half-Kelly für Sicherheit

        return PositionSizing(
            suggested_pct=round(suggested_pct, 2),
            suggested_chf=round(suggested_chf, 2),
            suggested_shares=round(suggested_shares, 4),
            max_pct_by_regime=regime.max_position_size_pct,
            kelly_fraction=kelly,
            risk_per_trade_chf=round(max_risk_chf, 2),
            risk_pct_of_portfolio=self.max_risk_per_trade_pct,
        )

    def validate_order(
        self,
        cost_chf: float,
        stop_loss: Optional[float],
        entry_price: float,
        target_price: Optional[float],
        portfolio_value_chf: float,
        regime: RegimeState,
    ) -> dict:
        """
        Validiert eine Order gegen alle Risikoregeln.
        Gibt Dict mit 'valid', 'errors', 'warnings' zurück.
        """
        errors = []
        warnings = []

        # Positionsgrösse
        position_pct = (cost_chf / portfolio_value_chf) * 100
        if position_pct > self.max_position_pct:
            errors.append(f"Position {position_pct:.1f}% überschreitet Limit {self.max_position_pct}%")
        elif position_pct > regime.max_position_size_pct:
            warnings.append(f"Position {position_pct:.1f}% überschreitet Regime-Limit {regime.max_position_size_pct}%")

        # Stop-Loss Pflicht
        if not stop_loss:
            warnings.append("Kein Stop-Loss gesetzt — dringend empfohlen")
        else:
            risk_per_share = abs(entry_price - stop_loss)
            shares = cost_chf / entry_price
            risk_chf = risk_per_share * shares
            risk_pct = (risk_chf / portfolio_value_chf) * 100
            if risk_pct > 2.0:
                errors.append(f"Risiko {risk_pct:.1f}% überschreitet 2%-Limit")
            elif risk_pct > self.max_risk_per_trade_pct:
                warnings.append(f"Risiko {risk_pct:.1f}% überschreitet 1%-Empfehlung")

        # CRV
        crv = None
        if stop_loss and target_price:
            risk = abs(entry_price - stop_loss)
            reward = abs(target_price - entry_price)
            crv = round(reward / risk, 2) if risk > 0 else None
            if crv and crv < 2.0:
                errors.append(f"CRV {crv:.1f} unter Mindest-CRV 1:2")

        # Regime-Check
        if regime.is_risk_off and cost_chf > portfolio_value_chf * 0.03:
            warnings.append(f"Risk-Off Regime: Position > 3% in {regime.label} erhöht Risiko")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "crv": crv,
            "stamp_tax_chf": round(cost_chf * self.stamp_tax_rate, 2),
        }
