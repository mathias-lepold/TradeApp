"""
Reality Layer: DataNormalizer
Konvertiert rohe Daten aus verschiedenen Quellen in einheitliche Domain-Objekte.
"""
from __future__ import annotations

from typing import Dict, Any, Optional
from datetime import datetime

from app.domain.asset import Asset, AssetType, AssetStatus
from app.domain.event import Event, EventType, EventSource


# Statische Konfiguration bekannter Instrumente
KNOWN_ASSETS: Dict[str, Dict[str, Any]] = {
    "MSFT":  {"name": "Microsoft Corporation", "type": AssetType.stock,     "exchange": "SMART", "currency": "USD", "sector": "Technology"},
    "NVDA":  {"name": "NVIDIA Corporation",    "type": AssetType.stock,     "exchange": "SMART", "currency": "USD", "sector": "Technology"},
    "AAPL":  {"name": "Apple Inc.",            "type": AssetType.stock,     "exchange": "SMART", "currency": "USD", "sector": "Technology"},
    "AMZN":  {"name": "Amazon.com Inc.",       "type": AssetType.stock,     "exchange": "SMART", "currency": "USD", "sector": "Consumer Discretionary"},
    "GOOGL": {"name": "Alphabet Inc.",         "type": AssetType.stock,     "exchange": "SMART", "currency": "USD", "sector": "Communication Services"},
    "META":  {"name": "Meta Platforms Inc.",   "type": AssetType.stock,     "exchange": "SMART", "currency": "USD", "sector": "Communication Services"},
    "NOVN":  {"name": "Novartis AG",           "type": AssetType.stock,     "exchange": "SWX",   "currency": "CHF", "sector": "Healthcare",   "country": "CH"},
    "NESN":  {"name": "Nestlé SA",             "type": AssetType.stock,     "exchange": "SWX",   "currency": "CHF", "sector": "Consumer Staples", "country": "CH"},
    "ZGLD":  {"name": "ZKB Gold ETF AA",       "type": AssetType.etf,       "exchange": "SWX",   "currency": "CHF", "sector": "Commodities",  "country": "CH"},
    "XAUUSD":{"name": "Gold Spot USD",         "type": AssetType.commodity, "exchange": "IDEALPRO", "currency": "USD", "sector": "Commodities"},
}


class DataNormalizer:
    """
    Wandelt rohe API-Antworten in typisierte Domain-Objekte um.
    Zentrale Stelle für alle Datenformat-Konvertierungen im Reality Layer.
    """

    @staticmethod
    def symbol_to_asset(symbol: str) -> Asset:
        """
        Erstellt ein Asset-Objekt aus einem Ticker-Symbol.
        Nutzt KNOWN_ASSETS für bekannte Instrumente, sonst Defaults.
        """
        sym = symbol.upper()
        config = KNOWN_ASSETS.get(sym, {
            "name": sym,
            "type": AssetType.stock,
            "exchange": "SMART",
            "currency": "USD",
            "sector": None,
        })
        return Asset(
            symbol=sym,
            name=config["name"],
            asset_type=config["type"],
            exchange=config["exchange"],
            currency=config["currency"],
            sector=config.get("sector"),
            country=config.get("country"),
        )

    @staticmethod
    def ibkr_bar_to_price_dict(bars: list, symbol: str) -> Dict[str, Any]:
        """
        Konvertiert eine ib_insync BarData-Liste in ein standardisiertes Preis-Dict.
        """
        if not bars:
            return {}
        last = bars[-1]
        prev = bars[-2] if len(bars) > 1 else last
        change = round(last.close - prev.close, 4)
        change_pct = round((change / prev.close) * 100, 3) if prev.close else 0.0
        return {
            "symbol": symbol.upper(),
            "price": last.close,
            "open": last.open,
            "high": last.high,
            "low": last.low,
            "close": last.close,
            "volume": int(last.volume),
            "change": change,
            "change_percent": change_pct,
            "bar_time": last.date,
            "normalized_at": datetime.utcnow(),
            "source": "ibkr_historical",
        }

    @staticmethod
    def price_dict_to_event(data: Dict[str, Any]) -> Event:
        """Wandelt ein normalisiertes Preis-Dict in ein price_update Event um."""
        return Event.price_update(
            symbol=data["symbol"],
            price=data["price"],
            change=data["change"],
            change_percent=data["change_percent"],
            source=data.get("source", "unknown"),
        )

    @staticmethod
    def enrich_asset_with_price(asset: Asset, price_data: Dict[str, Any]) -> Asset:
        """Fügt einem Asset-Objekt aktuelle Preisdaten hinzu."""
        asset.last_price = price_data.get("price")
        asset.avg_daily_volume = price_data.get("volume")
        asset.updated_at = datetime.utcnow()
        return asset
