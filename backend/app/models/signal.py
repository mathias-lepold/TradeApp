"""SQLAlchemy ORM-Modell: Signal"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import String, Float, DateTime, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.services.database import Base


class SignalModel(Base):
    __tablename__ = "signals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    signal_type: Mapped[str] = mapped_column(String(20), nullable=False)  # buy, sell, hold, avoid, reduce, add
    strength: Mapped[str] = mapped_column(String(20), nullable=False)     # strong, moderate, weak
    confidence: Mapped[str] = mapped_column(String(20), nullable=False)   # high, medium, low
    total_score: Mapped[float] = mapped_column(Float, nullable=False)
    score_breakdown: Mapped[dict | None] = mapped_column(JSON)            # ScoreBreakdown as dict
    technical_levels: Mapped[dict | None] = mapped_column(JSON)          # TechnicalLevels as dict
    entry_price: Mapped[float | None] = mapped_column(Float)
    stop_loss: Mapped[float | None] = mapped_column(Float)
    take_profit: Mapped[float | None] = mapped_column(Float)
    reasons: Mapped[list | None] = mapped_column(JSON)
    catalyst: Mapped[str | None] = mapped_column(Text)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
