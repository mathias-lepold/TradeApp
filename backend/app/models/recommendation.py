"""SQLAlchemy ORM-Modell: Recommendation"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import String, Float, DateTime, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.services.database import Base


class RecommendationModel(Base):
    __tablename__ = "recommendations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(20), nullable=False)      # buy, sell, hold, add, reduce, exit, avoid, rebalance, wait
    priority: Mapped[str] = mapped_column(String(20), nullable=False)    # urgent, high, normal, low
    signal_id: Mapped[str | None] = mapped_column(String(36), index=True)
    regime_id: Mapped[str | None] = mapped_column(String(36))
    total_score: Mapped[float | None] = mapped_column(Float)
    bias_risk: Mapped[dict | None] = mapped_column(JSON)                 # BiasRisk as dict
    position_sizing: Mapped[dict | None] = mapped_column(JSON)          # PositionSizing as dict
    reasons: Mapped[list | None] = mapped_column(JSON)
    risks: Mapped[list | None] = mapped_column(JSON)
    invalidation_conditions: Mapped[list | None] = mapped_column(JSON)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
