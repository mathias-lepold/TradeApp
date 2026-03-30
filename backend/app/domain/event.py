"""
Domain Model: Event
Universelles Ereignis-Objekt, das durch das System fließt (Reality → Interpretation → Decision).
Dient als gemeinsame Sprache aller Layer.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional, Any, Dict, List
from datetime import datetime
from pydantic import BaseModel, Field
import uuid


class EventType(str, Enum):
    # Reality Layer Events
    price_update = "price_update"          # Neuer Kurs eingetroffen
    trade_executed = "trade_executed"      # Order wurde ausgeführt
    market_open = "market_open"            # Börse öffnet
    market_close = "market_close"          # Börse schließt
    ibkr_connected = "ibkr_connected"      # IBKR-Verbindung hergestellt
    ibkr_disconnected = "ibkr_disconnected"

    # Interpretation Layer Events
    signal_generated = "signal_generated"  # Neues Handelssignal
    regime_changed = "regime_changed"      # Marktregime hat gewechselt
    indicator_alert = "indicator_alert"    # Technischer Indikator ausgelöst
    news_parsed = "news_parsed"            # Nachricht verarbeitet

    # Behavioral Layer Events
    bias_detected = "bias_detected"        # Verhaltens-Bias erkannt
    pattern_match = "pattern_match"        # Verhaltens-Muster identifiziert

    # Decision Engine Events
    recommendation_issued = "recommendation_issued"  # Empfehlung ausgegeben
    risk_limit_breached = "risk_limit_breached"      # Risikograenze überschritten
    rebalance_triggered = "rebalance_triggered"

    # System Events
    system_error = "system_error"
    system_warning = "system_warning"
    cache_miss = "cache_miss"


class EventSeverity(str, Enum):
    info = "info"
    warning = "warning"
    critical = "critical"
    emergency = "emergency"


class EventSource(str, Enum):
    reality_layer = "reality_layer"
    interpretation_layer = "interpretation_layer"
    behavioral_layer = "behavioral_layer"
    decision_engine = "decision_engine"
    ibkr = "ibkr"
    system = "system"
    user = "user"


class Event(BaseModel):
    """
    Generisches Ereignis-Objekt.
    Alle Layer kommunizieren via Events — ermöglicht vollständiges Audit-Log.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType
    source: EventSource
    severity: EventSeverity = EventSeverity.info

    # Optionale Verknüpfung mit einem Asset
    asset_symbol: Optional[str] = Field(None, description="Betroffenes Symbol, falls zutreffend")

    # Inhalt
    payload: Dict[str, Any] = Field(default_factory=dict, description="Layer-spezifische Daten")
    message: Optional[str] = Field(None, description="Menschenlesbare Beschreibung")

    # Verknüpfungen
    parent_event_id: Optional[str] = Field(None, description="ID des auslösenden Events (Kausalkette)")
    correlation_id: Optional[str] = Field(None, description="Gruppen-ID für zusammengehörige Events")
    tags: List[str] = Field(default_factory=list)

    # Zeitstempel
    occurred_at: datetime = Field(default_factory=datetime.utcnow, description="Wann das Ereignis eintrat")
    processed_at: Optional[datetime] = Field(None, description="Wann das Event verarbeitet wurde")

    # ── Erweiterte Felder (Zyklus- und Erwartungsmodell) ──────────────────────
    relevance:          Optional[float] = Field(None, ge=0.0, le=1.0,
                                                description="Relevanz für aktuelles Regime 0–1")
    confidence:         Optional[float] = Field(None, ge=0.0, le=1.0,
                                                description="Konfidenz der Event-Interpretation 0–1")
    expected_half_life: Optional[float] = Field(None, ge=0.0,
                                                description="Erwartete Halbwertszeit des Effekts (Stunden)")
    expected_lag:       Optional[float] = Field(None, ge=0.0,
                                                description="Erwartete Verzögerung bis Marktreaktion (Stunden)")
    direct_impact:      Optional[str]   = Field(None,
                                                description="Direkte Auswirkung auf betroffenes Asset")
    indirect_impact:    Optional[str]   = Field(None,
                                                description="Indirekte Auswirkungen auf andere Assets / Sektoren")
    narrative_tag:      Optional[str]   = Field(None,
                                                description="Narrativ-Kategorie z.B. 'Fed Pivot', 'Earnings Beat'")

    model_config = {"use_enum_values": True}

    @classmethod
    def price_update(
        cls,
        symbol: str,
        price: float,
        change: float,
        change_percent: float,
        source: str = "ibkr",
    ) -> "Event":
        """Factory-Methode für Kurs-Updates."""
        return cls(
            event_type=EventType.price_update,
            source=EventSource.reality_layer,
            asset_symbol=symbol,
            payload={
                "price": price,
                "change": change,
                "change_percent": change_percent,
                "data_source": source,
            },
            message=f"{symbol} @ {price} ({change_percent:+.2f}%)",
        )

    @classmethod
    def signal_generated(cls, symbol: str, signal_id: str, verdict: str, score: int) -> "Event":
        """Factory-Methode für neue Signale."""
        return cls(
            event_type=EventType.signal_generated,
            source=EventSource.interpretation_layer,
            asset_symbol=symbol,
            payload={"signal_id": signal_id, "verdict": verdict, "score": score},
            message=f"Signal [{verdict.upper()}] für {symbol} — Score {score}",
            severity=EventSeverity.info if verdict == "hold" else EventSeverity.warning,
        )
