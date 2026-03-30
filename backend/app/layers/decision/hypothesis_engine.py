"""
Decision Engine: HypothesisEngine
Generiert Basishypothese + Gegenhypothese + Trigger für Phasenwechsel.
Erzwingt explizite Auseinandersetzung mit Gegenthesen (Falsifizierbarkeit).
"""
from __future__ import annotations

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from app.domain.signal import Signal, SignalType
from app.domain.regime_state import RegimeState, RegimeType


class HypothesisScenario(BaseModel):
    """Einzelnes Hypothesen-Szenario mit Konfidenz und Triggern."""
    title:             str
    description:       str
    confidence:        float = Field(..., ge=0.0, le=1.0)
    triggers:          List[str] = Field(default_factory=list,
                                         description="Bedingungen die dieses Szenario aktivieren")
    invalidators:      List[str] = Field(default_factory=list,
                                         description="Was das Szenario zunichte macht")
    price_target_pct:  Optional[float] = Field(None,
                                                description="Preisziel in % (pos=up, neg=down)")
    time_horizon_days: Optional[int]   = None


class HypothesisSet(BaseModel):
    """Vollständiges Hypothesen-Set für ein Asset."""
    asset_symbol:              str
    base_hypothesis:           HypothesisScenario
    counter_hypothesis:        HypothesisScenario
    alternative_scenarios:     List[HypothesisScenario] = Field(default_factory=list)
    overall_conviction:        float = Field(..., ge=0.0, le=1.0,
                                             description="Überzeugung in Basishypothese")
    phase_transition_triggers: List[str] = Field(default_factory=list)
    generated_at:              datetime  = Field(default_factory=datetime.utcnow)


class HypothesisEngine:
    """
    Erzeugt strukturierte Hypothesen aus Signal + Regime + Preisdynamik.
    Keine externen APIs — basiert auf lokalen Daten.
    """

    def generate(
        self,
        signal: Signal,
        regime: RegimeState,
        prices: Optional[List[float]] = None,
    ) -> HypothesisSet:

        prices = prices or []

        # Momentum der letzten 10 Perioden
        if len(prices) >= 10 and prices[-10] > 0:
            momentum = (prices[-1] - prices[-10]) / prices[-10]
        else:
            momentum = 0.0

        is_bullish        = signal.signal_type in (SignalType.buy,  SignalType.add)
        is_bearish        = signal.signal_type in (SignalType.sell, SignalType.reduce)
        regime_supportive = regime.regime_type in (RegimeType.bull_market, RegimeType.recovery)

        crv_str = f"CRV {signal.crv:.1f}" if signal.crv else "kein CRV berechnet"
        score   = signal.score.total

        if is_bullish:
            base, counter = self._bullish_pair(signal, regime, momentum, crv_str, score)
        elif is_bearish:
            base, counter = self._bearish_pair(signal, regime, momentum, crv_str, score)
        else:
            base, counter = self._neutral_pair(signal, regime, score)

        # Conviction: Score + Regime-Alignment
        conviction = score / 100 * 0.6
        if regime_supportive and is_bullish:
            conviction = min(1.0, conviction + 0.25)
        if regime.is_risk_off and is_bullish:
            conviction = max(0.1, conviction - 0.30)
        conviction = round(conviction, 3)

        # Wait-Szenario immer als Alternative
        wait = HypothesisScenario(
            title="Abwarten",
            description=(
                "Regime unklar oder Signal noch nicht reif — kein Einstieg. "
                "Regime-Fragility und Phasenwechsel beobachten."
            ),
            confidence=0.2 if regime_supportive else 0.4,
            triggers=["VIX > 30", "Fear&Greed < 25 oder > 75"],
            invalidators=["Regime bestätigt sich", "Score steigt über 85"],
            time_horizon_days=10,
        )

        triggers = self._phase_triggers(signal, regime)

        return HypothesisSet(
            asset_symbol=signal.asset_symbol,
            base_hypothesis=base,
            counter_hypothesis=counter,
            alternative_scenarios=[wait],
            overall_conviction=conviction,
            phase_transition_triggers=triggers,
        )

    # ── Szenarien ─────────────────────────────────────────────────────────────

    def _bullish_pair(
        self, signal: Signal, regime: RegimeState,
        momentum: float, crv_str: str, score: int,
    ) -> tuple[HypothesisScenario, HypothesisScenario]:

        sl_str = f"Stop-Loss {signal.stop_loss:.2f}" if signal.stop_loss else "kein Stop-Loss"
        base = HypothesisScenario(
            title=f"Bullisher Einstieg {signal.asset_symbol}",
            description=(
                f"{signal.asset_name} zeigt fundamentale Stärke (Score {score}/100). "
                f"Momentum {momentum:+.1%}, {crv_str}. "
                f"Regime {regime.label} unterstützt weiteres Aufwärtspotential."
            ),
            confidence=round(min(0.9, score / 100 * 0.8 + 0.1), 3),
            triggers=[
                f"Score {score} > 75 bestätigt",
                f"Momentum {momentum:+.1%} positiv",
                f"Regime {regime.label} stabil",
            ],
            invalidators=[
                sl_str + " unterschritten",
                "Regime wechselt zu bear_market oder crisis",
                "Fundamentale Gewinnwarnung",
            ],
            price_target_pct=(
                (signal.target_price / signal.price_at_signal - 1) * 100
                if signal.target_price else None
            ),
            time_horizon_days=14,
        )
        counter = HypothesisScenario(
            title=f"Bärischer Gegencase {signal.asset_symbol}",
            description=(
                "Bullisher Case scheitert durch Makro-Gegenwind, Regime-Instabilität "
                "oder psychologische Übertreibung nach bisheriger Rally."
            ),
            confidence=round(max(0.1, 1.0 - score / 100 * 0.7), 3),
            triggers=["VIX steigt > 28", "Fear&Greed < 30", "Momentum dreht negativ"],
            invalidators=["Score bleibt > 75", "Regime stabil"],
            price_target_pct=-10.0,
            time_horizon_days=14,
        )
        return base, counter

    def _bearish_pair(
        self, signal: Signal, regime: RegimeState,
        momentum: float, crv_str: str, score: int,
    ) -> tuple[HypothesisScenario, HypothesisScenario]:

        base = HypothesisScenario(
            title=f"Bärischer Case {signal.asset_symbol}",
            description=(
                f"Verkaufssignal für {signal.asset_name} (Score {score}/100). "
                f"Momentum {momentum:+.1%}. Regime {regime.label}."
            ),
            confidence=round(min(0.85, score / 100 * 0.7 + 0.15), 3),
            triggers=["Momentum negativ", "Regime risk-off"],
            invalidators=["Starker Turnaround", "Positive Earnings-Überraschung"],
            price_target_pct=-8.0,
            time_horizon_days=10,
        )
        counter = HypothesisScenario(
            title=f"Bullisher Rebound {signal.asset_symbol}",
            description="Oversold-Bounce oder Sentiment-Reversal entkräftet bearishen Case.",
            confidence=0.3,
            triggers=["Fear&Greed < 20 (Contrarian-Signal)", "VIX-Spike reverses"],
            invalidators=["Momentum bleibt negativ", "Earnings-Enttäuschung"],
            price_target_pct=5.0,
            time_horizon_days=7,
        )
        return base, counter

    def _neutral_pair(
        self, signal: Signal, regime: RegimeState, score: int,
    ) -> tuple[HypothesisScenario, HypothesisScenario]:

        base = HypothesisScenario(
            title=f"Range-bound / Hold {signal.asset_symbol}",
            description=f"{signal.asset_name} in Konsolidierungsphase (Score {score}/100). Abwarten.",
            confidence=0.5,
            triggers=["Kein klares Signal", "Regime seitwärts"],
            invalidators=["Breakout über Widerstand", "Breakdown unter Support"],
            time_horizon_days=7,
        )
        counter = HypothesisScenario(
            title=f"Breakout-Szenario {signal.asset_symbol}",
            description="Konsolidierung kann in Ausbruch enden — Richtung noch unklar.",
            confidence=0.3,
            triggers=["Volumen-Spike", "Macro-Katalysator"],
            invalidators=["Seitwärtsbewegung hält an"],
        )
        return base, counter

    @staticmethod
    def _phase_triggers(signal: Signal, regime: RegimeState) -> List[str]:
        triggers = [
            "VIX > 35 → External Shock Phase",
            "Fear&Greed < 15 → Psychological Overshoot (Panik)",
            "Fear&Greed > 85 → Psychological Overshoot (Euphorie)",
        ]
        if regime.macro.vix and regime.macro.vix > 25:
            triggers.append(f"VIX aktuell {regime.macro.vix:.0f} — nahe Schock-Trigger")
        if signal.stop_loss:
            triggers.append(f"Kurs unter {signal.stop_loss:.2f} → Neubewertung")
        return triggers
