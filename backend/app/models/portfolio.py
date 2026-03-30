"""SQLAlchemy ORM-Modell: PortfolioTradeModel"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import String, Numeric, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.services.database import Base


class PortfolioTradeModel(Base):
    """
    Persistierte Portfolio-Trades.
    Separate Tabelle von `trades` (Journal) — portfolio_trades enthält
    die tatsächlichen Käufe/Verkäufe zur Portfolio-Berechnung.
    """
    __tablename__ = "portfolio_trades"

    id:        Mapped[str] = mapped_column(String(36), primary_key=True)
    symbol:    Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    action:    Mapped[str] = mapped_column(String(4), nullable=False)   # buy | sell
    quantity:  Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    price:     Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    fees:      Mapped[float] = mapped_column(Numeric(10, 4), nullable=False, default=0.0)
    currency:  Mapped[str] = mapped_column(String(3), nullable=False, default="CHF")
    notes:     Mapped[str | None] = mapped_column(Text)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
