"""
Domain Model: Asset
Repräsentiert ein handelbares Finanzinstrument (Aktie, ETF, Forex, Crypto, Rohstoff).
"""
from __future__ import annotations

from enum import Enum
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, model_validator
import uuid


class AssetType(str, Enum):
    stock = "stock"
    etf = "etf"
    crypto = "crypto"
    forex = "forex"
    commodity = "commodity"
    bond = "bond"
    index = "index"


class AssetStatus(str, Enum):
    active = "active"
    halted = "halted"
    delisted = "delisted"
    watchlist = "watchlist"


class Asset(BaseModel):
    """
    Kernobjekt: ein handelbares Finanzinstrument.
    Wird vom Reality Layer erstellt und durch alle Layers weitergereicht.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    symbol: str = Field(..., min_length=1, max_length=20, description="Ticker-Symbol (z.B. NVDA, NOVN, USDCHF)")
    name: str = Field(..., description="Vollständiger Name des Instruments")
    asset_type: AssetType
    currency: str = Field(..., min_length=3, max_length=3, description="ISO 4217 Währungscode")
    exchange: str = Field(..., description="Börsenplatz (z.B. SMART, SWX, NASDAQ)")

    # Klassifikation
    sector: Optional[str] = Field(None, description="GICS-Sektor (z.B. Technology, Healthcare)")
    industry: Optional[str] = Field(None, description="GICS-Industrie")
    country: Optional[str] = Field(None, description="ISO 3166-1 alpha-2 Ländercode")
    isin: Optional[str] = Field(None, min_length=12, max_length=12, description="ISIN-Kennung")

    # Marktdaten (snapshot)
    last_price: Optional[float] = Field(None, ge=0)
    market_cap: Optional[float] = Field(None, ge=0, description="Marktkapitalisierung in USD")
    avg_daily_volume: Optional[int] = Field(None, ge=0)

    # Metadaten
    status: AssetStatus = AssetStatus.active
    ibkr_con_id: Optional[int] = Field(None, description="IBKR Contract ID für direkten API-Zugriff")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @model_validator(mode="after")
    def normalize_symbol(self) -> "Asset":
        self.symbol = self.symbol.upper()
        self.currency = self.currency.upper()
        return self

    model_config = {"use_enum_values": True}
