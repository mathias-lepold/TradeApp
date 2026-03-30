"""
Domain: Portfolio
-----------------
Pydantic-Schemas für Portfolio-Verwaltung.

Position     — Offene Position mit aktuellem PnL
PortfolioTrade — Erfasster Trade (Kauf oder Verkauf)
PortfolioSummary — Gesamtübersicht des Portfolios
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from enum import Enum

from pydantic import BaseModel, Field


class TradeAction(str, Enum):
    buy  = "buy"
    sell = "sell"


# ── Position ──────────────────────────────────────────────────────────────────

class Position(BaseModel):
    symbol:             str
    name:               str = ""
    quantity:           float
    avg_entry_price:    float           # in Originalwährung
    current_price:      float           # in Originalwährung
    currency:           str = "CHF"
    unrealized_pnl:     float           # in CHF
    unrealized_pnl_pct: float           # in Prozent
    realized_pnl:       float = 0.0    # realisierte PnL in CHF (aus Verkäufen)
    value_chf:          float           # aktueller Positionswert in CHF
    cost_basis_chf:     float           # Einstandskosten in CHF
    weight_pct:         float = 0.0     # Anteil am Gesamtportfolio
    opened_at:          Optional[datetime] = None
    data_source:        str = "mock"


# ── Trade ─────────────────────────────────────────────────────────────────────

class PortfolioTrade(BaseModel):
    id:         str
    symbol:     str
    action:     TradeAction
    quantity:   float
    price:      float           # Preis in Originalwährung
    fees:       float = 0.0    # Gebühren in CHF
    currency:   str = "CHF"
    timestamp:  datetime
    notes:      str = ""

    # Berechnete Felder
    value_chf:  float = 0.0    # quantity * price * fx_rate
    total_chf:  float = 0.0    # value_chf + fees (bei Kauf) oder value_chf - fees (bei Verkauf)


class PortfolioTradeCreate(BaseModel):
    symbol:   str
    action:   TradeAction
    quantity: float = Field(gt=0)
    price:    float = Field(gt=0)
    fees:     float = Field(default=0.0, ge=0)
    currency: str   = "CHF"
    notes:    str   = ""
    timestamp: Optional[datetime] = None  # default: now


# ── Portfolio Summary ─────────────────────────────────────────────────────────

class PortfolioSummary(BaseModel):
    # Werte
    starting_capital_chf: float
    total_value_chf:      float    # Positionen + Cash
    invested_chf:         float    # Einstandswert aller Positionen
    cash_chf:             float    # verfügbares Kapital
    positions_value_chf:  float    # aktueller Wert aller Positionen

    # PnL
    total_pnl_chf:        float    # unrealisiert + realisiert
    total_pnl_pct:        float
    unrealized_pnl_chf:   float
    realized_pnl_chf:     float
    today_pnl_chf:        float = 0.0

    # Listen
    positions: List[Position]
    trades:    List[PortfolioTrade]

    # Meta
    num_trades:      int = 0
    num_open_pos:    int = 0
    last_updated:    datetime = Field(default_factory=datetime.utcnow)
