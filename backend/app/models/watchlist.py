"""SQLAlchemy ORM-Modell: Watchlist"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import String, Numeric, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.services.database import Base


class WatchlistModel(Base):
    __tablename__ = "watchlist"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, unique=True, index=True)
    name: Mapped[str | None] = mapped_column(String(100))
    target_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    alert_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    notes: Mapped[str | None] = mapped_column(Text)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
