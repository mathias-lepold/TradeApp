"""
Backtest Engine
Generiert historische Preisreihen (MockFeed-Logik mit festem Seed),
wendet SignalGenerator an und berechnet Performance-Metriken.
"""
from __future__ import annotations

import math
import random
import time
import uuid
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple

from app.domain.backtest import (
    BacktestConfig, BacktestMetrics, BacktestResult,
    EquityCurvePoint, TradeRecord,
)
from app.layers.interpretation.signal_generator import SignalGenerator
from app.layers.backtesting.portfolio_simulator import PortfolioSimulator


# ── Asset-Konfiguration (spiegelt MockFeed._MOCK_BASE wider) ─────────────────

_ASSET_CFG: Dict[str, Dict] = {
    "AAPL": {"price": 228.50, "daily_vol": 0.018, "volume_base": 58_000_000, "name": "Apple Inc."},
    "MSFT": {"price": 358.20, "daily_vol": 0.016, "volume_base": 22_000_000, "name": "Microsoft Corp."},
    "NVDA": {"price": 882.00, "daily_vol": 0.028, "volume_base": 45_000_000, "name": "NVIDIA Corp."},
    "SPY":  {"price": 521.40, "daily_vol": 0.012, "volume_base": 80_000_000, "name": "SPDR S&P 500 ETF"},
    "NOVN": {"price":  97.80, "daily_vol": 0.010, "volume_base":  3_200_000, "name": "Novartis AG"},
    "ZGLD": {"price": 210.50, "daily_vol": 0.008, "volume_base":     90_000, "name": "ZKB Gold ETF"},
    "AMZN": {"price": 192.00, "daily_vol": 0.019, "volume_base": 40_000_000, "name": "Amazon.com Inc."},
    "GOOGL":{"price": 175.00, "daily_vol": 0.017, "volume_base": 25_000_000, "name": "Alphabet Inc."},
    "META": {"price": 557.00, "daily_vol": 0.022, "volume_base": 15_000_000, "name": "Meta Platforms Inc."},
    "TSM":  {"price": 195.00, "daily_vol": 0.020, "volume_base": 12_000_000, "name": "Taiwan Semiconductor"},
}

# Standard-Fundamentalscores falls Symbol nicht bekannt
_DEFAULT_FUND: Dict[str, int] = {"fundamental": 70, "management": 70, "geopolitical": 60, "macro": 65}

_FUND_SCORES: Dict[str, Dict[str, int]] = {
    "MSFT": {"fundamental": 84, "management": 91, "geopolitical": 55, "macro": 68},
    "NVDA": {"fundamental": 88, "management": 86, "geopolitical": 72, "macro": 76},
    "AAPL": {"fundamental": 82, "management": 89, "geopolitical": 60, "macro": 72},
    "NOVN": {"fundamental": 79, "management": 82, "geopolitical": 88, "macro": 74},
    "ZGLD": {"fundamental": 75, "management": 70, "geopolitical": 85, "macro": 82},
    "AMZN": {"fundamental": 80, "management": 84, "geopolitical": 58, "macro": 70},
    "GOOGL":{"fundamental": 83, "management": 87, "geopolitical": 56, "macro": 69},
    "META": {"fundamental": 78, "management": 82, "geopolitical": 54, "macro": 67},
    "SPY":  {"fundamental": 75, "management": 75, "geopolitical": 65, "macro": 70},
    "TSM":  {"fundamental": 81, "management": 83, "geopolitical": 75, "macro": 71},
}

# Mindestperiode für technische Indikatoren (RSI 14 + MACD 26 + Signal 9 + Buffer)
_MIN_PERIOD = 40


# ── BacktestEngine ────────────────────────────────────────────────────────────

class BacktestEngine:
    """
    Reproduzierbares Backtesting mit MockFeed-kompatibler Preissimulation.

    Ablauf:
    1. Generiere n_days tägliche Preise (Brownsche Bewegung mit Mean-Reversion)
    2. Wende SignalGenerator ab Tag MIN_PERIOD an
    3. PortfolioSimulator simuliert Trades (1%-Regel, CRV 2.0)
    4. Berechne Sharpe, Max-Drawdown, Win-Rate, etc.
    """

    def __init__(self) -> None:
        self._sig_gen = SignalGenerator(min_score_threshold=60)

    # ── Öffentliche API ───────────────────────────────────────────────────────

    def run_backtest(self, config: BacktestConfig) -> BacktestResult:
        t0 = time.monotonic()

        # Handelstage abzählen (~252 pro Jahr)
        calendar_days = max(30, (config.end_date - config.start_date).days)
        n_days = max(60, int(calendar_days * 252 / 365))
        n_days = min(n_days, 756)  # max 3 Jahre

        # Asset-Config (Fallback für unbekannte Symbole)
        sym = config.symbol.upper()
        cfg = _ASSET_CFG.get(sym, {
            "price":       100.0,
            "daily_vol":   0.020,
            "volume_base": 1_000_000,
            "name":        sym,
        })

        # Preise + Volumen generieren
        prices, volumes = self._generate_prices(cfg, n_days, config.seed)

        # Signale generieren
        fund = _FUND_SCORES.get(sym, _DEFAULT_FUND)
        daily_signals = self._generate_signals(sym, cfg["name"], prices, volumes, fund, config.min_score)

        # Portfolio-Simulation
        sim = PortfolioSimulator(initial_capital=config.initial_capital)
        trades, equity_curve = sim.simulate(
            prices=prices,
            daily_signals=daily_signals,
            start_date=config.start_date,
            symbol=sym,
            daily_vol=cfg["daily_vol"],
        )

        # Metriken berechnen
        metrics = self._compute_metrics(
            trades=trades,
            equity_curve=equity_curve,
            initial_capital=config.initial_capital,
            n_days=n_days,
        )

        duration_ms = int((time.monotonic() - t0) * 1000)

        return BacktestResult(
            config=config,
            metrics=metrics,
            equity_curve=equity_curve,
            trades=trades,
            duration_ms=duration_ms,
        )

    # ── Preisreihen-Simulation ────────────────────────────────────────────────

    def _generate_prices(
        self,
        cfg:    Dict,
        n_days: int,
        seed:   int,
    ) -> Tuple[List[float], List[float]]:
        """
        Simuliert tägliche OHLC-Schlusskurse und Volumen
        mit Brownscher Bewegung + Mean-Reversion (identisch zu MockFeed).
        """
        rng        = random.Random(seed)
        base_price = cfg["price"]
        daily_vol  = cfg["daily_vol"]
        vol_base   = cfg["volume_base"]

        prices:  List[float] = [base_price]
        volumes: List[float] = [float(vol_base)]

        for _ in range(n_days - 1):
            prev = prices[-1]

            # Drift: sanfte Mean-Reversion zum Basispreis
            drift = 0.0002 * (base_price - prev) / base_price
            # Tägliche Zufallskomponente
            shock     = rng.gauss(drift, daily_vol)
            new_price = prev * (1.0 + shock)
            # Floor bei 30% des Basispreises
            new_price = max(new_price, base_price * 0.30)
            prices.append(round(new_price, 4))

            # Volumen
            vol = max(100, int(rng.gauss(vol_base, vol_base * 0.20)))
            volumes.append(float(vol))

        return prices, volumes

    # ── Signalgenerierung ─────────────────────────────────────────────────────

    def _generate_signals(
        self,
        symbol:     str,
        name:       str,
        prices:     List[float],
        volumes:    List[float],
        fund:       Dict[str, int],
        min_score:  int,
    ) -> List[Tuple[int, Optional[object]]]:
        """
        Erzeugt täglich ein Signal ab MIN_PERIOD.
        Gibt nur Signale zurück, die den min_score übersteigen.
        """
        # Passe SignalGenerator-Schwelle an Nutzerkonfiguration an
        self._sig_gen.min_score_threshold = min_score

        daily_signals = []
        for i in range(_MIN_PERIOD, len(prices)):
            price_window  = prices[:i + 1]
            volume_window = volumes[:i + 1]

            # Sentiment: neutral (50) — kein externer Fear&Greed in Backtest
            try:
                signal = self._sig_gen.generate_from_prices(
                    symbol=symbol,
                    name=name,
                    prices=price_window,
                    fund_scores=fund,
                    volumes=volume_window,
                    sentiment_score=50,
                )
            except Exception:
                signal = None

            daily_signals.append((i, signal))

        return daily_signals

    # ── Metriken ──────────────────────────────────────────────────────────────

    def _compute_metrics(
        self,
        trades:          List[TradeRecord],
        equity_curve:    List[EquityCurvePoint],
        initial_capital: float,
        n_days:          int,
    ) -> BacktestMetrics:
        final_equity = equity_curve[-1].equity if equity_curve else initial_capital

        # Returns
        total_return = (final_equity - initial_capital) / initial_capital * 100
        years = max(n_days / 252, 1 / 252)
        ann_return = ((final_equity / initial_capital) ** (1 / years) - 1) * 100

        # Drawdown
        max_dd = max((p.drawdown_pct for p in equity_curve), default=0.0)

        # Sharpe Ratio (tägliche Returns)
        daily_rets = []
        equities = [p.equity for p in equity_curve]
        for j in range(1, len(equities)):
            if equities[j - 1] > 0:
                daily_rets.append((equities[j] - equities[j - 1]) / equities[j - 1])

        if len(daily_rets) >= 2:
            mean_r = sum(daily_rets) / len(daily_rets)
            std_r  = math.sqrt(sum((r - mean_r) ** 2 for r in daily_rets) / (len(daily_rets) - 1))
            sharpe = (mean_r / std_r * math.sqrt(252)) if std_r > 0 else 0.0
        else:
            sharpe = 0.0

        # Calmar
        calmar = (ann_return / max_dd) if max_dd > 0 else 0.0

        # Trade-Statistiken
        wins   = [t for t in trades if t.is_win]
        losses = [t for t in trades if not t.is_win]

        num_trades = len(trades)
        num_wins   = len(wins)
        num_losses = len(losses)
        win_rate   = num_wins / num_trades if num_trades > 0 else 0.0

        gross_profit = sum(t.pnl_chf for t in wins)
        gross_loss   = abs(sum(t.pnl_chf for t in losses))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else (
            float("inf") if gross_profit > 0 else 0.0
        )

        avg_dur = sum(t.duration_days for t in trades) / num_trades if num_trades > 0 else 0.0

        best  = max((t.pnl_pct for t in trades), default=0.0)
        worst = min((t.pnl_pct for t in trades), default=0.0)

        avg_win  = sum(t.pnl_pct for t in wins)   / num_wins   if num_wins   > 0 else 0.0
        avg_loss = sum(t.pnl_pct for t in losses) / num_losses if num_losses > 0 else 0.0

        # Consecutive wins/losses
        max_cons_wins = max_cons_losses = 0
        cur_w = cur_l = 0
        for t in trades:
            if t.is_win:
                cur_w += 1; cur_l = 0
            else:
                cur_l += 1; cur_w = 0
            max_cons_wins   = max(max_cons_wins, cur_w)
            max_cons_losses = max(max_cons_losses, cur_l)

        return BacktestMetrics(
            initial_capital=round(initial_capital, 2),
            final_equity=round(final_equity, 2),
            total_return_pct=round(total_return, 3),
            annualized_return_pct=round(ann_return, 3),
            sharpe_ratio=round(sharpe, 3),
            calmar_ratio=round(calmar, 3),
            max_drawdown_pct=round(max_dd, 3),
            win_rate=round(win_rate, 4),
            profit_factor=round(profit_factor, 3),
            num_trades=num_trades,
            num_wins=num_wins,
            num_losses=num_losses,
            avg_trade_duration_days=round(avg_dur, 1),
            best_trade_pct=round(best, 3),
            worst_trade_pct=round(worst, 3),
            avg_win_pct=round(avg_win, 3),
            avg_loss_pct=round(avg_loss, 3),
            max_consecutive_wins=max_cons_wins,
            max_consecutive_losses=max_cons_losses,
        )
