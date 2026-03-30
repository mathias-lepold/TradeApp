"""
Reality Layer: IBKRFeed
-----------------------
Echtzeit-Marktdaten via Interactive Brokers TWS / IB Gateway.

Verbindung:
  - Host:      127.0.0.1  (oder IBKR_HOST env)
  - Port:      7497        (TWS Paper/Live)  oder 4002 (IB Gateway Paper)
  - Client-ID: 1           (oder IBKR_CLIENT_ID env)

Daten-Strategie:
  - reqMktData → Streaming-Ticks (bid/ask/last/volume) — benötigt Market-Data-Abo
  - reqHistoricalData → Fallback-Kurs wenn kein Abo aktiv (immer kostenlos)

Reconnect:
  - Exponentielles Backoff: 2s → 4s → 8s → max. 60s
  - Re-Subscription nach erfolgreicher Reconnection
"""
from __future__ import annotations

import asyncio
import os
from typing import Callable, Dict, List, Optional, Set
from datetime import datetime

from ib_insync import IB, Stock, Contract, Ticker

from app.domain.event import Event, EventType, EventSource, EventSeverity
from app.layers.reality.market_feed import MarketFeed
from app.layers.reality.normalizer import DataNormalizer, KNOWN_ASSETS


# ── Konstanten ─────────────────────────────────────────────────────────────────

_RECONNECT_BASE_DELAY = 2.0      # Sekunden bis zur ersten Retry
_RECONNECT_MAX_DELAY  = 60.0     # Maximale Wartezeit
_RECONNECT_MAX_TRIES  = 10       # 0 = unbegrenzt
_HIST_DURATION        = "1 D"    # reqHistoricalData Zeitraum
_HIST_BAR_SIZE        = "5 mins" # reqHistoricalData Bar-Größe


# ── IBKRFeed ───────────────────────────────────────────────────────────────────

class IBKRFeed(MarketFeed):
    """
    MarketFeed-Implementierung für Interactive Brokers TWS / IB Gateway.

    Funktionen:
      - Async-Verbindung mit connectAsync
      - Real-time Streaming via reqMktData (Tick-Daten)
      - Historischer Fallback via reqHistoricalData
      - Automatischer Reconnect mit exponentiellem Backoff
      - Re-Subscription aller Symbole nach Reconnect

    Verwendung:
        feed = IBKRFeed()
        feed.subscribe(EventType.price_update, handler)
        await feed.connect()
        await feed.start_streaming(["NVDA", "MSFT", "AAPL", "SPY"])
    """

    def __init__(self) -> None:
        super().__init__()
        self._ib = IB()
        self._host      = os.getenv("IBKR_HOST",      "127.0.0.1")
        self._port      = int(os.getenv("IBKR_PORT",  "7497"))
        self._client_id = int(os.getenv("IBKR_CLIENT_ID", "1"))

        # Aktive Subscriptions symbol → Ticker
        self._tickers:   Dict[str, Ticker]   = {}
        self._contracts: Dict[str, Contract] = {}
        self._subscribed_symbols: Set[str]   = set()

        # Reconnect-State
        self._reconnect_task:  Optional[asyncio.Task] = None
        self._reconnect_delay  = _RECONNECT_BASE_DELAY
        self._reconnect_count  = 0

        # ib_insync Event-Hooks
        self._ib.disconnectedEvent += self._on_ibkr_disconnected
        self._ib.errorEvent        += self._on_ibkr_error

    # ── Verbindung ─────────────────────────────────────────────────────────────

    async def connect(self) -> bool:
        """
        Verbindet mit IBKR TWS / IB Gateway (async).
        Gibt True zurück wenn die Verbindung erfolgreich war.
        """
        try:
            await self._ib.connectAsync(
                self._host,
                self._port,
                clientId=self._client_id,
                timeout=15,
            )
            self._reconnect_delay = _RECONNECT_BASE_DELAY
            self._reconnect_count = 0

            await self._emit(Event(
                event_type=EventType.ibkr_connected,
                source=EventSource.reality_layer,
                message=f"IBKR verbunden: {self._host}:{self._port} (clientId={self._client_id})",
                payload={"host": self._host, "port": self._port, "client_id": self._client_id},
            ))
            return True

        except Exception as exc:
            await self._emit(Event(
                event_type=EventType.system_error,
                source=EventSource.reality_layer,
                severity=EventSeverity.critical,
                message=f"IBKR Verbindung fehlgeschlagen: {exc}",
                payload={"error": str(exc), "host": self._host, "port": self._port},
            ))
            return False

    async def disconnect(self) -> None:
        """Beendet alle Subscriptions und trennt die Verbindung."""
        self.stop_streaming()
        self._cancel_subscriptions()
        if self._reconnect_task and not self._reconnect_task.done():
            self._reconnect_task.cancel()
        if self._ib.isConnected():
            self._ib.disconnect()

    @property
    def is_connected(self) -> bool:
        return self._ib.isConnected()

    # ── Streaming ──────────────────────────────────────────────────────────────

    async def start_streaming(
        self,
        symbols: List[str],
        interval_sec: float = 30.0,
    ) -> None:
        """
        Startet Real-time Streaming für die angegebenen Symbole.

        Strategie:
          1. Versucht reqMktData für Live-Ticks (benötigt Market-Data-Abo).
          2. Fällt auf reqHistoricalData-Polling zurück wenn reqMktData
             kein Ergebnis liefert (z.B. kein Abo, außerhalb Handelszeiten).

        Emittiert `price_update` Events über den Event-Bus.
        """
        self._streaming = True
        self._subscribed_symbols = set(symbols)

        # Alle Symbole qualifizieren und Live-Subscriptions starten
        await self._subscribe_symbols(symbols)

        # Polling-Loop als Fallback / für historische Kurse außerhalb RTH
        while self._streaming:
            if not self._ib.isConnected():
                await asyncio.sleep(5)
                continue

            for sym in list(self._subscribed_symbols):
                await self._poll_historical(sym)

            await asyncio.sleep(interval_sec)

    def stop_streaming(self) -> None:
        super().stop_streaming()
        self._cancel_subscriptions()

    # ── Interne Subscription-Verwaltung ───────────────────────────────────────

    async def _subscribe_symbols(self, symbols: List[str]) -> None:
        """Qualifiziert Contracts und startet reqMktData-Subscriptions."""
        for sym in symbols:
            if not self._ib.isConnected():
                break
            contract = await self._qualify_contract(sym)
            if contract is None:
                continue
            self._contracts[sym] = contract
            self._start_ticker(sym, contract)

    def _start_ticker(self, symbol: str, contract: Contract) -> None:
        """Abonniert Live-Ticks für einen Contract und registriert den Update-Hook."""
        if symbol in self._tickers:
            return  # bereits abonniert
        ticker = self._ib.reqMktData(contract, "", False, False)
        ticker.updateEvent += self._make_tick_handler(symbol)
        self._tickers[symbol] = ticker

    def _make_tick_handler(self, symbol: str) -> Callable:
        """Erstellt einen Tick-Handler der Ticker-Updates in Events umwandelt."""
        def handler(ticker: Ticker) -> None:
            price = ticker.last or ticker.close or ticker.bid
            if not price or price != price:  # NaN-Guard
                return
            prev_close = ticker.close or price
            change = round(price - prev_close, 4)
            change_pct = round((change / prev_close) * 100, 3) if prev_close else 0.0
            volume = int(ticker.volume) if ticker.volume and ticker.volume == ticker.volume else 0

            event = Event.price_update(
                symbol=symbol,
                price=price,
                change=change,
                change_percent=change_pct,
                source="ibkr_realtime",
            )
            event.payload.update({
                "bid":    ticker.bid,
                "ask":    ticker.ask,
                "volume": volume,
                "high":   ticker.high,
                "low":    ticker.low,
            })
            asyncio.ensure_future(self._emit(event))

        return handler

    def _cancel_subscriptions(self) -> None:
        """Beendet alle laufenden reqMktData-Subscriptions."""
        for sym, ticker in list(self._tickers.items()):
            try:
                self._ib.cancelMktData(ticker.contract)
            except Exception:
                pass
        self._tickers.clear()

    # ── Historischer Fallback ──────────────────────────────────────────────────

    async def _poll_historical(self, symbol: str) -> None:
        """
        Holt den letzten Kurs via reqHistoricalDataAsync.
        Wird als Fallback genutzt wenn reqMktData keine Daten liefert.
        """
        contract = self._contracts.get(symbol)
        if contract is None:
            contract = await self._qualify_contract(symbol)
            if contract is None:
                return
            self._contracts[symbol] = contract

        try:
            bars = await asyncio.wait_for(
                self._ib.reqHistoricalDataAsync(
                    contract,
                    endDateTime="",
                    durationStr=_HIST_DURATION,
                    barSizeSetting=_HIST_BAR_SIZE,
                    whatToShow="TRADES",
                    useRTH=True,
                    timeout=10,
                ),
                timeout=15,
            )
        except (asyncio.TimeoutError, Exception) as exc:
            await self._emit(Event(
                event_type=EventType.system_warning,
                source=EventSource.reality_layer,
                asset_symbol=symbol,
                message=f"reqHistoricalData Timeout/Fehler für {symbol}: {exc}",
            ))
            return

        if not bars:
            return

        data = DataNormalizer.ibkr_bar_to_price_dict(bars, symbol)
        data["source"] = "ibkr_historical"

        # Nur emittieren wenn reqMktData keinen aktuellen Live-Kurs liefert
        ticker = self._tickers.get(symbol)
        live_price = ticker.last if ticker else None
        if live_price and live_price == live_price:  # NaN-Guard: NaN != NaN
            return  # Live-Daten vorhanden → kein Fallback nötig

        event = DataNormalizer.price_dict_to_event(data)
        event.payload["source"] = "ibkr_historical"
        await self._emit(event)

    async def _qualify_contract(self, symbol: str) -> Optional[Contract]:
        """Qualifiziert einen IBKR-Contract für das gegebene Symbol."""
        cfg = KNOWN_ASSETS.get(symbol.upper(), {
            "exchange": "SMART",
            "currency": "USD",
        })
        try:
            contract = Stock(symbol.upper(), cfg["exchange"], cfg["currency"])
            qualified = await asyncio.wait_for(
                self._ib.qualifyContractsAsync(contract),
                timeout=10,
            )
            if qualified:
                return qualified[0]
        except Exception as exc:
            await self._emit(Event(
                event_type=EventType.system_warning,
                source=EventSource.reality_layer,
                asset_symbol=symbol,
                message=f"Contract-Qualifizierung fehlgeschlagen für {symbol}: {exc}",
            ))
        return None

    # ── IBKR Event-Hooks ───────────────────────────────────────────────────────

    def _on_ibkr_disconnected(self) -> None:
        """Wird von ib_insync aufgerufen wenn die Verbindung getrennt wird."""
        asyncio.ensure_future(self._handle_disconnect())

    async def _handle_disconnect(self) -> None:
        """Emittiert disconnect-Event und startet Reconnect-Loop."""
        await self._emit(Event(
            event_type=EventType.ibkr_disconnected,
            source=EventSource.reality_layer,
            severity=EventSeverity.warning,
            message=f"IBKR Verbindung getrennt — Reconnect in {self._reconnect_delay:.0f}s",
        ))
        self._tickers.clear()  # alte Ticker-Referenzen ungültig

        if _RECONNECT_MAX_TRIES == 0 or self._reconnect_count < _RECONNECT_MAX_TRIES:
            if self._reconnect_task is None or self._reconnect_task.done():
                self._reconnect_task = asyncio.ensure_future(self._reconnect_loop())

    async def _reconnect_loop(self) -> None:
        """
        Reconnect-Schleife mit exponentiellem Backoff.
        Nach erfolgreicher Reconnection werden alle Symbole neu abonniert.
        """
        while not self._ib.isConnected():
            self._reconnect_count += 1

            await self._emit(Event(
                event_type=EventType.system_warning,
                source=EventSource.reality_layer,
                message=(
                    f"IBKR Reconnect-Versuch {self._reconnect_count} "
                    f"in {self._reconnect_delay:.0f}s..."
                ),
                payload={"attempt": self._reconnect_count, "delay": self._reconnect_delay},
            ))

            await asyncio.sleep(self._reconnect_delay)

            # Backoff erhöhen (max. _RECONNECT_MAX_DELAY)
            self._reconnect_delay = min(
                self._reconnect_delay * 2,
                _RECONNECT_MAX_DELAY,
            )

            success = await self.connect()
            if success:
                # Alle vorherigen Subscriptions wiederherstellen
                if self._subscribed_symbols:
                    await self._subscribe_symbols(list(self._subscribed_symbols))
                    await self._emit(Event(
                        event_type=EventType.ibkr_connected,
                        source=EventSource.reality_layer,
                        message=f"IBKR Reconnect erfolgreich nach {self._reconnect_count} Versuch(en)",
                        payload={
                            "attempt": self._reconnect_count,
                            "resubscribed": list(self._subscribed_symbols),
                        },
                    ))
                self._reconnect_delay = _RECONNECT_BASE_DELAY
                return

            if _RECONNECT_MAX_TRIES > 0 and self._reconnect_count >= _RECONNECT_MAX_TRIES:
                await self._emit(Event(
                    event_type=EventType.system_error,
                    source=EventSource.reality_layer,
                    severity=EventSeverity.critical,
                    message=f"IBKR Reconnect nach {self._reconnect_count} Versuchen aufgegeben",
                ))
                return

    # ── Health-Check Probe ─────────────────────────────────────────────────────

    @classmethod
    async def probe_connection(
        cls,
        host: str = "127.0.0.1",
        port: int = 7497,
        timeout: float = 3.0,
    ) -> bool:
        """
        Leichtgewichtiger TCP-Probe: prüft ob TWS auf host:port erreichbar ist.

        Öffnet eine Socket-Verbindung ohne den vollen IBKR-Handshake zu
        starten — geeignet für /health ohne Seiteneffekte auf eine laufende
        IBKRFeed-Instanz.

        Gibt True zurück wenn der Port offen ist (TWS läuft),
        False wenn kein Dienst antwortet oder der Timeout überschritten wird.
        """
        try:
            _, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=timeout,
            )
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
            return True
        except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
            return False

    def _on_ibkr_error(
        self,
        req_id: int,
        error_code: int,
        error_string: str,
        contract: Optional[Contract],
    ) -> None:
        """
        Verarbeitet IBKR API-Fehlermeldungen.
        Codes < 2000 sind Informationsmeldungen, keine echten Fehler.
        """
        if error_code < 2000:
            return  # nur Info/Warn, kein Fehler

        sym = contract.symbol if contract else "unknown"
        severity = (
            EventSeverity.critical if error_code >= 500
            else EventSeverity.warning
        )
        asyncio.ensure_future(self._emit(Event(
            event_type=EventType.system_error,
            source=EventSource.ibkr,
            severity=severity,
            asset_symbol=sym if sym != "unknown" else None,
            message=f"IBKR Error {error_code}: {error_string}",
            payload={"req_id": req_id, "error_code": error_code, "symbol": sym},
        )))
