"""SQLAlchemy ORM-Modell: Trade (Journal)"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import String, Numeric, Integer, DateTime, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.services.database import Base


class TradeModel(Base):
    __tablename__ = "trades"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String(100))
    direction: Mapped[str] = mapped_column(String(4), nullable=False)    # buy, sell
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    entry_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    exit_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    stop_loss: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    take_profit: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="CHF")
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="open")  # open, closed
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    pnl_chf: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    pnl_percent: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    holding_days: Mapped[int | None] = mapped_column(Integer)
    score_at_entry: Mapped[int | None] = mapped_column(Integer)
    crv_achieved: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    stamp_tax_chf: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    bias: Mapped[list | None] = mapped_column(JSON)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
