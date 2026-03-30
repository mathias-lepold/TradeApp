"""
Decision Engine: Engine
Hauptorchestrator — integriert alle Layer zu einer finalen Empfehlung.
"""
from __future__ import annotations

from typing import Optional, List, Dict
from datetime import datetime

from app.domain.signal import Signal, SignalType
from app.domain.regime_state import RegimeState, RegimeType
from app.domain.recommendation import (
    Recommendation, RecommendationAction, RecommendationPriority,
    BiasRisk, PositionSizing
)
from .risk_manager import RiskManager


VERSION = "2.0.0"


class DecisionEngine:
    """
    Finaler Layer — erstellt actionable Recommendations.

    Entscheidungsbaum:
      1. Signal gültig und Score ausreichend?
      2. Regime erlaubt diese Aktion?
      3. Bias-Risiko akzeptabel (< 60)?
      4. Risikoregeln eingehalten (CRV, Positionsgrösse)?
      → Recommendation ausgeben
    """

    MIN_SIGNAL_SCORE = 70
    MAX_BIAS_SCORE_FOR_BUY = 60

    def __init__(
        self,
        risk_manager: Optional[RiskManager] = None,
        portfolio_value_chf: float = 0.0,
        fx_usd_chf: float = 0.889,
    ) -> None:
        self.risk_manager = risk_manager or RiskManager()
        self.portfolio_value_chf = portfolio_value_chf
        self.fx_usd_chf = fx_usd_chf

    def decide(
        self,
        signal: Signal,
        regime: RegimeState,
        bias_risk: Optional[BiasRisk] = None,
    ) -> Recommendation:
        """
        Hauptmethode: erstellt eine Recommendation aus Signal + Regime + BiasRisk.

        Args:
            signal:     Vom Interpretation Layer erzeugtes Signal
            regime:     Aktueller Marktregime-Zustand
            bias_risk:  Bias-Analyse vom Behavioral Layer (optional)

        Returns:
            Recommendation — actionable Handlungsempfehlung
        """
        # Szenario + Hypothesen vorab berechnen (für alle Rückgabepfade)
        _scenarios = self._build_scenario_analysis(signal, regime)
        _uncertainty = self._uncertainty_level(signal, regime)

        # ── 1. Signal-Ablauf prüfen ────────────────────────
        if signal.is_expired:
            _base, _counter = self._hypothesis_texts(signal, regime, RecommendationAction.wait)
            return self._build(
                signal, regime, bias_risk,
                action=RecommendationAction.wait,
                rationale="Signal ist abgelaufen — neue Analyse erforderlich.",
                priority=RecommendationPriority.low,
                key_risks=["Signal-Ablauf: Marktbedingungen können sich verändert haben"],
                scenario_analysis=_scenarios, uncertainty_level=_uncertainty,
                base_hypothesis=_base, counter_hypothesis=_counter,
            )

        # ── 2. Score-Schwelle ─────────────────────────────
        if signal.score.total < self.MIN_SIGNAL_SCORE:
            _base, _counter = self._hypothesis_texts(signal, regime, RecommendationAction.avoid)
            return self._build(
                signal, regime, bias_risk,
                action=RecommendationAction.avoid,
                rationale=f"Score {signal.score.total} unterhalb Schwelle {self.MIN_SIGNAL_SCORE}.",
                priority=RecommendationPriority.low,
                scenario_analysis=_scenarios, uncertainty_level=_uncertainty,
                base_hypothesis=_base, counter_hypothesis=_counter,
            )

        # ── 3. Regime-Kompatibilität ──────────────────────
        action, rationale = self._regime_adjusted_action(signal, regime)

        # ── 4. Bias-Override ──────────────────────────────
        bias_override = False
        if bias_risk and bias_risk.overall_score > self.MAX_BIAS_SCORE_FOR_BUY:
            if action == RecommendationAction.buy:
                action = RecommendationAction.wait
                rationale = (
                    f"Signal ist bullisch (Score {signal.score.total}), "
                    f"aber Bias-Risiko {bias_risk.overall_score}/100 zu hoch. "
                    "Abwarten bis emotionaler Zustand normalisiert."
                )
                bias_override = True

        # ── 5. Positionsgrösse berechnen ──────────────────
        sizing = None
        if action in {RecommendationAction.buy, RecommendationAction.add} and signal.stop_loss:
            fx = self.fx_usd_chf if signal.asset_symbol not in {"NOVN", "NESN", "ZGLD"} else 1.0
            sizing = self.risk_manager.calculate_sizing(
                entry_price=signal.price_at_signal,
                stop_loss=signal.stop_loss,
                portfolio_value_chf=self.portfolio_value_chf,
                regime=regime,
                fx_rate=fx,
            )

        # ── 6. Priority bestimmen ─────────────────────────
        priority = self._determine_priority(signal, regime, bias_override)

        # ── 7. No-Trade-Flag bei instabilem Regime ────────
        no_trade = False
        if getattr(regime, "regime_fragility", 0.3) > 0.7:
            no_trade = True
            if action == RecommendationAction.buy:
                action   = RecommendationAction.wait
                rationale = (
                    f"Regime-Fragility {regime.regime_fragility:.0%} zu hoch — "
                    "No-Trade-Flag gesetzt. Warten bis Regime sich stabilisiert."
                )

        # ── 8. Szenarioanalyse ────────────────────────────
        scenario_analysis = self._build_scenario_analysis(signal, regime)
        uncertainty       = self._uncertainty_level(signal, regime)
        base_hyp, counter_hyp = self._hypothesis_texts(signal, regime, action)

        # ── 9. Risks & Invalidierungsbedingungen ──────────
        key_risks = list(regime.active_risks)
        if bias_risk and bias_risk.warnings:
            key_risks.extend(bias_risk.warnings)

        conditions_to_invalidate = self._invalidation_conditions(signal)

        return self._build(
            signal, regime, bias_risk,
            action=action,
            rationale=rationale,
            priority=priority,
            sizing=sizing,
            key_risks=key_risks,
            conditions_to_invalidate=conditions_to_invalidate,
            no_trade_flag=no_trade,
            scenario_analysis=scenario_analysis,
            uncertainty_level=uncertainty,
            base_hypothesis=base_hyp,
            counter_hypothesis=counter_hyp,
        )

    # ── Hilfsmethoden ─────────────────────────────────────

    def _regime_adjusted_action(
        self, signal: Signal, regime: RegimeState
    ) -> tuple[RecommendationAction, str]:
        """Passt die Aktion basierend auf dem Regime an."""
        base = signal.signal_type

        if base == SignalType.buy:
            if regime.regime_type == RegimeType.crisis:
                return RecommendationAction.avoid, (
                    f"Krisenmodus ({regime.label}): Keine neuen Käufe trotz positivem Signal."
                )
            if regime.regime_type == RegimeType.bear_market:
                return RecommendationAction.wait, (
                    f"Bärenmarkt ({regime.label}): Signal bullisch (Score {signal.score.total}), "
                    "aber Regime erhöht Verlustrisiko — Abwarten."
                )
            if regime.regime_type == RegimeType.volatile and signal.score.total < 80:
                return RecommendationAction.wait, (
                    f"Volatile Märkte ({regime.label}): Erst bei Score > 80 einsteigen."
                )
            return RecommendationAction.buy, (
                f"{signal.asset_name} zeigt starkes Signal (Score {signal.score.total}, "
                f"CRV {signal.crv or '?'}). Regime {regime.label} unterstützt Einstieg."
            )

        if base == SignalType.sell:
            return RecommendationAction.sell, (
                f"Verkaufssignal für {signal.asset_name} (Score {signal.score.total})."
            )

        if base == SignalType.reduce:
            return RecommendationAction.reduce, (
                f"Position in {signal.asset_name} teilweise abbauen."
            )

        return RecommendationAction.hold, (
            f"{signal.asset_name}: Halten — kein klares Signal."
        )

    @staticmethod
    def _determine_priority(
        signal: Signal, regime: RegimeState, bias_override: bool
    ) -> RecommendationPriority:
        if bias_override:
            return RecommendationPriority.low
        if signal.score.total >= 85 and not regime.is_risk_off:
            return RecommendationPriority.high
        if signal.score.total >= 75:
            return RecommendationPriority.normal
        return RecommendationPriority.low

    @staticmethod
    def _invalidation_conditions(signal: Signal) -> List[str]:
        conditions = []
        if signal.stop_loss:
            conditions.append(f"Kurs fällt unter Stop-Loss {signal.stop_loss:.2f}")
        if signal.target_price:
            conditions.append(f"Kursziel {signal.target_price:.2f} erreicht → Review")
        conditions.append("Fundamentale Verschlechterung (Gewinnwarnung, Guidance-Senkung)")
        conditions.append("Regime-Wechsel zu bear_market oder crisis")
        return conditions

    # ── Szenario & Hypothesen Helpers ─────────────────────

    @staticmethod
    def _build_scenario_analysis(signal: Signal, regime: RegimeState) -> Dict[str, float]:
        """Erstellt Wahrscheinlichkeitsverteilung für Bull/Base/Bear Szenarien."""
        score   = signal.score.total
        is_risk = regime.is_risk_off

        bull  = round(max(0.05, min(0.80, (score - 50) / 50 * 0.6 + (0.0 if is_risk else 0.15))), 2)
        bear  = round(max(0.05, min(0.70, (1 - score / 100) * 0.5 + (0.15 if is_risk else 0.0))), 2)
        base  = round(max(0.05, 1.0 - bull - bear), 2)
        # Normalisieren auf 1.0
        total = bull + base + bear
        return {
            "bull": round(bull / total, 3),
            "base": round(base / total, 3),
            "bear": round(bear / total, 3),
        }

    @staticmethod
    def _uncertainty_level(signal: Signal, regime: RegimeState) -> str:
        """Leitet explizite Unsicherheitsstufe ab."""
        fragility = getattr(regime, "regime_fragility", 0.3)
        if signal.score.confidence == "low" or fragility > 0.6 or regime.is_risk_off:
            return "high"
        if signal.score.confidence == "medium" or fragility > 0.4:
            return "medium"
        return "low"

    @staticmethod
    def _hypothesis_texts(
        signal: Signal, regime: RegimeState, action: RecommendationAction
    ) -> tuple[str, str]:
        """Kompakte Texte für Basis- und Gegenhypothese."""
        score = signal.score.total
        if action in (RecommendationAction.buy, RecommendationAction.add):
            base    = (f"{signal.asset_name} (Score {score}) bietet Kaufgelegenheit im "
                       f"{regime.label}. Fundamentale + technische Stärke rechtfertigen Einstieg.")
            counter = (f"Bullisher Case scheitert wenn Regime nach {regime.regime_type} "
                       f"deterioriert oder makroökonomischer Gegenwind zunimmt.")
        elif action in (RecommendationAction.sell, RecommendationAction.reduce):
            base    = (f"Verkaufsdruck bei {signal.asset_name} — Risiko/Ertrag ungünstig "
                       f"im aktuellen {regime.label}.")
            counter = (f"Oversold-Bounce oder positive Überraschung könnte Verkaufssignal entkräften.")
        else:
            base    = (f"Kein klares Signal für {signal.asset_name} — Abwarten sinnvoll "
                       f"(Score {score}, Regime {regime.label}).")
            counter = (f"Konsolidierung könnte in starken Ausbruch übergehen — Auslöser beobachten.")
        return base, counter

    def _build(
        self,
        signal: Signal,
        regime: RegimeState,
        bias_risk: Optional[BiasRisk],
        action: RecommendationAction,
        rationale: str,
        priority: RecommendationPriority = RecommendationPriority.normal,
        sizing: Optional[PositionSizing] = None,
        key_risks: Optional[List[str]] = None,
        conditions_to_invalidate: Optional[List[str]] = None,
        no_trade_flag: bool = False,
        scenario_analysis: Optional[Dict[str, float]] = None,
        uncertainty_level: Optional[str] = None,
        base_hypothesis: Optional[str] = None,
        counter_hypothesis: Optional[str] = None,
    ) -> Recommendation:
        return Recommendation(
            asset_symbol=signal.asset_symbol,
            asset_name=signal.asset_name,
            action=action,
            priority=priority,
            rationale=rationale,
            signal_id=signal.id,
            regime_state_id=regime.id,
            entry_price=signal.price_at_signal,
            stop_loss=signal.stop_loss,
            target_price=signal.target_price,
            sizing=sizing,
            bias_risk=bias_risk,
            regime_summary=regime.label,
            key_risks=key_risks or list(regime.active_risks),
            conditions_to_invalidate=conditions_to_invalidate or [],
            composite_score=signal.score.total,
            decision_engine_version=VERSION,
            no_trade_flag=no_trade_flag,
            scenario_analysis=scenario_analysis,
            uncertainty_level=uncertainty_level,
            base_hypothesis=base_hypothesis,
            counter_hypothesis=counter_hypothesis,
        )
