"""Domain: Alerts"""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field


class AlertCondition(str, Enum):
    price_above        = "price_above"
    price_below        = "price_below"
    signal_score_above = "signal_score_above"
    signal_score_below = "signal_score_below"
    regime_change      = "regime_change"


class AlertConfig(BaseModel):
    id:              str
    symbol:          str
    condition:       AlertCondition
    threshold:       float
    active:          bool = True
    triggered:       bool = False
    triggered_at:    Optional[datetime] = None
    triggered_value: Optional[float] = None
    notes:           str = ""
    created_at:      datetime


class AlertCreate(BaseModel):
    symbol:    str
    condition: AlertCondition
    threshold: float = Field(ge=0)
    notes:     str = ""


class AlertEvent(BaseModel):
    alert_id:        str
    symbol:          str
    condition:       AlertCondition
    threshold:       float
    triggered_value: float
    triggered_at:    datetime
    message:         str
