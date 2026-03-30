"""
Reality Layer: MarketFeed (abstrakte Basis) + MockFeed
------------------------------------------------------
MarketFeed  — abstrakte Schnittstelle für alle Marktdaten-Quellen.
MockFeed    — realistische Test-Implementierung ohne IBKR-Verbindung.

Konkrete Implementierungen:
  - IBKRFeed   (ibkr_feed.py)   — Real-Time via ib_insync
  - MockFeed   (dieses Modul)   — Simulierte Daten für Tests
"""
from __future__ import annotations

import asyncio
import random
from abc import ABC, abstractmethod
from typing import Callable, Awaitable, Dict, List, Optional
from datetime import datetime

from app.domain.event import Event, EventType, EventSource, EventSeverity


# Typ-Alias für Event-Handler
EventHandler = Callable[[Event], Awaitable[None]]


# ── Abstrakte Basis ────────────────────────────────────────────────────────────

class MarketFeed(ABC):
    """
    Abstrakte Basis-Klasse für alle Marktdaten-Quellen.

    Jede Implementierung (IBKR, Mock, externe API) erbt von hier und
    implementiert `connect`, `start_streaming` und `stop_streaming`.
    Der Event-Bus (`subscribe` / `_emit`) ist in der Basis eingebaut.

    Beispiel:
        feed = IBKRFeed()
        await feed.connect()
        feed.subscribe(EventType.price_update, my_handler)
        await feed.start_streaming(["NVDA", "MSFT"])
    """

    def __init__(self) -> None:
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._streaming = False

    # ── Event-Bus ──────────────────────────────────────────────────────────────

    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Registriert einen async Handler für einen Event-Typ."""
        key = str(event_type.value) if hasattr(event_type, "value") else str(event_type)
        self._handlers.setdefault(key, []).append(handler)

    def unsubscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Entfernt einen Handler."""
        key = str(event_type.value) if hasattr(event_type, "value") else str(event_type)
        handlers = self._handlers.get(key, [])
        if handler in handlers:
            handlers.remove(handler)

    async def _emit(self, event: Event) -> None:
        """Verteilt ein Event an alle registrierten Handler dieses Typs."""
        event.processed_at = datetime.utcnow()
        key = str(event.event_type)
        for handler in list(self._handlers.get(key, [])):
            try:
                await handler(event)
            except Exception as exc:
                print(f"[{self.__class__.__name__}] Handler-Fehler ({key}): {exc}")

    # ── Interface ──────────────────────────────────────────────────────────────

    @abstractmethod
    async def connect(self) -> bool:
        """Stellt Verbindung zur Datenquelle her. True = Erfolg."""
        ...

    @abstractmethod
    async def disconnect(self) -> None:
        """Beendet die Verbindung sauber."""
        ...

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Gibt an ob die Verbindung aktiv ist."""
        ...

    @abstractmethod
    async def start_streaming(
        self,
        symbols: List[str],
        interval_sec: float = 30.0,
    ) -> None:
        """
        Startet den Datenstrom für die angegebenen Symbole.
        Emittiert `price_update` Events über den Event-Bus.
        """
        ...

    def stop_streaming(self) -> None:
        """Stoppt den laufenden Datenstrom."""
        self._streaming = False


# ── Mock-Feed ──────────────────────────────────────────────────────────────────

# Basis-Kurse für den Mock (annähernd realistisch — Stand Q1 2026)
_MOCK_BASE: Dict[str, Dict] = {
    "AAPL": {"price": 228.50, "name": "Apple Inc.",       "daily_vol": 0.018, "volume_base": 58_000_000},
    "MSFT": {"price": 358.20, "name": "Microsoft Corp.",  "daily_vol": 0.016, "volume_base": 22_000_000},
    "NVDA": {"price": 882.00, "name": "NVIDIA Corp.",     "daily_vol": 0.028, "volume_base": 45_000_000},
    "SPY":  {"price": 521.40, "name": "SPDR S&P 500 ETF","daily_vol": 0.012, "volume_base": 80_000_000},
    "NOVN": {"price":  97.80, "name": "Novartis AG",      "daily_vol": 0.010, "volume_base":  3_200_000},
    "ZGLD": {"price": 210.50, "name": "ZKB Gold ETF",     "daily_vol": 0.008, "volume_base":     90_000},
}


class MockFeed(MarketFeed):
    """
    Mock-Implementierung des MarketFeed für Tests und Entwicklung.

    Generiert realistische Zufallskurse mit Mean-Reversion und simulierten
    Volumen-Schwankungen. Keine IBKR-Verbindung erforderlich.

    Merkmale:
    - Brownsche Bewegung mit konfigurierbarer Volatilität pro Symbol
    - Simulierter Intraday-Rhythmus (höheres Volumen zur Marktöffnung)
    - Identisches Event-Interface wie IBKRFeed
    """

    def __init__(self, seed: Optional[int] = None) -> None:
        super().__init__()
        if seed is not None:
            random.seed(seed)
        # Laufende Kurse — werden pro Tick aktualisiert
        self._prices: Dict[str, float] = {
            sym: cfg["price"] for sym, cfg in _MOCK_BASE.items()
        }
        self._connected = False
        self._tick_counter = 0

    # ── Interface-Implementierung ──────────────────────────────────────────────

    async def connect(self) -> bool:
        self._connected = True
        await self._emit(Event(
            event_type=EventType.ibkr_connected,
            source=EventSource.reality_layer,
            message="MockFeed verbunden (Test-Modus)",
        ))
        return True

    async def disconnect(self) -> None:
        self._connected = False
        self.stop_streaming()

    @property
    def is_connected(self) -> bool:
        return self._connected

    async def start_streaming(
        self,
        symbols: List[str],
        interval_sec: float = 5.0,
    ) -> None:
        """
        Startet die Mock-Datengenerierung.
        Emittiert `price_update` Events in `interval_sec`-Abständen.
        """
        self._streaming = True
        # Unbekannte Symbole mit generischen Defaults ergänzen
        for sym in symbols:
            if sym not in self._prices:
                self._prices[sym] = 100.0

        while self._streaming:
            self._tick_counter += 1
            for sym in symbols:
                data = self._next_tick(sym)
                event = Event.price_update(
                    symbol=sym,
                    price=data["price"],
                    change=data["change"],
                    change_percent=data["change_percent"],
                    source="mock",
                )
                event.payload.update({
                    "volume": data["volume"],
                    "bid": data["bid"],
                    "ask": data["ask"],
                    "high": data["high"],
                    "low": data["low"],
                    "tick": self._tick_counter,
                })
                await self._emit(event)
            await asyncio.sleep(interval_sec)

    # ── Interne Logik ──────────────────────────────────────────────────────────

    def _next_tick(self, symbol: str) -> Dict:
        """Berechnet den nächsten simulierten Kurs für ein Symbol."""
        cfg = _MOCK_BASE.get(symbol, {"price": 100.0, "daily_vol": 0.015, "volume_base": 1_000_000})
        base_price = cfg["price"]
        daily_vol = cfg["daily_vol"]
        vol_base = cfg["volume_base"]

        prev_price = self._prices[symbol]

        # Brownsche Bewegung mit leichter Mean-Reversion zum Basis-Kurs
        tick_vol = daily_vol / (252 * 78) ** 0.5  # ~5-min-Äquivalent
        drift = 0.001 * (base_price - prev_price) / base_price  # Mean-Reversion
        shock = random.gauss(drift, tick_vol)
        new_price = round(prev_price * (1 + shock), 4)
        new_price = max(new_price, base_price * 0.5)  # Bodengrenze

        change = round(new_price - prev_price, 4)
        change_pct = round((change / prev_price) * 100, 3) if prev_price else 0.0

        # Simulated Spread (Basis-Punkte abhängig von Liquidität)
        spread_pct = 0.0002 if vol_base > 10_000_000 else 0.0005
        bid = round(new_price * (1 - spread_pct / 2), 4)
        ask = round(new_price * (1 + spread_pct / 2), 4)

        # Simulated OHLC für den Tick
        tick_range = abs(new_price * tick_vol * 2)
        high = round(max(prev_price, new_price) + random.uniform(0, tick_range), 4)
        low = round(min(prev_price, new_price) - random.uniform(0, tick_range), 4)

        # Volumen mit simuliertem Intraday-Rhythmus
        volume = int(random.gauss(vol_base / 78, vol_base / 200))
        volume = max(volume, 1000)

        self._prices[symbol] = new_price
        return {
            "price": new_price,
            "change": change,
            "change_percent": change_pct,
            "bid": bid,
            "ask": ask,
            "high": high,
            "low": low,
            "volume": volume,
        }

    def get_snapshot(self, symbol: str) -> Optional[Dict]:
        """Gibt den aktuellen Mock-Kurs zurück ohne Event zu emittieren."""
        if symbol not in self._prices:
            return None
        return self._next_tick(symbol)
