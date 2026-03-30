"""
Interpretation Layer: ExpectationEngine
Modelliert Markterwartungen vs. tatsächliche Ergebnisse.
Surprise-Score beeinflusst Volatilität und Regime-Anpassungen.
"""
from __future__ import annotations

from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ExpectationModel(BaseModel):
    """Erwartungsmodell für ein einzelnes Asset."""
    asset_symbol:            str
    consensus_expectation:   float = Field(..., description="Erwartete Rendite % (aus Momentum)")
    actual_outcome:          float = Field(..., description="Tatsächliche Rendite % (letzte Perioden)")
    surprise_score:          float = Field(..., ge=-1.0, le=1.0,
                                           description="-1=sehr negativ, +1=sehr positiv")
    expectation_gap:         float = Field(..., ge=0.0, description="Absolute Lücke in %")
    revision_trend:          str   = Field(..., description="up / down / neutral")
    implied_volatility_proxy: float = Field(0.0, ge=0.0,
                                            description="Proxy für Volatilitätserwartung (annualisiert %)")
    confidence:              float = Field(0.5, ge=0.0, le=1.0)
    assessed_at:             datetime = Field(default_factory=datetime.utcnow)


class ExpectationEngine:
    """
    Leitet Markterwartungen aus Preisdynamik + Fundamentalscores ab.
    Keine externen Datenquellen erforderlich.

    Methodik:
    - consensus_expectation: extrapolierter Trend der ersten Preishälfte
    - actual_outcome:        tatsächliche Bewegung der zweiten Hälfte
    - surprise_score:        (actual - consensus) / Normalisierung
    - revision_trend:        Vergleich letzter 5 vs. vorherige 5 Perioden
    """

    def assess(
        self,
        symbol:           str,
        prices:           List[float],
        fundamental_score: int = 70,
        sentiment_score:   int = 50,
    ) -> ExpectationModel:

        if len(prices) < 5:
            return ExpectationModel(
                asset_symbol=symbol,
                consensus_expectation=0.0,
                actual_outcome=0.0,
                surprise_score=0.0,
                expectation_gap=0.0,
                revision_trend="neutral",
                confidence=0.1,
            )

        mid         = len(prices) // 2
        first_half  = prices[:mid]
        second_half = prices[mid:]

        # Consensus: Trend erster Hälfte + fundamentaler Drift
        if len(first_half) >= 2 and first_half[0] > 0:
            trend = (first_half[-1] - first_half[0]) / first_half[0]
            drift = (fundamental_score - 50) / 1000.0
            consensus = trend + drift
        else:
            consensus = 0.0

        # Actual: tatsächliche Bewegung zweite Hälfte
        actual = (second_half[-1] - second_half[0]) / second_half[0] if second_half[0] > 0 else 0.0

        # Surprise Score (begrenzt auf [-1, 1])
        gap      = actual - consensus
        surprise = max(-1.0, min(1.0, gap * 10))

        # Revision Trend: letzten 5 vs. 5 davor
        if len(prices) >= 10:
            r_late  = (prices[-1] - prices[-5])  / prices[-5]  if prices[-5]  > 0 else 0.0
            r_early = (prices[-5] - prices[-10]) / prices[-10] if prices[-10] > 0 else 0.0
            if r_late > r_early + 0.01:
                revision_trend = "up"
            elif r_late < r_early - 0.01:
                revision_trend = "down"
            else:
                revision_trend = "neutral"
        else:
            revision_trend = "neutral"

        # Implied Volatility Proxy: annualisierte Standardabweichung der Returns
        rets = [(prices[i] - prices[i - 1]) / prices[i - 1]
                for i in range(1, len(prices)) if prices[i - 1] > 0]
        if rets:
            mean_r  = sum(rets) / len(rets)
            var     = sum((r - mean_r) ** 2 for r in rets) / len(rets)
            iv_proxy = round((var ** 0.5) * (252 ** 0.5) * 100, 4)
        else:
            iv_proxy = 0.0

        confidence = round(min(0.9, len(prices) / 60), 3)

        return ExpectationModel(
            asset_symbol=symbol,
            consensus_expectation=round(consensus * 100, 4),
            actual_outcome=round(actual * 100, 4),
            surprise_score=round(surprise, 4),
            expectation_gap=round(abs(gap) * 100, 4),
            revision_trend=revision_trend,
            implied_volatility_proxy=iv_proxy,
            confidence=confidence,
        )

    def assess_portfolio(
        self,
        price_histories:  Dict[str, List[float]],
        fund_scores:      Optional[Dict[str, int]] = None,
    ) -> Dict[str, ExpectationModel]:
        fund_scores = fund_scores or {}
        return {
            sym: self.assess(sym, prices, fund_scores.get(sym, 70))
            for sym, prices in price_histories.items()
            if prices
        }
