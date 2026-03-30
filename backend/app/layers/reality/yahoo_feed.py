"""
Reality Layer: YahooFeed
------------------------
Implementiert MarketFeed via Yahoo Finance (yfinance).

Merkmale:
- Historische Daten via yfinance.download() zum Vorbelegen der Preishistorie
- Real-Time Quotes via yfinance.Ticker.fast_info (15-Min-Delay)
- Automatisches Fallback auf letzte bekannte Preise bei Netzwerkfehler
- Schweizer Symbole: NOVN → NOVN.SW, ZGLD → ZGLD.SW
- Streaming-Loop emittiert Events alle interval_sec Sekunden
"""
from __future__ import annotations

import asyncio
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from app.domain.event import Event, EventType, EventSource, EventSeverity
from app.layers.reality.market_feed import MarketFeed

# Mapping: internes Symbol → Yahoo Finance Ticker
_YAHOO_SYMBOLS: Dict[str, str] = {
    "AAPL":  "AAPL",
    "MSFT":  "MSFT",
    "NVDA":  "NVDA",
    "SPY":   "SPY",
    "NOVN":  "NOVN.SW",
    "ZGLD":  "ZGLD.SW",
}

# Fallback-Basispreise falls Yahoo nicht erreichbar
_FALLBACK_PRICES: Dict[str, float] = {
    "AAPL": 228.50,
    "MSFT": 358.20,
    "NVDA": 882.00,
    "SPY":  521.40,
    "NOVN":  97.80,
    "ZGLD": 210.50,
}


class YahooFeed(MarketFeed):
    """
    MarketFeed-Implementierung via Yahoo Finance.

    Lädt beim Start historische Schlusskurse für die Preishistorie.
    Im Live-Modus werden Quotes via fast_info abgefragt und als
    price_update Events emittiert.
    """

    def __init__(self) -> None:
        super().__init__()
        self._connected = False
        self._prices: Dict[str, float] = {}
        self._prev_prices: Dict[str, float] = {}
        self._last_fetch: Optional[datetime] = None
        self._error_count: int = 0

    # ── Interface-Implementierung ──────────────────────────────────────────────

    async def connect(self) -> bool:
        try:
            import yfinance as yf  # lazy import — nur wenn benötigt
            # Verbindungstest: Mini-Download für ein Symbol
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: yf.download("AAPL", period="1d", interval="1d",
                                     progress=False, auto_adjust=True)
            )
            if result is not None and not result.empty:
                self._connected = True
                self._error_count = 0
                self._last_fetch = datetime.utcnow()
                await self._emit(Event(
                    event_type=EventType.ibkr_connected,
                    source=EventSource.reality_layer,
                    message="YahooFeed verbunden (Yahoo Finance)",
                ))
                return True
        except Exception as exc:
            print(f"[YahooFeed] Verbindungsfehler: {exc}")

        self._connected = False
        return False

    async def disconnect(self) -> None:
        self._connected = False
        self.stop_streaming()

    @property
    def is_connected(self) -> bool:
        return self._connected

    async def start_streaming(
        self,
        symbols: List[str],
        interval_sec: float = 30.0,
    ) -> None:
        """
        Polling-Loop: fragt Yahoo Finance alle interval_sec Sekunden ab.
        Emittiert price_update Events pro Symbol.
        """
        import yfinance as yf

        # Initiale Preise laden
        for sym in symbols:
            if sym not in self._prices:
                self._prices[sym] = _FALLBACK_PRICES.get(sym, 100.0)

        self._streaming = True

        while self._streaming:
            for sym in symbols:
                try:
                    yahoo_sym = _YAHOO_SYMBOLS.get(sym, sym)
                    loop = asyncio.get_event_loop()

                    ticker_info = await loop.run_in_executor(
                        None,
                        lambda s=yahoo_sym: yf.Ticker(s).fast_info
                    )

                    price = getattr(ticker_info, "last_price", None)
                    if price is None or price <= 0:
                        # Fallback: letzten bekannten Preis leicht simulieren
                        price = self._prices.get(sym, _FALLBACK_PRICES.get(sym, 100.0))
                        price *= (1 + random.gauss(0, 0.001))

                    prev = self._prices.get(sym, price)
                    change = round(price - prev, 4)
                    change_pct = round((change / prev) * 100, 3) if prev else 0.0

                    self._prev_prices[sym] = prev
                    self._prices[sym] = price
                    self._last_fetch = datetime.utcnow()
                    self._error_count = 0

                    volume = getattr(ticker_info, "three_month_average_volume", 1_000_000)
                    if volume is None:
                        volume = 1_000_000

                    event = Event.price_update(
                        symbol=sym,
                        price=round(price, 4),
                        change=change,
                        change_percent=change_pct,
                        source="yahoo",
                    )
                    event.payload.update({
                        "volume": int(volume),
                        "bid": round(price * 0.9999, 4),
                        "ask": round(price * 1.0001, 4),
                        "high": round(price * 1.002, 4),
                        "low":  round(price * 0.998, 4),
                    })
                    await self._emit(event)

                except Exception as exc:
                    self._error_count += 1
                    print(f"[YahooFeed] Fehler für {sym}: {exc}")

                    if self._error_count >= 5:
                        print("[YahooFeed] Zu viele Fehler — Verbindung markiert als unterbrochen")
                        self._connected = False

                    # Letzten bekannten Preis mit minimalem Rauschen emittieren
                    fallback_price = self._prices.get(sym, _FALLBACK_PRICES.get(sym, 100.0))
                    fallback_price *= (1 + random.gauss(0, 0.0005))
                    self._prices[sym] = round(fallback_price, 4)

                    event = Event.price_update(
                        symbol=sym,
                        price=round(fallback_price, 4),
                        change=0.0,
                        change_percent=0.0,
                        source="yahoo_fallback",
                    )
                    await self._emit(event)

            await asyncio.sleep(interval_sec)

    # ── Historische Daten ──────────────────────────────────────────────────────

    async def fetch_history(
        self,
        symbol: str,
        days: int = 30,
    ) -> List[float]:
        """
        Lädt historische Schlusskurse für symbol via yfinance.download().
        Gibt eine Liste von Preisen zurück (älteste zuerst).
        Fällt auf leere Liste zurück bei Fehler.
        """
        try:
            import yfinance as yf
            yahoo_sym = _YAHOO_SYMBOLS.get(symbol, symbol)
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days + 5)  # Puffer für Wochenenden

            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None,
                lambda: yf.download(
                    yahoo_sym,
                    start=start_date.strftime("%Y-%m-%d"),
                    end=end_date.strftime("%Y-%m-%d"),
                    interval="1d",
                    progress=False,
                    auto_adjust=True,
                )
            )

            if df is None or df.empty:
                return []

            # MultiIndex: columns like ("Close", "MSFT") — flatten by taking first level
            if isinstance(df.columns, __import__("pandas").MultiIndex):
                # Select "Close" level, drop ticker level
                close_series = df["Close"].iloc[:, 0] if hasattr(df["Close"], "iloc") else df["Close"]
            else:
                close_series = df["Close"]

            prices = close_series.dropna().tail(days).values.tolist()
            return [float(p) for p in prices]

        except Exception as exc:
            print(f"[YahooFeed] History-Fehler für {symbol}: {exc}")
            return []

    @property
    def last_fetch(self) -> Optional[datetime]:
        return self._last_fetch
