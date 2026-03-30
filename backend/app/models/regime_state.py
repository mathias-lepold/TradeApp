"""SQLAlchemy ORM-Modell: RegimeState"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import String, Float, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.services.database import Base


class RegimeStateModel(Base):
    __tablename__ = "regime_states"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    regime_type: Mapped[str] = mapped_column(
        String(30), nullable=False, index=True
    )  # bull_market, bear_market, sideways, volatile, crisis, recovery
    sub_regime: Mapped[str | None] = mapped_column(String(30))  # risk_on, risk_off, trending_up, ...
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    strength: Mapped[float] = mapped_column(Float, nullable=False)
    characteristics: Mapped[list | None] = mapped_column(JSON)
    active_risks: Mapped[list | None] = mapped_column(JSON)
    position_sizing_rules: Mapped[dict | None] = mapped_column(JSON)
    macro_snapshot: Mapped[dict | None] = mapped_column(JSON)   # MacroSnapshot as dict
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
