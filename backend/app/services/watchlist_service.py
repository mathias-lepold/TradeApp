"""Service: WatchlistService — In-Memory + PostgreSQL-Persistenz."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.domain.watchlist import WatchlistItem, WatchlistAdd

_NAMES: Dict[str, str] = {
    "AAPL": "Apple Inc.", "MSFT": "Microsoft Corp.", "NVDA": "NVIDIA Corp.",
    "SPY": "SPDR S&P 500 ETF", "NOVN": "Novartis AG", "ZGLD": "ZKB Gold ETF",
    "AMZN": "Amazon.com", "GOOGL": "Alphabet Inc.", "META": "Meta Platforms",
    "TSLA": "Tesla Inc.", "TSM": "TSMC",
}

_SEED = [("AAPL", "Apple Inc."), ("SPY", "SPDR S&P 500 ETF")]


class WatchlistService:
    def __init__(self) -> None:
        self._items: Dict[str, WatchlistItem] = {}
        for sym, name in _SEED:
            self._items[sym] = WatchlistItem(
                id=str(uuid.uuid4()), symbol=sym, name=name,
                added_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            )

    async def load_from_db(self) -> None:
        try:
            from sqlalchemy import select
            from app.services.database import AsyncSessionLocal
            from app.models.watchlist import WatchlistModel

            async with AsyncSessionLocal() as session:
                rows = (await session.execute(select(WatchlistModel))).scalars().all()

            if rows:
                self._items = {}
                for r in rows:
                    self._items[r.symbol] = WatchlistItem(
                        id=r.id, symbol=r.symbol,
                        name=r.name or _NAMES.get(r.symbol, r.symbol),
                        target_price=float(r.target_price) if r.target_price else None,
                        alert_price=float(r.alert_price) if r.alert_price else None,
                        notes=r.notes or "",
                        added_at=r.added_at,
                    )
                print(f"[WatchlistService] {len(self._items)} Symbole aus DB geladen")
        except Exception as exc:
            print(f"[WatchlistService] DB nicht verfügbar — In-Memory: {exc}")

    def get_all(self) -> List[WatchlistItem]:
        return sorted(self._items.values(), key=lambda x: x.added_at, reverse=True)

    async def add(self, data: WatchlistAdd) -> WatchlistItem:
        sym = data.symbol.upper()
        if sym in self._items:
            return self._items[sym]
        item = WatchlistItem(
            id=str(uuid.uuid4()), symbol=sym,
            name=data.name or _NAMES.get(sym, sym),
            target_price=data.target_price, notes=data.notes,
            added_at=datetime.now(tz=timezone.utc),
        )
        self._items[sym] = item
        await self._persist(item)
        return item

    async def remove(self, symbol: str) -> bool:
        sym = symbol.upper()
        if sym not in self._items:
            return False
        item_id = self._items.pop(sym).id
        await self._delete_from_db(item_id)
        return True

    async def _persist(self, item: WatchlistItem) -> None:
        try:
            from app.services.database import AsyncSessionLocal
            from app.models.watchlist import WatchlistModel
            async with AsyncSessionLocal() as session:
                row = WatchlistModel(
                    id=item.id, symbol=item.symbol, name=item.name,
                    target_price=item.target_price, notes=item.notes or None,
                    added_at=item.added_at,
                )
                session.add(row)
                await session.commit()
        except Exception:
            pass

    async def _delete_from_db(self, item_id: str) -> None:
        try:
            from sqlalchemy import delete
            from app.services.database import AsyncSessionLocal
            from app.models.watchlist import WatchlistModel
            async with AsyncSessionLocal() as session:
                await session.execute(delete(WatchlistModel).where(WatchlistModel.id == item_id))
                await session.commit()
        except Exception:
            pass
