"""
Reality Layer Test: MockFeed
Testet async Verbindung, Preishistorie, Event-Bus und Streaming.
"""
import asyncio
import pytest
from app.domain.event import Event, EventType
from app.layers.reality.market_feed import MockFeed


# ── Verbindung ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_connect_returns_true():
    feed = MockFeed(seed=42)
    result = await feed.connect()
    assert result is True
    assert feed.is_connected


@pytest.mark.asyncio
async def test_disconnect_sets_not_connected():
    feed = MockFeed(seed=42)
    await feed.connect()
    await feed.disconnect()
    assert not feed.is_connected


# ── Preishistorie ─────────────────────────────────────────────────────────────

def test_get_snapshot_returns_price_dict():
    feed = MockFeed(seed=42)
    snap = feed.get_snapshot("NVDA")
    assert snap is not None
    assert "price" in snap
    assert snap["price"] > 0


def test_snapshot_prices_vary_across_calls():
    """MockFeed soll Brownsche Bewegung simulieren → Preise ändern sich."""
    feed = MockFeed(seed=99)
    prices = [feed.get_snapshot("MSFT")["price"] for _ in range(10)]
    assert len(set(prices)) > 1, "Alle Preise identisch — kein Rauschen"


def test_snapshot_bid_less_than_ask():
    feed = MockFeed(seed=42)
    snap = feed.get_snapshot("AAPL")
    assert snap["bid"] < snap["ask"]


def test_unknown_symbol_returns_none():
    """Unbekanntes Symbol ohne vorgängiges start_streaming → None."""
    feed = MockFeed(seed=42)
    snap = feed.get_snapshot("UNKNOWN_SYM")
    assert snap is None


# ── Event-Bus ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_price_update_event_emitted():
    """MockFeed soll price_update Events emittieren."""
    feed   = MockFeed(seed=42)
    events: list[Event] = []

    async def capture(event: Event):
        events.append(event)

    feed.subscribe(EventType.price_update, capture)
    await feed.connect()

    # Einen einzigen Streaming-Zyklus ausführen
    task = asyncio.create_task(
        feed.start_streaming(["NVDA", "MSFT"], interval_sec=0.05)
    )
    await asyncio.sleep(0.15)
    feed.stop_streaming()
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

    assert len(events) >= 2, f"Erwartet mind. 2 Events, bekommen {len(events)}"
    symbols = {e.asset_symbol for e in events}
    assert "NVDA" in symbols
    assert "MSFT" in symbols


@pytest.mark.asyncio
async def test_ibkr_connected_event_on_connect():
    """connect() soll ibkr_connected Event emittieren."""
    feed   = MockFeed(seed=42)
    events: list[Event] = []

    async def capture(event: Event):
        events.append(event)

    feed.subscribe(EventType.ibkr_connected, capture)
    await feed.connect()

    assert any(e.event_type == "ibkr_connected" for e in events)


# ── Stop-Streaming ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_stop_streaming_halts_feed():
    feed   = MockFeed(seed=42)
    count  = 0

    async def counter(e: Event):
        nonlocal count
        count += 1

    feed.subscribe(EventType.price_update, counter)
    await feed.connect()

    task = asyncio.create_task(
        feed.start_streaming(["AAPL"], interval_sec=0.05)
    )
    await asyncio.sleep(0.12)
    feed.stop_streaming()
    count_after_stop = count
    await asyncio.sleep(0.12)

    assert count_after_stop > 0
    # Nach stop_streaming dürfen keine neuen Events kommen
    assert count == count_after_stop or count <= count_after_stop + 1

    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
