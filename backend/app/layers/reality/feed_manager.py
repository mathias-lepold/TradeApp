"""
Reality Layer: FeedManager
--------------------------
Wählt automatisch zwischen YahooFeed und MockFeed.

Auswahllogik (Priorität):
  1. Umgebungsvariable FEED_MODE=mock  → immer MockFeed
  2. Umgebungsvariable FEED_MODE=yahoo → YahooFeed versuchen, MockFeed als Fallback
  3. Standard (kein FEED_MODE)         → YahooFeed versuchen, MockFeed als Fallback

Verwendung in main.py:
    feed, feed_mode = await FeedManager.create()
    # feed ist eine MarketFeed-Instanz (YahooFeed oder MockFeed)
    # feed_mode ist "yahoo" oder "mock"
"""
from __future__ import annotations

import os
from typing import Tuple

from app.layers.reality.market_feed import MarketFeed, MockFeed
from app.layers.reality.yahoo_feed import YahooFeed


class FeedManager:
    """
    Factory für MarketFeed-Instanzen.

    Liest FEED_MODE aus der Umgebung und erstellt den passenden Feed.
    Fällt bei Yahoo-Fehler automatisch auf MockFeed zurück.
    """

    @staticmethod
    async def create(seed: int | None = None) -> Tuple[MarketFeed, str]:
        """
        Erstellt und verbindet den passenden Feed.

        Returns:
            (feed, feed_mode) — feed_mode ist "yahoo" oder "mock"
        """
        feed_mode_env = os.getenv("FEED_MODE", "yahoo").lower().strip()

        if feed_mode_env == "mock":
            print("[FeedManager] FEED_MODE=mock — starte MockFeed")
            return await FeedManager._create_mock(seed), "mock"

        # Yahoo versuchen
        print("[FeedManager] Versuche YahooFeed zu verbinden…")
        yahoo = YahooFeed()
        connected = await yahoo.connect()

        if connected:
            print("[FeedManager] YahooFeed aktiv — Yahoo Finance Daten")
            return yahoo, "yahoo"

        # Fallback
        print("[FeedManager] YahooFeed fehlgeschlagen — Fallback auf MockFeed")
        return await FeedManager._create_mock(seed), "mock"

    @staticmethod
    async def _create_mock(seed: int | None = None) -> MockFeed:
        feed = MockFeed(seed=seed)
        await feed.connect()
        return feed
