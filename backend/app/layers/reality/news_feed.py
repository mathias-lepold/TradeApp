"""
Reality Layer: NewsFeed
-----------------------
Echte Nachrichten via yfinance.Ticker.news mit MockNews-Fallback.
Cached 15 Minuten pro Symbol um Rate-Limits zu vermeiden.
"""
from __future__ import annotations

import asyncio
import random
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel

# ── Sentiment-Keywords ────────────────────────────────────────────────────────

_BULLISH = {"upgrade", "buy", "surge", "beat", "strong", "growth", "gain",
            "record", "outperform", "positive", "rally", "soar", "rise",
            "bullish", "profit", "win", "top", "above", "exceed"}
_BEARISH = {"downgrade", "sell", "drop", "miss", "weak", "loss", "decline",
            "cut", "bearish", "slump", "fall", "below", "disappoint",
            "concern", "risk", "warn", "crash", "plunge", "layoff"}


def _detect_sentiment(text: str) -> str:
    words = set(text.lower().split())
    bull = len(words & _BULLISH)
    bear = len(words & _BEARISH)
    if bull > bear:
        return "bullish"
    if bear > bull:
        return "bearish"
    return "neutral"


# ── Domain Model ──────────────────────────────────────────────────────────────

class NewsItem(BaseModel):
    id:           str
    title:        str
    summary:      str
    symbol:       str
    source:       str
    url:          str
    published_at: str   # ISO string
    sentiment:    str   # bullish | bearish | neutral
    is_mock:      bool = False


# ── Mock-News-Generator ───────────────────────────────────────────────────────

_MOCK_TEMPLATES = [
    ("{sym} meldet starke Quartalsergebnisse — Umsatz übertrifft Erwartungen",
     "{sym} übertraff im letzten Quartal die Analystenerwartungen mit einem Umsatzwachstum von 12%. "
     "CEO betont starke Nachfrage in allen Segmenten.", "bullish"),
    ("{sym} kündigt Aktienrückkaufprogramm im Wert von 5 Mrd. USD an",
     "Das Board genehmigte ein neues Aktienrückkaufprogramm. Analysten sehen dies als "
     "Signal für überschüssige Cash-Reserven.", "bullish"),
    ("Analyst hebt Kursziel für {sym} auf 520 USD an",
     "Nach starken Betriebskennzahlen heben Analysten von Goldman Sachs das Kursziel an "
     "und bestätigen die Kaufempfehlung.", "bullish"),
    ("{sym} unter Druck nach schwachem Ausblick",
     "{sym} enttäuschte mit einem vorsichtigen Ausblick für das nächste Quartal. "
     "Kostendruck und nachlassende Nachfrage belasten die Margen.", "bearish"),
    ("Neue Partnerschaft: {sym} kooperiert mit Microsoft Azure",
     "{sym} gab eine strategische Partnerschaft bekannt, die Cloud-Dienste und "
     "KI-Integration umfasst. Langfristiges Wachstumspotential erwartet.", "bullish"),
    ("{sym} im Fokus: Technische Analyse zeigt Ausbruch aus Konsolidierung",
     "Charttechnisch deutet {sym} auf einen möglichen Ausbruch hin. RSI nahe 60, "
     "Volumen steigt an. Widerstand bei aktuellem Allzeithoch.", "neutral"),
    ("Makrorisiken belasten {sym} — Fed-Zinspolitik im Fokus",
     "Anhaltende Unsicherheit über den Fed-Kurs belastet Wachstumswerte wie {sym}. "
     "Höhere Zinsen drücken die Bewertungsmultiplikatoren.", "bearish"),
    ("{sym} erhöht Dividende um 8% — Aktionäre profitieren",
     "Das Management hob die Quartalsdividende um 8% an, was das Vertrauen in "
     "nachhaltige Cashflows widerspiegelt.", "bullish"),
]

_SOURCES = ["Reuters", "Bloomberg", "Financial Times", "CNBC", "MarketWatch", "Seeking Alpha"]


def _generate_mock_news(symbol: str, count: int = 5) -> List[NewsItem]:
    rng = random.Random(hash(symbol) + int(datetime.utcnow().timestamp() // 3600))
    items = []
    templates = rng.sample(_MOCK_TEMPLATES, min(count, len(_MOCK_TEMPLATES)))
    for i, (title_tpl, summary_tpl, sentiment) in enumerate(templates):
        title   = title_tpl.format(sym=symbol)
        summary = summary_tpl.format(sym=symbol)
        pub_at  = datetime.now(tz=timezone.utc) - timedelta(hours=i * 4 + rng.randint(0, 3))
        items.append(NewsItem(
            id=f"mock_{symbol}_{i}",
            title=title, summary=summary, symbol=symbol,
            source=rng.choice(_SOURCES),
            url=f"https://example.com/news/{symbol.lower()}-{i}",
            published_at=pub_at.isoformat(),
            sentiment=sentiment,
            is_mock=True,
        ))
    return items


# ── NewsFeed ──────────────────────────────────────────────────────────────────

class NewsFeed:
    """
    Lädt Nachrichten via yfinance (15-Min-Cache) mit MockNews-Fallback.
    """

    CACHE_TTL = 900  # 15 Minuten

    def __init__(self) -> None:
        # symbol → (items, fetched_at)
        self._cache: Dict[str, Tuple[List[NewsItem], datetime]] = {}

    async def get_news(self, symbol: str, limit: int = 5) -> List[NewsItem]:
        """Nachrichten für ein Symbol (Cache → Yahoo → Mock)."""
        sym = symbol.upper()

        # Cache-Hit?
        if sym in self._cache:
            items, fetched = self._cache[sym]
            age = (datetime.now(tz=timezone.utc) - fetched).total_seconds()
            if age < self.CACHE_TTL:
                return items[:limit]

        items = await self._fetch_yahoo(sym, limit)
        if not items:
            items = _generate_mock_news(sym, limit)

        self._cache[sym] = (items, datetime.now(tz=timezone.utc))
        return items[:limit]

    async def get_all_news(self, symbols: List[str], limit_per: int = 3) -> List[NewsItem]:
        """Nachrichten für mehrere Symbole — zusammengeführt und nach Datum sortiert."""
        results: List[NewsItem] = []
        for sym in symbols:
            items = await self.get_news(sym, limit=limit_per)
            results.extend(items)
        return sorted(results, key=lambda x: x.published_at, reverse=True)

    async def _fetch_yahoo(self, symbol: str, limit: int) -> List[NewsItem]:
        try:
            import yfinance as yf

            # Swiss symbols
            yahoo_sym = {"NOVN": "NOVN.SW", "ZGLD": "ZGLD.SW"}.get(symbol, symbol)

            loop = asyncio.get_event_loop()
            news_raw = await loop.run_in_executor(
                None, lambda: yf.Ticker(yahoo_sym).news
            )

            if not news_raw:
                return []

            items: List[NewsItem] = []
            for i, n in enumerate(news_raw[:limit]):
                title   = n.get("title", "")
                summary = n.get("summary", n.get("description", title))
                url     = n.get("link", n.get("url", ""))
                source  = n.get("publisher", n.get("source", "Yahoo Finance"))
                ts      = n.get("providerPublishTime", n.get("published", 0))

                if isinstance(ts, (int, float)) and ts > 0:
                    pub_at = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
                else:
                    pub_at = datetime.now(tz=timezone.utc).isoformat()

                items.append(NewsItem(
                    id=n.get("uuid", f"yf_{symbol}_{i}"),
                    title=title, summary=summary or title,
                    symbol=symbol, source=source, url=url,
                    published_at=pub_at,
                    sentiment=_detect_sentiment(f"{title} {summary}"),
                    is_mock=False,
                ))
            return items

        except Exception as exc:
            print(f"[NewsFeed] Yahoo-Fehler für {symbol}: {exc}")
            return []
