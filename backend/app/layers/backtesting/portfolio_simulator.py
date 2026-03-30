"""
Portfolio Simulator
Simuliert Trades mit 1%-Risiko-Regel, CRV 2.0, Stop-Loss und Take-Profit.
Gibt Equity-Kurve (tägliche Zeitreihe) und Trade-Liste zurück.
"""
from __future__ import annotations

import math
import uuid
from datetime import date, timedelta
from typing import List, Optional, Tuple

from app.domain.backtest import TradeRecord, EquityCurvePoint


# ── Interne Datenstrukturen ───────────────────────────────────────────────────

class _OpenPosition:
    __slots__ = ("entry_day", "entry_price", "stop_loss", "take_profit",
                 "quantity", "signal_score", "entry_date")

    def __init__(
        self, entry_day: int, entry_price: float, stop_loss: float,
        take_profit: float, quantity: float, signal_score: int, entry_date: date,
    ) -> None:
        self.entry_day    = entry_day
        self.entry_price  = entry_price
        self.stop_loss    = stop_loss
        self.take_profit  = take_profit
        self.quantity     = quantity
        self.signal_score = signal_score
        self.entry_date   = entry_date


# ── Portfolio Simulator ───────────────────────────────────────────────────────

class PortfolioSimulator:
    """
    Einfacher Long-Only Portfolio-Simulator.

    Regeln:
    - 1% Risikoregel: max. 1% des Portfolios als Risiko pro Trade
    - Max. 10% Kapitaleinsatz je Position
    - Min. CRV 2.0 (Take-Profit = Einstieg + 2 × (Einstieg – Stop))
    - Stop-Loss: aus Signal oder 3% unter Einstieg
    - Max. Haltedauer: 20 Handelstage
    """

    MAX_RISK_PCT   = 0.01   # 1%
    MAX_POS_PCT    = 0.10   # max. 10% des Kapitals
    MIN_CRV        = 2.0
    MAX_HOLD_DAYS  = 20
    MIN_STOP_PCT   = 0.02   # mind. 2% Stop-Abstand
    MAX_STOP_PCT   = 0.08   # max. 8% Stop-Abstand

    def __init__(self, initial_capital: float) -> None:
        self.initial_capital = initial_capital

    def simulate(
        self,
        prices:             List[float],
        daily_signals:      List[Tuple[int, Optional[object]]],  # (day_idx, Signal | None)
        start_date:         date,
        symbol:             str,
        daily_vol:          float = 0.02,
    ) -> Tuple[List[TradeRecord], List[EquityCurvePoint]]:
        """
        Simuliert Trades über die gesamte Preisreihe.

        Args:
            prices:        Tägliche Schlusskurse (len = n_days)
            daily_signals: Liste von (tag_index, Signal oder None) ab MIN_PERIOD
            start_date:    Startdatum für Label-Generierung
            symbol:        Symbol-Kürzel
            daily_vol:     Tägliche Volatilität (für Range-Schätzung)

        Returns:
            (trades, equity_curve)
        """
        n_days   = len(prices)
        capital  = self.initial_capital
        position: Optional[_OpenPosition] = None
        trades:   List[TradeRecord]       = []
        equity_curve: List[EquityCurvePoint] = []

        # Signal-Map: tag → Signal
        sig_map = {day: sig for day, sig in daily_signals}

        peak_equity = capital

        for i in range(n_days):
            current_price = prices[i]
            current_date  = start_date + timedelta(days=i)
            signal        = sig_map.get(i)

            # ── Prüfe offene Position ─────────────────────────────────────────
            if position is not None:
                duration = i - position.entry_day

                # Schätze Tages-Range aus Volatilität
                day_range = current_price * daily_vol * 1.5
                est_low   = current_price - day_range / 2
                est_high  = current_price + day_range / 2

                exit_price  = None
                exit_reason = None

                # Stop-Loss getroffen?
                if est_low <= position.stop_loss:
                    exit_price  = position.stop_loss
                    exit_reason = "stop_loss"

                # Take-Profit getroffen? (Priorität falls beide am selben Tag)
                if est_high >= position.take_profit:
                    exit_price  = position.take_profit
                    exit_reason = "take_profit"

                # Max-Haltedauer überschritten?
                if exit_reason is None and duration >= self.MAX_HOLD_DAYS:
                    exit_price  = current_price
                    exit_reason = "end_of_period"

                # Verkaufssignal?
                if (exit_reason is None and signal is not None
                        and hasattr(signal, "signal_type")
                        and signal.signal_type in ("sell", "avoid", "reduce", "exit")):
                    exit_price  = current_price
                    exit_reason = "signal_exit"

                if exit_price is not None:
                    trade = self._close_position(
                        pos=position,
                        exit_price=exit_price,
                        exit_date=current_date,
                        exit_reason=exit_reason,
                        symbol=symbol,
                    )
                    trades.append(trade)
                    capital  += trade.pnl_chf
                    position  = None

            # ── Einstieg prüfen (kein offenes Handel) ────────────────────────
            if position is None and signal is not None:
                if (hasattr(signal, "signal_type")
                        and signal.signal_type in ("buy", "add")
                        and hasattr(signal, "score")
                        and signal.score.total >= 65):

                    pos = self._try_open_position(
                        signal=signal,
                        current_price=current_price,
                        entry_day=i,
                        entry_date=current_date,
                        capital=capital,
                    )
                    if pos is not None:
                        position = pos

            # ── Equity-Kurve ──────────────────────────────────────────────────
            unrealized = 0.0
            if position is not None:
                unrealized = (current_price - position.entry_price) * position.quantity

            equity = capital + unrealized
            peak_equity = max(peak_equity, equity)
            drawdown = (peak_equity - equity) / peak_equity * 100 if peak_equity > 0 else 0.0

            equity_curve.append(EquityCurvePoint(
                date=current_date.isoformat(),
                equity=round(equity, 2),
                drawdown_pct=round(drawdown, 2),
            ))

        # ── Offene Position am Ende schließen ─────────────────────────────────
        if position is not None:
            trade = self._close_position(
                pos=position,
                exit_price=prices[-1],
                exit_date=start_date + timedelta(days=n_days - 1),
                exit_reason="end_of_period",
                symbol=symbol,
            )
            trades.append(trade)
            capital += trade.pnl_chf

        return trades, equity_curve

    # ── Hilfsmethoden ─────────────────────────────────────────────────────────

    def _try_open_position(
        self,
        signal,
        current_price: float,
        entry_day:     int,
        entry_date:    date,
        capital:       float,
    ) -> Optional[_OpenPosition]:
        """Berechnet Positionsgröße und öffnet Position falls Regeln erfüllt."""
        entry = current_price

        # Stop-Loss: aus Signal oder 3% unter Einstieg
        stop_raw = getattr(signal, "stop_loss", None)
        if stop_raw and stop_raw > 0 and (entry - stop_raw) / entry <= self.MAX_STOP_PCT:
            stop_loss = stop_raw
        else:
            stop_loss = entry * (1 - self.MIN_STOP_PCT)

        # Stop-Abstand mindestens MIN_STOP_PCT
        risk_per_share = entry - stop_loss
        if risk_per_share <= 0:
            return None

        # Abstand zu eng oder zu weit
        stop_pct = risk_per_share / entry
        if stop_pct < self.MIN_STOP_PCT * 0.5 or stop_pct > self.MAX_STOP_PCT:
            stop_loss  = entry * (1 - self.MIN_STOP_PCT)
            risk_per_share = entry - stop_loss

        # Take-Profit: aus Signal oder CRV 2.0
        tp_raw = getattr(signal, "target_price", None)
        if tp_raw and tp_raw > entry:
            crv = (tp_raw - entry) / risk_per_share
            take_profit = tp_raw if crv >= self.MIN_CRV else entry + risk_per_share * self.MIN_CRV
        else:
            take_profit = entry + risk_per_share * self.MIN_CRV

        # 1%-Risikoregel
        risk_amount   = capital * self.MAX_RISK_PCT
        quantity      = risk_amount / risk_per_share

        # Max-Position begrenzen
        max_pos_value = capital * self.MAX_POS_PCT
        quantity      = min(quantity, max_pos_value / entry)

        if quantity < 0.01:
            return None

        return _OpenPosition(
            entry_day=entry_day,
            entry_price=entry,
            stop_loss=round(stop_loss, 4),
            take_profit=round(take_profit, 4),
            quantity=round(quantity, 4),
            signal_score=signal.score.total,
            entry_date=entry_date,
        )

    def _close_position(
        self,
        pos:         _OpenPosition,
        exit_price:  float,
        exit_date:   date,
        exit_reason: str,
        symbol:      str,
    ) -> TradeRecord:
        pnl_chf = (exit_price - pos.entry_price) * pos.quantity
        pnl_pct = (exit_price - pos.entry_price) / pos.entry_price * 100
        duration = max(1, (exit_date - pos.entry_date).days)

        return TradeRecord(
            trade_id=str(uuid.uuid4()),
            symbol=symbol,
            entry_date=pos.entry_date.isoformat(),
            exit_date=exit_date.isoformat(),
            entry_price=round(pos.entry_price, 4),
            exit_price=round(exit_price, 4),
            quantity=round(pos.quantity, 4),
            stop_loss=round(pos.stop_loss, 4),
            take_profit=round(pos.take_profit, 4),
            pnl_chf=round(pnl_chf, 2),
            pnl_pct=round(pnl_pct, 3),
            duration_days=duration,
            exit_reason=exit_reason,
            signal_score=pos.signal_score,
            is_win=pnl_chf > 0,
        )
