"""
Domain Model: Signal
Ausgabe des Interpretation Layers — ein konkretes Handelssignal mit vollständiger Analyse.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel, Field, model_validator, computed_field
import uuid


class SignalType(str, Enum):
    buy = "buy"
    sell = "sell"
    hold = "hold"
    avoid = "avoid"
    reduce = "reduce"      # Position teilweise abbauen
    add = "add"            # Position aufstocken


class SignalStrength(str, Enum):
    strong = "strong"
    moderate = "moderate"
    weak = "weak"


class SignalConfidence(str, Enum):
    high = "high"       # Score > 80, mehrere Indikatoren bestätigen
    medium = "medium"   # Score 60–80
    low = "low"         # Score < 60, widersprüchliche Signale


class ScoreBreakdown(BaseModel):
    """
    Multidimensionaler Score — Ausgabe des Interpretation Layers.
    Jede Dimension bewertet einen anderen Aspekt des Investments.
    """
    fundamental: int = Field(..., ge=0, le=100, description="KGV, Wachstum, Margen, Bilanz")
    technical: int = Field(..., ge=0, le=100, description="Trend, RSI, MACD, Unterstützung/Widerstand")
    management: int = Field(..., ge=0, le=100, description="CEO-Qualität, Insider-Käufe, Governance")
    sentiment: int = Field(..., ge=0, le=100, description="Nachrichten-Sentiment, Social, Analysten")
    geopolitical: int = Field(..., ge=0, le=100, description="Länder-/Geopolitik-Risiko (invertiert)")
    macro: int = Field(..., ge=0, le=100, description="Zinsumfeld, FX, Konjunktur")

    # Gewichtete Gesamtnote
    total: int = Field(..., ge=0, le=100)
    verdict: SignalType
    confidence: SignalConfidence

    @model_validator(mode="after")
    def validate_total(self) -> "ScoreBreakdown":
        weighted = (
            self.fundamental * 0.25
            + self.technical * 0.20
            + self.management * 0.15
            + self.sentiment * 0.15
            + self.geopolitical * 0.10
            + self.macro * 0.15
        )
        # total darf max 5 Punkte vom gewichteten Wert abweichen (manuelle Anpassung erlaubt)
        assert abs(self.total - round(weighted)) <= 5, (
            f"total={self.total} weicht zu stark vom gewichteten Wert {weighted:.0f} ab"
        )
        return self


class TechnicalLevels(BaseModel):
    """Schlüsselpreismarken für das Signal."""
    support_1: Optional[float] = None
    support_2: Optional[float] = None
    resistance_1: Optional[float] = None
    resistance_2: Optional[float] = None
    moving_avg_50: Optional[float] = None
    moving_avg_200: Optional[float] = None
    rsi_14: Optional[float] = Field(None, ge=0, le=100)
    atr_14: Optional[float] = Field(None, ge=0)


class Signal(BaseModel):
    """
    Handelssignal — erstellt vom Interpretation Layer, konsumiert vom Decision Engine.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    asset_symbol: str = Field(..., description="Ticker-Symbol")
    asset_name: str = Field(..., description="Vollständiger Instrumentenname")

    # Kernurteil
    signal_type: SignalType
    strength: SignalStrength
    score: ScoreBreakdown

    # Preislevels
    price_at_signal: float = Field(..., gt=0, description="Kurs zum Zeitpunkt der Signalerzeugung")
    stop_loss: Optional[float] = Field(None, gt=0)
    target_price: Optional[float] = Field(None, gt=0)
    technical_levels: Optional[TechnicalLevels] = None

    # Begründung
    reasons: List[str] = Field(default_factory=list, description="Bullet-Points warum dieses Signal")
    risks: List[str] = Field(default_factory=list, description="Bekannte Gegenargumente / Risiken")
    catalyst: Optional[str] = Field(None, description="Primärer Auslöser (z.B. Earnings, Fed, Chart)")

    # Layer-Herkunft
    layer_source: str = Field("interpretation_layer", description="Welcher Layer das Signal erzeugt hat")
    regime_context: Optional[str] = Field(None, description="Marktregime zum Signalzeitpunkt")

    # ── Erweiterte Felder (Zyklus- und Erwartungsmodell) ──────────────────────
    decay_function: Optional[str] = Field(
        None, description="Art des Signal-Verfalls: 'linear' | 'exponential' | 'step'"
    )
    lag_seconds: Optional[float] = Field(
        None, ge=0.0,
        description="Erwartete Verzögerung zwischen Signal-Erzeugung und Marktreaktion (Sekunden)"
    )

    # Zeitstempel
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    valid_until: Optional[datetime] = Field(
        None, description="Ablaufzeit des Signals (None = unbegrenzt)"
    )

    @computed_field
    @property
    def crv(self) -> Optional[float]:
        """Chance-Risiko-Verhältnis berechnet aus Einstieg, Stop und Ziel."""
        if self.stop_loss and self.target_price:
            risk = abs(self.price_at_signal - self.stop_loss)
            reward = abs(self.target_price - self.price_at_signal)
            if risk > 0:
                return round(reward / risk, 2)
        return None

    @computed_field
    @property
    def is_expired(self) -> bool:
        if self.valid_until:
            return datetime.utcnow() > self.valid_until
        return False

    model_config = {"use_enum_values": True}

    @classmethod
    def create_with_default_expiry(cls, days: int = 5, **kwargs) -> "Signal":
        """Erstellt ein Signal mit automatischer Ablaufzeit."""
        kwargs["valid_until"] = datetime.utcnow() + timedelta(days=days)
        return cls(**kwargs)
