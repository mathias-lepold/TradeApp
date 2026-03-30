"""SQLAlchemy ORM-Modell: Asset"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import String, Float, Integer, DateTime, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.services.database import Base


class AssetModel(Base):
    __tablename__ = "assets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    asset_type: Mapped[str] = mapped_column(
        SAEnum("stock", "etf", "crypto", "forex", "commodity", "bond", "index", name="asset_type_enum"),
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    exchange: Mapped[str] = mapped_column(String(50), nullable=False)
    sector: Mapped[str | None] = mapped_column(String(100))
    industry: Mapped[str | None] = mapped_column(String(100))
    country: Mapped[str | None] = mapped_column(String(2))
    isin: Mapped[str | None] = mapped_column(String(12))
    last_price: Mapped[float | None] = mapped_column(Float)
    market_cap: Mapped[float | None] = mapped_column(Float)
    avg_daily_volume: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(
        SAEnum("active", "halted", "delisted", "watchlist", name="asset_status_enum"),
        nullable=False,
        default="active",
    )
    ibkr_con_id: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
