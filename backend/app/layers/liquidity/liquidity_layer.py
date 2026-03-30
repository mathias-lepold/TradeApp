"""
Liquidity Layer: LiquidityLayer
Bewertet Liquiditätsbedingungen und Zwangsverkaufsrisiko aus MockFeed-Daten.
"""
from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class FundingCondition(str, Enum):
    ample      = "ample"       # Reichlich Liquidität
    normal     = "normal"      # Normale Bedingungen
    tightening = "tightening"  # Verschärfung in Gang
    tight      = "tight"       # Eng
    stressed   = "stressed"    # Unter Stress


class LiquidityState(BaseModel):
    liquidity_stress:    float = Field(..., ge=0.0, le=1.0,
                                        description="0=kein Stress, 1=maximaler Stress")
    funding_conditions:  FundingCondition
    forced_selling_risk: float = Field(..., ge=0.0, le=1.0,
                                        description="Risiko von Zwangsverkäufen 0–1")
    bid_ask_spread_proxy: float = Field(0.0, ge=0.0, description="Geschätzter Spread (Proxy %)")
    market_depth_score:  float = Field(1.0, ge=0.0, le=1.0,
                                        description="1=tiefe Märkte, 0=sehr dünn")
    vix_proxy:           float = Field(0.0, ge=0.0, description="Berechneter VIX-Proxy")
    signals:             List[str] = Field(default_factory=list)
    assessed_at:         datetime  = Field(default_factory=datetime.utcnow)

    model_config = {"use_enum_values": True}


class LiquidityLayer:
    """
    Berechnet Liquiditätskennzahlen aus Preishistorie + Makroinputs.
    Keine externen APIs erforderlich — alles aus MockFeed-Daten.

    VIX-Proxy: annualisierte Volatilität der Preishistorien × 100
    """

    def assess(
        self,
        price_histories: Dict[str, List[float]],
        vix:             Optional[float] = None,
        fear_greed:      Optional[int]   = None,
        fed_rate:        Optional[float] = None,
    ) -> LiquidityState:

        signals:    List[str] = []
        vix_proxy   = self._compute_vix_proxy(price_histories)
        eff_vix     = vix if vix is not None else vix_proxy

        # Liquidity Stress aus VIX-Niveau
        if eff_vix < 15:
            stress = 0.05
        elif eff_vix < 20:
            stress = 0.10 + (eff_vix - 15) / 50
        elif eff_vix < 30:
            stress = 0.20 + (eff_vix - 20) / 40
        elif eff_vix < 40:
            stress = 0.45 + (eff_vix - 30) / 40
        else:
            stress = 0.70 + min(0.30, (eff_vix - 40) / 80)

        # Fear & Greed Adjustierung
        if fear_greed is not None:
            if fear_greed < 20:
                stress = min(1.0, stress + 0.15)
                signals.append(f"Extreme Angst (F&G {fear_greed}) erhöht Liquiditätsstress")
            elif fear_greed > 80:
                stress = max(0.0, stress - 0.05)

        # Zinsniveau
        if fed_rate is not None and fed_rate > 5.0:
            stress = min(1.0, stress + 0.10)
            signals.append(f"Hohe Fed Rate ({fed_rate}%) verengt Funding-Bedingungen")

        stress = round(stress, 3)

        # Funding Conditions
        if stress < 0.15:
            funding = FundingCondition.ample
        elif stress < 0.30:
            funding = FundingCondition.normal
        elif stress < 0.45:
            funding = FundingCondition.tightening
        elif stress < 0.65:
            funding = FundingCondition.tight
        else:
            funding = FundingCondition.stressed

        # Forced Selling Risk
        fg_factor     = 1.0 + (1.0 - (fear_greed or 50) / 100)
        forced_risk   = round(min(1.0, stress * 1.3 * fg_factor), 3)
        if forced_risk > 0.5:
            signals.append(f"Zwangsverkaufsrisiko erhöht ({forced_risk:.0%})")

        # Bid-Ask Spread Proxy aus Volatilität
        avg_vol = (
            sum(abs((p[-1] - p[-2]) / p[-2])
                for p in price_histories.values()
                if len(p) >= 2 and p[-2] > 0)
            / max(1, len(price_histories))
        )
        spread_proxy  = round(avg_vol * 200, 4)

        # Market Depth Score (invers zu Stress)
        depth = round(max(0.1, 1.0 - stress * 0.9), 3)

        if eff_vix > 30:
            signals.append(f"VIX {eff_vix:.1f} — Markttiefe reduziert")

        return LiquidityState(
            liquidity_stress=stress,
            funding_conditions=funding,
            forced_selling_risk=forced_risk,
            bid_ask_spread_proxy=spread_proxy,
            market_depth_score=depth,
            vix_proxy=round(vix_proxy, 2),
            signals=signals,
        )

    def _compute_vix_proxy(self, price_histories: Dict[str, List[float]]) -> float:
        """Annualisierte Volatilität als VIX-Proxy (VIX-ähnliche Skala)."""
        vols: List[float] = []
        for prices in price_histories.values():
            if len(prices) < 5:
                continue
            recent = prices[-20:] if len(prices) >= 20 else prices
            rets   = [(recent[i] - recent[i - 1]) / recent[i - 1]
                      for i in range(1, len(recent)) if recent[i - 1] > 0]
            if len(rets) < 2:
                continue
            mean_r   = sum(rets) / len(rets)
            variance = sum((r - mean_r) ** 2 for r in rets) / len(rets)
            vols.append((variance ** 0.5) * (252 ** 0.5) * 100)
        return round(sum(vols) / len(vols), 2) if vols else 20.0
