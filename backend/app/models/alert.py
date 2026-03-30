"""SQLAlchemy ORM-Modell: Alert"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import String, Numeric, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.services.database import Base


class AlertModel(Base):
    __tablename__ = "alerts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    threshold: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    direction: Mapped[str] = mapped_column(String(5), nullable=False)    # above, below
    triggered: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    triggered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
