"""
Service: PortfolioService
--------------------------
Portfolio-Verwaltung mit PostgreSQL-Persistenz und In-Memory-Fallback.

Architektur:
- Primär: In-Memory (immer verfügbar, auch ohne DB)
- Optional: PostgreSQL-Persistenz (wird beim Start versucht)
- Seed: Echte Positionen aus _MY_POSITIONS werden als historische Käufe vorgeladen

Startkapital: 148.000 CHF
"""
from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional

from app.domain.portfolio import (
    Position, PortfolioTrade, PortfolioTradeCreate, PortfolioSummary, TradeAction
)

# ── Konfiguration ─────────────────────────────────────────────────────────────

STARTING_CAPITAL_CHF = 148_000.0

# FX-Rates (Fallback — Prod: aus settings)
_USD_CHF = 0.889

# Symbolnamen
_NAMES: Dict[str, str] = {
    "NVDA": "NVIDIA Corp.",
    "MSFT": "Microsoft Corp.",
    "ZGLD": "ZKB Gold ETF",
    "NOVN": "Novartis AG",
    "AAPL": "Apple Inc.",
    "SPY":  "SPDR S&P 500 ETF",
}

# Echte Startpositionen (werden als historische Käufe eingeseeded)
_SEED_TRADES = [
    # symbol, action, quantity, price, currency, date, notes
    ("NVDA", "buy",  59,  748.20, "USD", datetime(2024,  6, 15, tzinfo=timezone.utc), "Initialkauf NVIDIA"),
    ("MSFT", "buy", 130,  405.10, "USD", datetime(2024,  8,  3, tzinfo=timezone.utc), "Initialkauf Microsoft"),
    ("ZGLD", "buy", 210,  176.80, "CHF", datetime(2024,  9, 20, tzinfo=timezone.utc), "Gold-Absicherung"),
    ("NOVN", "buy", 282,   88.60, "CHF", datetime(2024, 10,  7, tzinfo=timezone.utc), "Novartis Dividende"),
]


class PortfolioService:
    """
    Portfolio-Verwaltung.

    Trades werden in-memory verwaltet und optional in PostgreSQL persistiert.
    Positionen werden dynamisch aus den Trades berechnet (FIFO nicht notwendig,
    da Durchschnittspreis verwendet wird).
    """

    def __init__(self, usd_chf: float = _USD_CHF) -> None:
        self._trades: List[PortfolioTrade] = []
        self._usd_chf = usd_chf
        self._db_loaded = False
        self._seed_initial_trades()

    # ── Initialisierung ────────────────────────────────────────────────────────

    def _seed_initial_trades(self) -> None:
        """Vorbelegen mit echten historischen Käufen."""
        for sym, action, qty, price, ccy, ts, notes in _SEED_TRADES:
            fx = self._usd_chf if ccy == "USD" else 1.0
            value_chf = round(qty * price * fx, 2)
            fees = round(value_chf * 0.00075, 2)  # Schweizer Stempelsteuer 0.075%
            self._trades.append(PortfolioTrade(
                id=str(uuid.uuid4()),
                symbol=sym,
                action=TradeAction(action),
                quantity=qty,
                price=price,
                fees=fees,
                currency=ccy,
                timestamp=ts,
                notes=notes,
                value_chf=value_chf,
                total_chf=round(value_chf + fees, 2),
            ))

    async def load_from_db(self) -> None:
        """
        Versucht Trades aus PostgreSQL zu laden.
        Bei Fehler bleibt der In-Memory-State unverändert.
        """
        try:
            from sqlalchemy import select
            from app.services.database import AsyncSessionLocal
            from app.models.portfolio import PortfolioTradeModel

            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(PortfolioTradeModel).order_by(PortfolioTradeModel.timestamp)
                )
                rows = result.scalars().all()

            if rows:
                self._trades = []
                for row in rows:
                    fx = self._usd_chf if row.currency == "USD" else 1.0
                    value_chf = round(float(row.quantity) * float(row.price) * fx, 2)
                    self._trades.append(PortfolioTrade(
                        id=row.id,
                        symbol=row.symbol,
                        action=TradeAction(row.action),
                        quantity=float(row.quantity),
                        price=float(row.price),
                        fees=float(row.fees),
                        currency=row.currency,
                        timestamp=row.timestamp,
                        notes=row.notes or "",
                        value_chf=value_chf,
                        total_chf=round(
                            value_chf + float(row.fees)
                            if row.action == "buy"
                            else value_chf - float(row.fees),
                            2,
                        ),
                    ))
                self._db_loaded = True
                print(f"[PortfolioService] {len(self._trades)} Trades aus DB geladen")

        except Exception as exc:
            print(f"[PortfolioService] DB nicht verfügbar — In-Memory-Modus: {exc}")

    # ── CRUD ──────────────────────────────────────────────────────────────────

    async def add_trade(self, data: PortfolioTradeCreate) -> PortfolioTrade:
        """Neuen Trade erfassen (In-Memory + optional DB)."""
        fx = self._usd_chf if data.currency == "USD" else 1.0
        value_chf = round(data.quantity * data.price * fx, 2)
        total_chf = round(
            value_chf + data.fees if data.action == TradeAction.buy else value_chf - data.fees,
            2,
        )
        trade = PortfolioTrade(
            id=str(uuid.uuid4()),
            symbol=data.symbol.upper(),
            action=data.action,
            quantity=data.quantity,
            price=data.price,
            fees=data.fees,
            currency=data.currency.upper(),
            timestamp=data.timestamp or datetime.now(tz=timezone.utc),
            notes=data.notes,
            value_chf=value_chf,
            total_chf=total_chf,
        )
        self._trades.append(trade)
        await self._persist_trade(trade)
        return trade

    async def delete_trade(self, trade_id: str) -> bool:
        """Trade löschen (Seed-Trades können nicht gelöscht werden)."""
        before = len(self._trades)
        self._trades = [t for t in self._trades if t.id != trade_id]
        deleted = len(self._trades) < before
        if deleted:
            await self._delete_from_db(trade_id)
        return deleted

    def get_trades(self) -> List[PortfolioTrade]:
        """Alle Trades (neueste zuerst)."""
        return sorted(self._trades, key=lambda t: t.timestamp, reverse=True)

    # ── Positions-Berechnung ──────────────────────────────────────────────────

    def get_positions(self, price_fn: Optional[Callable[[str], float]] = None) -> List[Position]:
        """
        Berechnet offene Positionen aus den Trades.
        price_fn(symbol) → aktueller Preis in Originalwährung.
        """
        # Aggregation nach Symbol
        qty_map:        Dict[str, float] = defaultdict(float)
        cost_map:       Dict[str, float] = defaultdict(float)   # Gesamtkosten CHF
        realized_map:   Dict[str, float] = defaultdict(float)   # realisierte PnL CHF
        ccy_map:        Dict[str, str]   = {}
        opened_map:     Dict[str, datetime] = {}

        for t in sorted(self._trades, key=lambda x: x.timestamp):
            sym = t.symbol
            ccy_map[sym] = t.currency
            fx = self._usd_chf if t.currency == "USD" else 1.0

            if t.action == TradeAction.buy:
                if sym not in opened_map:
                    opened_map[sym] = t.timestamp
                qty_map[sym]  += t.quantity
                cost_map[sym] += t.quantity * t.price * fx

            elif t.action == TradeAction.sell:
                if qty_map[sym] > 0:
                    avg_cost_per_share = cost_map[sym] / qty_map[sym] if qty_map[sym] else 0
                    sell_value_chf = t.quantity * t.price * fx
                    cost_of_sold   = t.quantity * avg_cost_per_share
                    realized_map[sym] += sell_value_chf - cost_of_sold - t.fees
                    qty_map[sym]  -= t.quantity
                    cost_map[sym] -= cost_of_sold
                    if qty_map[sym] <= 0:
                        qty_map[sym]  = 0
                        cost_map[sym] = 0

        positions: List[Position] = []
        for sym, qty in qty_map.items():
            if qty <= 0.001:
                continue
            ccy = ccy_map.get(sym, "CHF")
            fx  = self._usd_chf if ccy == "USD" else 1.0
            avg_cost_chf = cost_map[sym]
            avg_entry    = avg_cost_chf / qty / fx if qty else 0

            current_price = price_fn(sym) if price_fn else avg_entry
            value_chf     = round(qty * current_price * fx, 2)
            cost_chf      = round(avg_cost_chf, 2)
            unrealized    = round(value_chf - cost_chf, 2)
            unrealized_pct = round(unrealized / cost_chf * 100, 2) if cost_chf else 0.0

            positions.append(Position(
                symbol=sym,
                name=_NAMES.get(sym, sym),
                quantity=round(qty, 4),
                avg_entry_price=round(avg_entry, 4),
                current_price=round(current_price, 4),
                currency=ccy,
                unrealized_pnl=unrealized,
                unrealized_pnl_pct=unrealized_pct,
                realized_pnl=round(realized_map.get(sym, 0.0), 2),
                value_chf=value_chf,
                cost_basis_chf=cost_chf,
                opened_at=opened_map.get(sym),
            ))

        return sorted(positions, key=lambda p: p.value_chf, reverse=True)

    # ── Summary ───────────────────────────────────────────────────────────────

    def get_summary(
        self,
        price_fn: Optional[Callable[[str], float]] = None,
        today_pnl_fn: Optional[Callable[[str], float]] = None,
    ) -> PortfolioSummary:
        """Gesamtübersicht des Portfolios."""
        positions = self.get_positions(price_fn)

        # Cashberechnung: Startkapital − alle Käufe (inkl. Gebühren) + alle Verkäufe (− Gebühren)
        cash = STARTING_CAPITAL_CHF
        for t in self._trades:
            if t.action == TradeAction.buy:
                cash -= t.total_chf
            else:
                cash += t.total_chf
        cash = round(cash, 2)

        positions_value  = round(sum(p.value_chf for p in positions), 2)
        invested_chf     = round(sum(p.cost_basis_chf for p in positions), 2)
        total_value      = round(positions_value + max(cash, 0), 2)
        unrealized_pnl   = round(sum(p.unrealized_pnl for p in positions), 2)
        realized_pnl     = round(sum(p.realized_pnl for p in positions), 2)
        total_pnl        = round(unrealized_pnl + realized_pnl, 2)
        total_pnl_pct    = round(total_pnl / STARTING_CAPITAL_CHF * 100, 2)

        today_pnl = 0.0
        if today_pnl_fn:
            for p in positions:
                today_pnl += today_pnl_fn(p.symbol)
        today_pnl = round(today_pnl, 2)

        # Gewichtungen setzen
        for p in positions:
            p.weight_pct = round(p.value_chf / total_value * 100, 1) if total_value else 0

        return PortfolioSummary(
            starting_capital_chf=STARTING_CAPITAL_CHF,
            total_value_chf=total_value,
            invested_chf=invested_chf,
            cash_chf=cash,
            positions_value_chf=positions_value,
            total_pnl_chf=total_pnl,
            total_pnl_pct=total_pnl_pct,
            unrealized_pnl_chf=unrealized_pnl,
            realized_pnl_chf=realized_pnl,
            today_pnl_chf=today_pnl,
            positions=positions,
            trades=self.get_trades(),
            num_trades=len(self._trades),
            num_open_pos=len(positions),
        )

    # ── DB-Persistenz ─────────────────────────────────────────────────────────

    async def _persist_trade(self, trade: PortfolioTrade) -> None:
        try:
            from app.services.database import AsyncSessionLocal
            from app.models.portfolio import PortfolioTradeModel

            async with AsyncSessionLocal() as session:
                row = PortfolioTradeModel(
                    id=trade.id,
                    symbol=trade.symbol,
                    action=trade.action.value,
                    quantity=trade.quantity,
                    price=trade.price,
                    fees=trade.fees,
                    currency=trade.currency,
                    notes=trade.notes or None,
                    timestamp=trade.timestamp,
                    created_at=datetime.now(tz=timezone.utc),
                )
                session.add(row)
                await session.commit()
        except Exception as exc:
            print(f"[PortfolioService] DB-Persist fehlgeschlagen (kein Problem): {exc}")

    async def _delete_from_db(self, trade_id: str) -> None:
        try:
            from sqlalchemy import delete
            from app.services.database import AsyncSessionLocal
            from app.models.portfolio import PortfolioTradeModel

            async with AsyncSessionLocal() as session:
                await session.execute(
                    delete(PortfolioTradeModel).where(PortfolioTradeModel.id == trade_id)
                )
                await session.commit()
        except Exception:
            pass
