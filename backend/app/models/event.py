"""SQLAlchemy ORM-Modell: Event"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import String, DateTime, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.services.database import Base


class EventModel(Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="info")
    symbol: Mapped[str | None] = mapped_column(String(20), index=True)
    payload: Mapped[dict | None] = mapped_column(JSON)
    parent_id: Mapped[str | None] = mapped_column(String(36))
    correlation_id: Mapped[str | None] = mapped_column(String(36), index=True)
    message: Mapped[str | None] = mapped_column(Text)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
