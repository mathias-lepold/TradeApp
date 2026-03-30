"""
Domain Model: Recommendation
Finale Handlungsempfehlung des Decision Engines.
Integriert Signal + RegimeState + Behavioral Score zu einer konkreten Aktion.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from pydantic import BaseModel, Field, computed_field, model_validator
import uuid


class RecommendationAction(str, Enum):
    buy = "buy"
    sell = "sell"
    hold = "hold"
    add = "add"               # Bestehende Position aufstocken
    reduce = "reduce"         # Teilverkauf
    exit = "exit"             # Vollständiger Ausstieg
    avoid = "avoid"           # Nicht einsteigen
    rebalance = "rebalance"   # Portfolio neu gewichten
    wait = "wait"             # Abwarten (Signal nicht reif)


class RecommendationPriority(str, Enum):
    urgent = "urgent"         # Sofortiges Handeln empfohlen
    high = "high"             # Innerhalb 1–2 Tage
    normal = "normal"         # Diese Woche
    low = "low"               # Langfristig, keine Eile


class BiasRisk(BaseModel):
    """Bewertung des Verhaltens-Bias-Risikos durch den Behavioral Layer."""
    overall_score: int = Field(..., ge=0, le=100, description="0=kein Bias, 100=stark biased")
    detected_biases: List[str] = Field(
        default_factory=list,
        description="Erkannte Biases (z.B. ['fomo', 'loss_aversion'])"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Warnhinweise für den Trader"
    )
    recommendation_adjusted: bool = Field(
        False,
        description="True wenn die Empfehlung wegen Bias-Erkennung angepasst wurde"
    )


class PositionSizing(BaseModel):
    """Berechnung der optimalen Positionsgröße."""
    suggested_pct: float = Field(..., ge=0.1, le=15.0, description="% des Portfolios")
    suggested_chf: Optional[float] = Field(None, ge=0)
    suggested_shares: Optional[float] = Field(None, ge=0)
    max_pct_by_regime: float = Field(..., description="Vom Regime erlaubtes Maximum")
    kelly_fraction: Optional[float] = Field(None, ge=0, le=1.0, description="Kelly-Kriterium")
    risk_per_trade_chf: Optional[float] = Field(None, ge=0)
    risk_pct_of_portfolio: Optional[float] = Field(None, ge=0)


class Recommendation(BaseModel):
    """
    Abschliessende, actionable Empfehlung des Decision Engines.
    Aggregiert alle Layers zu einer einzigen, klaren Handlungsanweisung.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    asset_symbol: str
    asset_name: str

    # Kernaussage
    action: RecommendationAction
    priority: RecommendationPriority = RecommendationPriority.normal
    rationale: str = Field(..., description="Kompakte Begründung (1–3 Sätze)")

    # Quellen-IDs (Rückverfolgbarkeit)
    signal_id: Optional[str] = Field(None, description="Zugrunde liegendes Signal")
    regime_state_id: Optional[str] = Field(None, description="Marktregime zum Zeitpunkt")

    # Preislevel
    entry_price: Optional[float] = Field(None, gt=0)
    stop_loss: Optional[float] = Field(None, gt=0)
    target_price: Optional[float] = Field(None, gt=0)

    # Positionsgrösse
    sizing: Optional[PositionSizing] = None

    # Behavior-Analyse
    bias_risk: Optional[BiasRisk] = None

    # Kontext
    regime_summary: Optional[str] = Field(None, description="Kurzbeschreibung des Marktregimes")
    key_risks: List[str] = Field(default_factory=list)
    conditions_to_invalidate: List[str] = Field(
        default_factory=list,
        description="Bedingungen die diese Empfehlung entwerten (z.B. 'Kurs < 85 CHF')"
    )

    # ── Erweiterte Felder (Szenarioanalyse + Hypothesen) ─────────────────────
    no_trade_flag:      bool           = Field(
        False, description="True wenn Regime zu instabil für Eintritt"
    )
    base_hypothesis:    Optional[str]  = Field(
        None, description="Kompakte Basishypothese (1–2 Sätze)"
    )
    counter_hypothesis: Optional[str]  = Field(
        None, description="Explizite Gegenhypothese (Falsifizierbarkeit)"
    )
    scenario_analysis:  Optional[Dict[str, float]] = Field(
        None, description="Szenarien mit Wahrscheinlichkeiten: {'bull': 0.6, 'base': 0.3, 'bear': 0.1}"
    )
    uncertainty_level:  Optional[str]  = Field(
        None, description="'low' | 'medium' | 'high' — explizite Unsicherheitsangabe"
    )

    # Engine-Metadaten
    decision_engine_version: str = Field("2.0.0")
    composite_score: Optional[int] = Field(None, ge=0, le=100, description="Gesamtscore aus allen Layers")

    # Zeitstempel
    created_at: datetime = Field(default_factory=datetime.utcnow)
    valid_until: Optional[datetime] = None
    acted_on_at: Optional[datetime] = Field(None, description="Wann der Trader gehandelt hat")
    acted_on: bool = False

    @model_validator(mode="after")
    def set_default_expiry(self) -> "Recommendation":
        if self.valid_until is None:
            days = {"urgent": 1, "high": 2, "normal": 5, "low": 14}
            self.valid_until = self.created_at + timedelta(
                days=days.get(self.priority, 5)
            )
        return self

    @computed_field
    @property
    def crv(self) -> Optional[float]:
        if self.stop_loss and self.target_price and self.entry_price:
            risk = abs(self.entry_price - self.stop_loss)
            reward = abs(self.target_price - self.entry_price)
            if risk > 0:
                return round(reward / risk, 2)
        return None

    @computed_field
    @property
    def is_expired(self) -> bool:
        if self.valid_until:
            return datetime.utcnow() > self.valid_until
        return False

    @computed_field
    @property
    def has_bias_warning(self) -> bool:
        return self.bias_risk is not None and self.bias_risk.overall_score > 40

    model_config = {"use_enum_values": True}
