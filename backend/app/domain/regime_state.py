"""
Domain Model: RegimeState
Beschreibt den aktuellen Marktregime — Ausgabe des Interpretation Layers.
Bestimmt, welche Strategien und Positionsgrößen der Decision Engine zulässt.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional, List, Dict
from datetime import datetime
from pydantic import BaseModel, Field, computed_field
import uuid


class RegimeType(str, Enum):
    """Primäres Marktregime."""
    bull_market = "bull_market"          # Trending aufwärts, geringer Stress
    bear_market = "bear_market"          # Trending abwärts, erhöhter Stress
    sideways = "sideways"                # Seitwärtsbewegung, Range-bound
    volatile = "volatile"                # Hohe Volatilität ohne klaren Trend
    crisis = "crisis"                    # Systemische Krise (2008, COVID)
    recovery = "recovery"                # Erholung nach Krise


class SubRegime(str, Enum):
    """Sekundäre Klassifikation für feinere Steuerung."""
    risk_on = "risk_on"                  # Risikobereitschaft hoch
    risk_off = "risk_off"                # Risikoaversion dominiert
    trending_up = "trending_up"          # Klarer Aufwärtstrend
    trending_down = "trending_down"      # Klarer Abwärtstrend
    ranging = "ranging"                  # Definierte Range
    breakout = "breakout"                # Ausbruch aus Range
    distribution = "distribution"        # Institutioneller Verkauf
    accumulation = "accumulation"        # Institutioneller Kauf


class MacroSnapshot(BaseModel):
    """Makro-Kennzahlen zum Zeitpunkt der Regime-Erkennung."""
    fed_rate: Optional[float] = None
    snb_rate: Optional[float] = None
    vix: Optional[float] = Field(None, ge=0, description="CBOE VIX Volatilitätsindex")
    yield_curve_10y_2y: Optional[float] = Field(None, description="Positive = normal, Negative = invertiert")
    usd_chf: Optional[float] = None
    eur_chf: Optional[float] = None
    gold_xau_usd: Optional[float] = None
    oil_wti: Optional[float] = None
    fear_greed_index: Optional[int] = Field(None, ge=0, le=100)
    cpi_us: Optional[float] = None
    unemployment_us: Optional[float] = None


class RegimeState(BaseModel):
    """
    Aktueller Zustand des Marktregimes.
    Wird vom Interpretation Layer erkannt und vom Decision Engine konsumiert,
    um Strategien, Positionsgrößen und Risikotoleranzen anzupassen.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    regime_type: RegimeType
    sub_regime: Optional[SubRegime] = None

    # Konfidenz & Stärke
    confidence: float = Field(..., ge=0.0, le=1.0, description="0.0–1.0 Konfidenz der Regime-Erkennung")
    strength: float = Field(..., ge=0.0, le=1.0, description="0.0–1.0 Stärke/Klarheit des Regimes")

    # Indikatoren
    macro: MacroSnapshot = Field(default_factory=MacroSnapshot)
    characteristics: List[str] = Field(
        default_factory=list,
        description="Beschreibende Merkmale (z.B. 'Invertierte Zinsstruktur', 'VIX > 30')"
    )
    active_risks: List[str] = Field(
        default_factory=list,
        description="Aktive Marktrisiken (z.B. 'Rezessionsrisiko', 'Fed Pivot erwartet')"
    )

    # Handlungsimplikationen für den Decision Engine
    max_position_size_pct: float = Field(
        5.0, ge=0.5, le=15.0,
        description="Maximale Positionsgrösse in % des Portfolios in diesem Regime"
    )
    recommended_cash_buffer_pct: float = Field(
        10.0, ge=0.0, le=60.0,
        description="Empfohlener Cash-Anteil in diesem Regime"
    )
    sector_preferences: Dict[str, float] = Field(
        default_factory=dict,
        description="Sektorgewichtungs-Empfehlungen: {sector: weight_multiplier}"
    )

    # ── Erweiterte Felder (Zyklus- und Stabilitätsmodell) ────────────────────
    regime_fragility:  float = Field(
        0.3, ge=0.0, le=1.0,
        description="Instabilität des Regimes — wie leicht wechselt es? 0=stabil, 1=fragil"
    )
    dominant_layer: Optional[str] = Field(
        None, description="Welcher Layer das Regime gerade dominiert: 'fundamental' | 'liquidity' | 'behavioral'"
    )
    transition_speed: float = Field(
        0.3, ge=0.0, le=1.0,
        description="Geschwindigkeit potenzieller Regime-Transitionen 0=langsam, 1=schnell"
    )

    # Zeitstempel
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = Field(None, description="Wann das Regime begann (retrospektiv)")
    previous_regime_id: Optional[str] = Field(None, description="ID des vorherigen Regimes")

    @computed_field
    @property
    def is_risk_off(self) -> bool:
        """True wenn Risikoreduktion empfohlen wird."""
        risk_off_regimes = {RegimeType.bear_market, RegimeType.crisis, RegimeType.volatile}
        return self.regime_type in risk_off_regimes or self.sub_regime == SubRegime.risk_off

    @computed_field
    @property
    def vix_category(self) -> str:
        """Kategorisierung des VIX-Niveaus."""
        vix = self.macro.vix
        if vix is None:
            return "unknown"
        if vix < 15:
            return "low"
        if vix < 25:
            return "normal"
        if vix < 35:
            return "elevated"
        return "extreme"

    @computed_field
    @property
    def label(self) -> str:
        """Menschenlesbares Label für UI."""
        parts = [self.regime_type.replace("_", " ").title()]
        if self.sub_regime:
            parts.append(f"({self.sub_regime.replace('_', ' ').title()})")
        return " ".join(parts)

    model_config = {"use_enum_values": True}

    @classmethod
    def default_bull(cls) -> "RegimeState":
        """Standardregime für Initialisierung."""
        return cls(
            regime_type=RegimeType.bull_market,
            sub_regime=SubRegime.risk_on,
            confidence=0.6,
            strength=0.5,
            characteristics=["Initialer Standardzustand — noch keine Live-Daten"],
            max_position_size_pct=5.0,
            recommended_cash_buffer_pct=10.0,
        )
