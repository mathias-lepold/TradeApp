"""
Interpretation Layer: FeedbackLoopDetector
Erkennt positive Schleifen (Blasen, Panik) und negative Schleifen
(Stabilisierung / Mean Reversion) aus der Preishistorie.
"""
from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class FeedbackType(str, Enum):
    positive_bubble   = "positive_bubble"   # Selbstverstärkende Aufwärtsspirale
    positive_panic    = "positive_panic"    # Selbstverstärkende Abwärtsspirale
    negative_mean_rev = "negative_mean_rev" # Negative Rückkopplung → Stabilisierung
    neutral           = "neutral"


class FeedbackLoop(BaseModel):
    loop_type:    FeedbackType
    intensity:    float = Field(..., ge=0.0, le=1.0)
    description:  str
    asset_symbol: Optional[str]  = None
    evidence:     List[str]      = Field(default_factory=list)

    model_config = {"use_enum_values": True}


class FeedbackState(BaseModel):
    portfolio_feedback: FeedbackLoop
    asset_feedbacks:    Dict[str, FeedbackLoop] = Field(default_factory=dict)
    systemic_risk:      float = Field(0.0, ge=0.0, le=1.0,
                                      description="Risiko systemischer Verstärkungseffekte 0–1")
    detected_at:        datetime = Field(default_factory=datetime.utcnow)

    model_config = {"use_enum_values": True}


class FeedbackLoopDetector:
    """
    Methodik:
    - Positive Bubble:  Beschleunigendes Aufwärts-Momentum + steigende Volatilität
    - Positive Panic:   Beschleunigendes Abwärts-Momentum
    - Negative Loop:    Häufige Richtungswechsel, abnehmende Amplitude (Mean Reversion)
    """

    def detect(
        self,
        price_histories: Dict[str, List[float]],
        fear_greed:      Optional[int] = None,
    ) -> FeedbackState:

        asset_feedbacks: Dict[str, FeedbackLoop] = {
            sym: self._detect_single(sym, prices)
            for sym, prices in price_histories.items()
            if len(prices) >= 10
        }

        portfolio_loop = self._portfolio_feedback(asset_feedbacks, fear_greed)

        n_positive = sum(
            1 for f in asset_feedbacks.values()
            if f.loop_type in (FeedbackType.positive_bubble, FeedbackType.positive_panic)
        )
        systemic_risk = round(
            min(1.0, n_positive / max(1, len(asset_feedbacks)) * 1.5
                + portfolio_loop.intensity * 0.3),
            3,
        )

        return FeedbackState(
            portfolio_feedback=portfolio_loop,
            asset_feedbacks=asset_feedbacks,
            systemic_risk=systemic_risk,
        )

    # ── Hilfsmethoden ────────────────────────────────────────────────────────

    def _detect_single(self, symbol: str, prices: List[float]) -> FeedbackLoop:
        recent  = prices[-20:] if len(prices) >= 20 else prices
        rets    = [(recent[i] - recent[i - 1]) / recent[i - 1]
                   for i in range(1, len(recent)) if recent[i - 1] > 0]
        if not rets:
            return FeedbackLoop(loop_type=FeedbackType.neutral, intensity=0.0,
                                description="Keine Daten", asset_symbol=symbol)

        mid       = len(rets) // 2
        early_ret = rets[:mid] or rets
        late_ret  = rets[mid:] or rets

        early_mean = sum(early_ret) / len(early_ret)
        late_mean  = sum(late_ret)  / len(late_ret)
        early_vol  = (sum(r ** 2 for r in early_ret) / len(early_ret)) ** 0.5
        late_vol   = (sum(r ** 2 for r in late_ret)  / len(late_ret))  ** 0.5

        evidence: List[str] = []

        # Positive Bubble
        if late_mean > early_mean + 0.005 and late_mean > 0.005 and late_vol >= early_vol * 0.8:
            accel = (late_mean - early_mean) / (abs(early_mean) + 0.001)
            intensity = round(min(1.0, accel * 3), 3)
            if intensity > 0.15:
                evidence.append(f"Momentum {early_mean:+.2%} → {late_mean:+.2%}")
                evidence.append("Steigende Volatilität bestätigt Selbstverstärkung")
                return FeedbackLoop(
                    loop_type=FeedbackType.positive_bubble, intensity=intensity,
                    description=f"Selbstverstärkende Aufwärtsspirale (Beschl. {accel:.0%})",
                    asset_symbol=symbol, evidence=evidence,
                )

        # Positive Panic
        if late_mean < early_mean - 0.005 and late_mean < -0.005:
            accel = (early_mean - late_mean) / (abs(early_mean) + 0.001)
            intensity = round(min(1.0, accel * 3), 3)
            if intensity > 0.15:
                evidence.append(f"Panik-Momentum {early_mean:+.2%} → {late_mean:+.2%}")
                return FeedbackLoop(
                    loop_type=FeedbackType.positive_panic, intensity=intensity,
                    description="Panik-Spirale — Verkaufsdruck verstärkt sich",
                    asset_symbol=symbol, evidence=evidence,
                )

        # Negative Mean Reversion: häufige Richtungswechsel, abnehmende Amplitude
        if len(rets) >= 6:
            sign_changes = sum(1 for i in range(1, len(rets)) if rets[i] * rets[i - 1] < 0)
            if sign_changes > len(rets) * 0.5 and late_vol < early_vol * 0.9:
                intensity = round(min(1.0, sign_changes / len(rets) * 1.5), 3)
                return FeedbackLoop(
                    loop_type=FeedbackType.negative_mean_rev, intensity=intensity,
                    description="Negative Rückkopplung — Mean Reversion aktiv",
                    asset_symbol=symbol,
                    evidence=[f"Richtungswechsel {sign_changes}/{len(rets)}", "Abnehmende Amplitude"],
                )

        return FeedbackLoop(loop_type=FeedbackType.neutral, intensity=0.05,
                            description="Keine dominante Feedback-Schleife",
                            asset_symbol=symbol)

    def _portfolio_feedback(
        self,
        asset_feedbacks: Dict[str, FeedbackLoop],
        fear_greed:      Optional[int],
    ) -> FeedbackLoop:

        if not asset_feedbacks:
            return FeedbackLoop(loop_type=FeedbackType.neutral, intensity=0.0,
                                description="Keine Asset-Daten")

        bubble_i = max((f.intensity for f in asset_feedbacks.values()
                        if f.loop_type == FeedbackType.positive_bubble), default=0.0)
        panic_i  = max((f.intensity for f in asset_feedbacks.values()
                        if f.loop_type == FeedbackType.positive_panic),  default=0.0)
        stab_i   = max((f.intensity for f in asset_feedbacks.values()
                        if f.loop_type == FeedbackType.negative_mean_rev), default=0.0)

        # Fear&Greed verstärkt extreme Loops
        if fear_greed is not None and (fear_greed > 80 or fear_greed < 20):
            bubble_i = min(1.0, bubble_i * 1.4)
            panic_i  = min(1.0, panic_i  * 1.4)

        if bubble_i >= panic_i and bubble_i >= stab_i and bubble_i > 0.1:
            return FeedbackLoop(
                loop_type=FeedbackType.positive_bubble, intensity=round(bubble_i, 3),
                description=f"Portfolio-weite Euphorie-Schleife ({bubble_i:.0%})",
            )
        if panic_i > bubble_i and panic_i > stab_i and panic_i > 0.1:
            return FeedbackLoop(
                loop_type=FeedbackType.positive_panic, intensity=round(panic_i, 3),
                description=f"Portfolio-weite Panik-Schleife ({panic_i:.0%})",
            )
        if stab_i > 0.1:
            return FeedbackLoop(
                loop_type=FeedbackType.negative_mean_rev, intensity=round(stab_i, 3),
                description="Portfolio stabilisiert sich",
            )
        return FeedbackLoop(loop_type=FeedbackType.neutral, intensity=0.05,
                            description="Keine dominante Portfolio-Rückkopplung")
