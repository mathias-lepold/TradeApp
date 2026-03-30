"""
Interpretation Layer: MarketCycleEngine
Erkennt die aktuelle Phase des Marktzyklus.
Phasen können überlappen — jede Phase hat eine Intensität 0–1.
6 Phasen: Fundamental, ExternalShock, FirstReaction,
          PsychologicalOvershoot, Stabilization, ReturnToFundamentals
"""
from __future__ import annotations

from enum import Enum
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class CyclePhase(str, Enum):
    fundamental             = "fundamental"
    external_shock          = "external_shock"
    first_reaction          = "first_reaction"
    psychological_overshoot = "psychological_overshoot"
    stabilization           = "stabilization"
    return_to_fundamentals  = "return_to_fundamentals"


class PhaseIntensity(BaseModel):
    phase:       CyclePhase
    intensity:   float = Field(..., ge=0.0, le=1.0)
    description: str   = ""


class MarketCycleState(BaseModel):
    active_phases:       List[PhaseIntensity] = Field(default_factory=list)
    dominant_phase:      CyclePhase           = CyclePhase.fundamental
    transition_speed:    float = Field(0.3, ge=0.0, le=1.0,
                                       description="0=langsam, 1=schnell")
    overall_instability: float = Field(0.0, ge=0.0, le=1.0)
    signals:             List[str] = Field(default_factory=list)
    detected_at:         datetime  = Field(default_factory=datetime.utcnow)

    model_config = {"use_enum_values": True}


class MarketCycleEngine:
    """
    Bestimmt aus Preishistorie + Makrodaten welche Zyklusphasen
    gerade aktiv sind und wie stark (Intensität 0–1).
    Mehrere Phasen können gleichzeitig aktiv sein.
    """

    def detect(
        self,
        prices:       List[float],
        vix:          Optional[float] = None,
        fear_greed:   Optional[int]   = None,
        regime_type:  Optional[str]   = None,
    ) -> MarketCycleState:

        if len(prices) < 5:
            return MarketCycleState(
                active_phases=[PhaseIntensity(
                    phase=CyclePhase.fundamental, intensity=0.5,
                    description="Standardwert — zu wenig Preisdaten",
                )],
                dominant_phase=CyclePhase.fundamental,
                signals=["Zu wenig Preisdaten für Zyklusanalyse"],
            )

        phases:  List[PhaseIntensity] = []
        signals: List[str]            = []

        recent  = prices[-20:] if len(prices) >= 20 else prices
        returns = [abs((recent[i] - recent[i - 1]) / recent[i - 1])
                   for i in range(1, len(recent))]
        avg_vol = sum(returns) / len(returns) if returns else 0.0

        # Momentum: neue 10 vs alte 10
        if len(prices) >= 20:
            old_avg  = sum(prices[-20:-10]) / 10
            new_avg  = sum(prices[-10:])    / 10
            momentum = (new_avg - old_avg) / old_avg if old_avg > 0 else 0.0
        else:
            momentum = (prices[-1] - prices[0]) / prices[0] if prices[0] > 0 else 0.0

        # Drawdown im letzten Fenster
        window   = prices[-30:] if len(prices) >= 30 else prices
        peak     = max(window)
        trough   = min(window)
        drawdown = (peak - trough) / peak if peak > 0 else 0.0

        # ── Fundamental ──────────────────────────────────
        fund_i = max(0.0, 1.0 - avg_vol * 20 - drawdown * 2)
        if vix and vix < 20:
            fund_i = min(1.0, fund_i + 0.2)
        fund_i = round(min(1.0, max(0.0, fund_i)), 3)
        phases.append(PhaseIntensity(
            phase=CyclePhase.fundamental, intensity=fund_i,
            description="Fundamentale Bewertung dominiert Preisfindung",
        ))

        # ── External Shock ───────────────────────────────
        shock_i = 0.0
        if vix and vix > 35:
            shock_i = min(1.0, (vix - 35) / 30)
            signals.append(f"VIX {vix:.0f} — externer Schock möglich")
        if regime_type in ("crisis", "volatile") and avg_vol > 0.02:
            shock_i = max(shock_i, 0.6)
        if drawdown > 0.15:
            shock_i = max(shock_i, min(1.0, drawdown * 3))
            signals.append(f"Drawdown {drawdown:.1%} — Schocksignal")
        shock_i = round(shock_i, 3)
        if shock_i > 0.1:
            phases.append(PhaseIntensity(
                phase=CyclePhase.external_shock, intensity=shock_i,
                description="Externer Schock beeinflusst Marktstruktur",
            ))

        # ── First Reaction ───────────────────────────────
        react_i = 0.0
        if avg_vol > 0.015 and abs(momentum) > 0.05:
            react_i = min(1.0, avg_vol * 30 + abs(momentum) * 3)
            signals.append("Erstreaktion: hohe Volatilität + gerichtetes Momentum")
        react_i = round(react_i, 3)
        if react_i > 0.1:
            phases.append(PhaseIntensity(
                phase=CyclePhase.first_reaction, intensity=react_i,
                description="Märkte reagieren auf neues Informationsset",
            ))

        # ── Psychological Overshoot ──────────────────────
        over_i = 0.0
        if fear_greed is not None:
            if fear_greed > 80:
                over_i = (fear_greed - 80) / 20
                signals.append(f"Fear&Greed {fear_greed} — Euphorie-Übertreibung")
            elif fear_greed < 20:
                over_i = (20 - fear_greed) / 20
                signals.append(f"Fear&Greed {fear_greed} — Panik-Übertreibung")
        if drawdown > 0.20:
            over_i = max(over_i, min(1.0, (drawdown - 0.10) * 5))
        over_i = round(over_i, 3)
        if over_i > 0.1:
            phases.append(PhaseIntensity(
                phase=CyclePhase.psychological_overshoot, intensity=over_i,
                description="Psychologische Übertreibung (Euphorie oder Panik)",
            ))

        # ── Stabilization ────────────────────────────────
        stab_i = 0.0
        if len(prices) >= 20:
            e_ret = [abs((prices[i] - prices[i - 1]) / prices[i - 1])
                     for i in range(max(1, len(prices) - 20), max(2, len(prices) - 10))]
            l_ret = [abs((prices[i] - prices[i - 1]) / prices[i - 1])
                     for i in range(max(1, len(prices) - 10), len(prices))]
            if e_ret and l_ret:
                avg_e = sum(e_ret) / len(e_ret)
                avg_l = sum(l_ret) / len(l_ret)
                if avg_e > 0 and avg_l < avg_e * 0.7:
                    stab_i = min(1.0, 1 - avg_l / avg_e)
                    signals.append("Volatilität nimmt ab — Stabilisierung erkannt")
        stab_i = round(stab_i, 3)
        if stab_i > 0.1:
            phases.append(PhaseIntensity(
                phase=CyclePhase.stabilization, intensity=stab_i,
                description="Markt stabilisiert sich nach Volatilitätsphase",
            ))

        # ── Return to Fundamentals ───────────────────────
        rtf_i = 0.0
        if fund_i > 0.5 and shock_i < 0.2 and over_i < 0.2:
            rtf_i = round(fund_i * 0.8, 3)
            signals.append("Rückkehr zu fundamentaler Bewertung")
        elif stab_i > 0.4 and abs(momentum) < 0.02:
            rtf_i = round(stab_i * 0.6, 3)
        if rtf_i > 0.1:
            phases.append(PhaseIntensity(
                phase=CyclePhase.return_to_fundamentals, intensity=rtf_i,
                description="Markt kehrt zur fairen Fundamentalbewertung zurück",
            ))

        dominant = max(phases, key=lambda p: p.intensity)
        transition_speed = round(min(1.0, avg_vol * 40 + shock_i * 0.5), 3)
        instability      = round(min(1.0, shock_i * 0.4 + over_i * 0.3 + avg_vol * 20), 3)

        return MarketCycleState(
            active_phases=phases,
            dominant_phase=dominant.phase,
            transition_speed=transition_speed,
            overall_instability=instability,
            signals=signals,
        )
