"""
Reality Layer
=============
Verantwortlich für: Rohdaten-Ingestion, Normalisierung und Event-Erzeugung.

Architektur
-----------
                ┌─────────────────────────────────────────┐
                │            Reality Layer                │
                │                                         │
  IBKR TWS ──► │  IBKRFeed  ──►  EventPublisher  ──────► │ ──► Interpretation Layer
  (ib_insync)  │                      │                  │
               │  MockFeed   ─────────┘                  │
               │  (Tests/Dev)                             │
               │                                         │
               │  DataNormalizer  (IBKR-Daten → Domain)  │
               └─────────────────────────────────────────┘

Komponenten
-----------
MarketFeed      abstrakte Basis-Klasse; definiert das Feed-Interface + Event-Bus
IBKRFeed        konkrete Implementierung via ib_insync (Real-Time + Hist. Fallback)
MockFeed        Test-Implementierung mit realistischer Brownsche-Bewegung-Simulation
EventPublisher  konvertiert Feed-Events → QuoteEvents, leitet sie Downstream weiter
DataNormalizer  wandelt IBKR-Rohdaten (Bars, Ticks) in Domain-Objekte um

Schnelleinstieg
---------------
    # Produktion
    from app.layers.reality import IBKRFeed, EventPublisher

    feed = IBKRFeed()
    publisher = EventPublisher(feed)
    publisher.add_downstream(my_interpretation_handler)
    await feed.connect()
    await publisher.start(["NVDA", "MSFT", "AAPL", "SPY"])

    # Tests / Entwicklung
    from app.layers.reality import MockFeed, EventPublisher

    feed = MockFeed(seed=42)
    publisher = EventPublisher(feed)
    publisher.add_downstream(my_handler)
    await feed.connect()
    await publisher.start(["AAPL", "MSFT", "NVDA", "SPY"], interval_sec=1.0)
"""
from .market_feed    import MarketFeed, MockFeed
from .ibkr_feed      import IBKRFeed
from .yahoo_feed     import YahooFeed
from .feed_manager   import FeedManager
from .event_publisher import EventPublisher, QuoteEvent
from .normalizer     import DataNormalizer

__all__ = [
    "MarketFeed",
    "MockFeed",
    "IBKRFeed",
    "YahooFeed",
    "FeedManager",
    "EventPublisher",
    "QuoteEvent",
    "DataNormalizer",
]
