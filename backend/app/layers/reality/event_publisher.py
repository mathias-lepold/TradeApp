"""
Reality Layer: EventPublisher
------------------------------
Bindeglied zwischen MarketFeed (Reality Layer) und dem Interpretation Layer.

Aufgaben:
  1. Abonniert Events vom MarketFeed (price_update, ibkr_connected, …)
  2. Konvertiert rohe Feed-Daten in typisierte interne Event-Objekte
  3. Reichert Events mit Asset-Metadaten (Name, Sektor, Währung) an
  4. Leitet Events an registrierte Downstream-Handler weiter
     (z.B. SignalGenerator, RegimeDetector, WebSocket-Broadcaster)

Schema der publizierten Objekte: app.domain.event.Event (Pydantic)

Verwendung:
    feed = IBKRFeed()
    publisher = EventPublisher(feed)
    publisher.add_downstream(my_async_handler)
    await feed.connect()
    await publisher.start(["NVDA", "MSFT", "AAPL", "SPY"])
"""
from __future__ import annotations

import asyncio
from typing import Callable, Awaitable, Dict, List, Optional, Any
from datetime import datetime

from app.domain.event import Event, EventType, EventSource, EventSeverity
from app.domain.asset import Asset
from app.layers.reality.market_feed import MarketFeed, EventHandler
from app.layers.reality.normalizer import DataNormalizer, KNOWN_ASSETS


# ── Typen ──────────────────────────────────────────────────────────────────────

DownstreamHandler = Callable[[Event], Awaitable[None]]


# ── Internes Quote-Schema ──────────────────────────────────────────────────────

from pydantic import BaseModel, Field


class QuoteEvent(BaseModel):
    """
    Angereichertes Kurs-Ereignis — das kanonische Objekt das den Reality Layer verlässt.

    Enthält alle Felder eines price_update Events plus aufgelöste Asset-Metadaten.
    Wird vom EventPublisher erzeugt und an den Interpretation Layer weitergegeben.
    """
    # Identität
    event_id:    str   = Field(..., description="UUID des Basis-Events")
    symbol:      str
    asset_name:  str
    currency:    str
    exchange:    str
    sector:      Optional[str] = None

    # Preis
    price:          float
    change:         float
    change_percent: float
    bid:            Optional[float] = None
    ask:            Optional[float] = None
    high:           Optional[float] = None
    low:            Optional[float] = None
    volume:         Optional[int]   = None

    # Herkunft
    data_source: str = "unknown"     # ibkr_realtime | ibkr_historical | mock
    occurred_at: datetime

    @classmethod
    def from_event(cls, event: Event, asset: Asset) -> "QuoteEvent":
        """Erstellt ein QuoteEvent aus einem price_update Event + Asset."""
        p = event.payload
        return cls(
            event_id        = event.id,
            symbol          = event.asset_symbol or asset.symbol,
            asset_name      = asset.name,
            currency        = asset.currency,
            exchange        = asset.exchange,
            sector          = asset.sector,
            price           = p["price"],
            change          = p["change"],
            change_percent  = p["change_percent"],
            bid             = p.get("bid"),
            ask             = p.get("ask"),
            high            = p.get("high"),
            low             = p.get("low"),
            volume          = p.get("volume"),
            data_source     = p.get("data_source", p.get("source", "unknown")),
            occurred_at     = event.occurred_at,
        )


# ── EventPublisher ─────────────────────────────────────────────────────────────

class EventPublisher:
    """
    Konvertiert Feed-Rohdaten in typisierte QuoteEvents und verteilt sie
    an alle registrierten Downstream-Handler.

    Downstream-Handler können sein:
      - SignalGenerator (Interpretation Layer)
      - RegimeDetector  (Interpretation Layer)
      - WebSocket-Broadcaster (API Layer)
      - Datenbank-Writer (Persistence Layer)
      - Logger / Audit-Trail

    Alle Handler erhalten das originale `Event`-Objekt (mit QuoteEvent im
    `payload["quote"]` Schlüssel) — kein separates Protokoll notwendig.
    """

    def __init__(self, feed: MarketFeed) -> None:
        self._feed = feed
        self._downstream: List[DownstreamHandler] = []
        self._asset_cache: Dict[str, Asset] = {}
        self._stats: Dict[str, int] = {
            "published": 0,
            "errors":    0,
            "skipped":   0,
        }

        # Feed-Events abonnieren
        self._feed.subscribe(EventType.price_update,       self._on_price_update)
        self._feed.subscribe(EventType.ibkr_connected,     self._on_passthrough)
        self._feed.subscribe(EventType.ibkr_disconnected,  self._on_passthrough)
        self._feed.subscribe(EventType.system_error,       self._on_passthrough)
        self._feed.subscribe(EventType.system_warning,     self._on_passthrough)

    # ── Public API ─────────────────────────────────────────────────────────────

    def add_downstream(self, handler: DownstreamHandler) -> None:
        """Registriert einen Downstream-Handler für alle publizierten Events."""
        if handler not in self._downstream:
            self._downstream.append(handler)

    def remove_downstream(self, handler: DownstreamHandler) -> None:
        if handler in self._downstream:
            self._downstream.remove(handler)

    async def start(
        self,
        symbols: List[str],
        interval_sec: float = 30.0,
    ) -> None:
        """
        Startet den Feed-Stream für die angegebenen Symbole.
        Blockiert bis `stop()` aufgerufen wird.
        """
        await self._feed.start_streaming(symbols, interval_sec)

    def stop(self) -> None:
        """Stoppt den Feed-Stream."""
        self._feed.stop_streaming()

    @property
    def stats(self) -> Dict[str, int]:
        """Laufende Statistik: publizierte / fehlerhafte / übersprungene Events."""
        return dict(self._stats)

    # ── Handler ────────────────────────────────────────────────────────────────

    async def _on_price_update(self, event: Event) -> None:
        """
        Verarbeitet ein price_update Event vom Feed:
          1. Asset-Metadaten auflösen (mit Cache)
          2. QuoteEvent konstruieren
          3. Event mit QuoteEvent anreichern
          4. An alle Downstream-Handler weiterleiten
        """
        symbol = event.asset_symbol
        if not symbol:
            self._stats["skipped"] += 1
            return

        try:
            asset = self._resolve_asset(symbol)
            quote = QuoteEvent.from_event(event, asset)

            # Originales Event mit aufgelöstem QuoteEvent anreichern
            enriched = event.model_copy(deep=True)
            enriched.payload["quote"] = quote.model_dump()
            enriched.payload["asset"] = {
                "name":     asset.name,
                "currency": asset.currency,
                "exchange": asset.exchange,
                "sector":   asset.sector,
            }

            await self._publish(enriched)
            self._stats["published"] += 1

        except Exception as exc:
            self._stats["errors"] += 1
            print(f"[EventPublisher] Fehler bei {symbol}: {exc}")

    async def _on_passthrough(self, event: Event) -> None:
        """Leitet System-Events (connect/disconnect/error) direkt weiter."""
        await self._publish(event)

    async def _publish(self, event: Event) -> None:
        """Verteilt ein Event an alle registrierten Downstream-Handler."""
        for handler in list(self._downstream):
            try:
                await handler(event)
            except Exception as exc:
                self._stats["errors"] += 1
                print(f"[EventPublisher] Downstream-Handler Fehler: {exc}")

    # ── Asset-Auflösung ────────────────────────────────────────────────────────

    def _resolve_asset(self, symbol: str) -> Asset:
        """
        Gibt ein Asset-Objekt für das Symbol zurück.
        Nutzt einen In-Memory-Cache — Lookup kostet O(1) nach erstem Aufruf.
        """
        sym = symbol.upper()
        if sym not in self._asset_cache:
            self._asset_cache[sym] = DataNormalizer.symbol_to_asset(sym)
        return self._asset_cache[sym]

    # ── Diagnose ───────────────────────────────────────────────────────────────

    def status(self) -> Dict[str, Any]:
        """Gibt einen Statusbericht des Publishers zurück."""
        return {
            "feed_connected":     self._feed.is_connected,
            "feed_type":          type(self._feed).__name__,
            "downstream_count":   len(self._downstream),
            "cached_assets":      list(self._asset_cache.keys()),
            "stats":              self._stats,
            "checked_at":         datetime.utcnow().isoformat(),
        }
