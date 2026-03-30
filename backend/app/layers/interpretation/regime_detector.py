"""
Interpretation Layer: RegimeDetector
Klassifiziert das aktuelle Marktregime anhand von Makro-Indikatoren und Marktdaten.
"""
from __future__ import annotations

from typing import Optional, Dict, Any

from app.domain.regime_state import (
    RegimeState, RegimeType, SubRegime, MacroSnapshot
)


class RegimeDetector:
    """
    Bestimmt das aktuelle Marktregime aus Makro-Daten.

    Regelbasierte Klassifikation (Prod: ML-Modell als Erweiterung möglich):
      - VIX < 20 + positiver Trend → bull_market / risk_on
      - VIX > 30 → volatile / risk_off
      - VIX > 40 → crisis
      - Invertierte Zinskurve + steigende Arbeitslosigkeit → bear_market
      - Kleine VIX-Range, flacher Markt → sideways
    """

    def detect(self, macro: MacroSnapshot) -> RegimeState:
        """
        Hauptmethode: gibt einen RegimeState zurück basierend auf Makro-Daten.
        """
        regime, sub_regime = self._classify_regime(macro)
        confidence = self._estimate_confidence(macro)
        strength = self._estimate_strength(macro)
        characteristics = self._describe_characteristics(macro, regime)
        active_risks = self._identify_risks(macro)
        sizing = self._position_sizing_rules(regime)

        return RegimeState(
            regime_type=regime,
            sub_regime=sub_regime,
            confidence=confidence,
            strength=strength,
            macro=macro,
            characteristics=characteristics,
            active_risks=active_risks,
            max_position_size_pct=sizing["max_position_pct"],
            recommended_cash_buffer_pct=sizing["cash_buffer_pct"],
            sector_preferences=sizing["sector_preferences"],
        )

    # ── Klassifikationslogik ──────────────────────────────

    @staticmethod
    def _classify_regime(macro: MacroSnapshot) -> tuple[RegimeType, Optional[SubRegime]]:
        vix = macro.vix or 20.0
        yield_curve = macro.yield_curve_10y_2y or 0.0
        fear_greed = macro.fear_greed_index or 50

        # Krisenregime
        if vix > 40:
            return RegimeType.crisis, SubRegime.risk_off

        # Stark volatile
        if vix > 30:
            return RegimeType.volatile, SubRegime.risk_off

        # Bärenmarkt-Indikatoren
        if yield_curve < -0.3 and vix > 22:
            return RegimeType.bear_market, SubRegime.trending_down

        # Bärenmarkt mit Erholung
        if yield_curve < -0.3 and fear_greed > 50:
            return RegimeType.recovery, SubRegime.risk_on

        # Seitwärtsbewegung
        if vix < 18 and 40 <= fear_greed <= 60:
            return RegimeType.sideways, SubRegime.ranging

        # Bullmarkt
        if vix < 20 and fear_greed > 55:
            sub = SubRegime.trending_up if fear_greed > 70 else SubRegime.risk_on
            return RegimeType.bull_market, sub

        # Bullmarkt mit Accumulation
        if vix < 20 and fear_greed < 40:
            return RegimeType.bull_market, SubRegime.accumulation

        # Default
        return RegimeType.sideways, SubRegime.ranging

    @staticmethod
    def _estimate_confidence(macro: MacroSnapshot) -> float:
        """Höhere Konfidenz wenn mehrere Indikatoren in dieselbe Richtung zeigen."""
        signals_available = sum([
            macro.vix is not None,
            macro.yield_curve_10y_2y is not None,
            macro.fear_greed_index is not None,
            macro.fed_rate is not None,
            macro.cpi_us is not None,
        ])
        return min(0.4 + signals_available * 0.12, 0.95)

    @staticmethod
    def _estimate_strength(macro: MacroSnapshot) -> float:
        vix = macro.vix or 20.0
        fear_greed = macro.fear_greed_index or 50
        extremeness = abs(fear_greed - 50) / 50  # 0.0 = neutral, 1.0 = extrem
        vix_factor = min(vix / 40, 1.0)
        return round(min((extremeness * 0.6 + vix_factor * 0.4), 1.0), 2)

    @staticmethod
    def _describe_characteristics(macro: MacroSnapshot, regime: RegimeType) -> list[str]:
        chars = []
        if macro.vix:
            chars.append(f"VIX {macro.vix:.1f}")
        if macro.yield_curve_10y_2y is not None:
            label = "invertiert" if macro.yield_curve_10y_2y < 0 else "normal"
            chars.append(f"Zinskurve {label} ({macro.yield_curve_10y_2y:+.2f}%)")
        if macro.fear_greed_index is not None:
            level = "Extreme Fear" if macro.fear_greed_index < 25 else \
                    "Fear" if macro.fear_greed_index < 45 else \
                    "Neutral" if macro.fear_greed_index < 55 else \
                    "Greed" if macro.fear_greed_index < 75 else "Extreme Greed"
            chars.append(f"Fear & Greed: {level} ({macro.fear_greed_index})")
        if macro.fed_rate:
            chars.append(f"Fed Funds Rate: {macro.fed_rate:.2f}%")
        return chars

    @staticmethod
    def _identify_risks(macro: MacroSnapshot) -> list[str]:
        risks = []
        if macro.vix and macro.vix > 25:
            risks.append("Erhöhte Marktvolatilität")
        if macro.yield_curve_10y_2y is not None and macro.yield_curve_10y_2y < -0.2:
            risks.append("Invertierte Zinskurve — Rezessionsrisiko")
        if macro.fed_rate and macro.fed_rate > 4.5:
            risks.append("Restriktives Zinsumfeld")
        if macro.fear_greed_index is not None and macro.fear_greed_index < 25:
            risks.append("Extreme Marktangst — Überverkauft möglich")
        if macro.fear_greed_index is not None and macro.fear_greed_index > 80:
            risks.append("Extreme Gier — Korrekturrisiko erhöht")
        return risks

    @staticmethod
    def _position_sizing_rules(regime: RegimeType) -> Dict[str, Any]:
        """Gibt regime-spezifische Positionsgrössen-Regeln zurück."""
        rules = {
            RegimeType.bull_market: {
                "max_position_pct": 8.0,
                "cash_buffer_pct": 10.0,
                "sector_preferences": {"Technology": 1.2, "Healthcare": 1.0, "Utilities": 0.8},
            },
            RegimeType.sideways: {
                "max_position_pct": 5.0,
                "cash_buffer_pct": 15.0,
                "sector_preferences": {"Consumer Staples": 1.2, "Healthcare": 1.1},
            },
            RegimeType.volatile: {
                "max_position_pct": 3.0,
                "cash_buffer_pct": 25.0,
                "sector_preferences": {"Gold": 1.5, "Utilities": 1.3, "Consumer Staples": 1.2},
            },
            RegimeType.bear_market: {
                "max_position_pct": 2.0,
                "cash_buffer_pct": 40.0,
                "sector_preferences": {"Gold": 2.0, "Utilities": 1.5, "Healthcare": 1.2},
            },
            RegimeType.crisis: {
                "max_position_pct": 1.0,
                "cash_buffer_pct": 60.0,
                "sector_preferences": {"Gold": 2.5},
            },
            RegimeType.recovery: {
                "max_position_pct": 5.0,
                "cash_buffer_pct": 20.0,
                "sector_preferences": {"Technology": 1.1, "Financials": 1.1},
            },
        }
        return rules.get(regime, rules[RegimeType.sideways])
