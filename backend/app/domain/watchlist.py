"""Domain: Watchlist"""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class WatchlistItem(BaseModel):
    id:            str
    symbol:        str
    name:          str = ""
    target_price:  Optional[float] = None
    alert_price:   Optional[float] = None
    notes:         str = ""
    added_at:      datetime
    current_price: float = 0.0
    change_pct:    float = 0.0
    signal_score:  Optional[int] = None
    signal_type:   Optional[str] = None
    data_source:   str = "mock"


class WatchlistAdd(BaseModel):
    symbol:       str
    name:         str = ""
    target_price: Optional[float] = None
    notes:        str = ""
