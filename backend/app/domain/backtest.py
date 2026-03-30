"""
Domain Models: Backtesting
Pydantic-Schemas für Konfiguration, Ergebnis, Trades und Equity-Kurve.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# ── Konfiguration ─────────────────────────────────────────────────────────────

class BacktestConfig(BaseModel):
    """Eingabe-Parameter für einen Backtest-Lauf."""
    symbol:          str   = Field(..., description="Tickersymbol, z.B. NVDA")
    start_date:      date  = Field(..., description="Startdatum des Backtests")
    end_date:        date  = Field(..., description="Enddatum des Backtests")
    initial_capital: float = Field(100_000.0, gt=0, description="Startkapital in CHF")
    seed:            int   = Field(42, description="Zufalls-Seed für Reproduzierbarkeit")
    min_score:       int   = Field(65, ge=50, le=90, description="Min. Signal-Score zum Einstieg")

    model_config = {"json_schema_extra": {
        "example": {
            "symbol": "NVDA",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "initial_capital": 100000.0,
            "seed": 42,
            "min_score": 65,
        }
    }}


# ── Einzelner Trade ───────────────────────────────────────────────────────────

class TradeRecord(BaseModel):
    """Ein abgeschlossener simulierter Trade."""
    trade_id:       str
    symbol:         str
    entry_date:     str     # ISO-Datum
    exit_date:      str     # ISO-Datum
    entry_price:    float
    exit_price:     float
    quantity:       float
    stop_loss:      float
    take_profit:    float
    pnl_chf:        float
    pnl_pct:        float
    duration_days:  int
    exit_reason:    str     # "stop_loss" | "take_profit" | "signal_exit" | "end_of_period"
    signal_score:   Optional[int] = None
    is_win:         bool = False


# ── Equity-Kurve ──────────────────────────────────────────────────────────────

class EquityCurvePoint(BaseModel):
    """Täglicher Equity-Stand mit Drawdown."""
    date:         str   # ISO-Datum
    equity:       float
    drawdown_pct: float


# ── Performance-Kennzahlen ────────────────────────────────────────────────────

class BacktestMetrics(BaseModel):
    """Aggregierte Performance-Metriken eines Backtest-Laufs."""
    initial_capital:       float
    final_equity:          float
    total_return_pct:      float
    annualized_return_pct: float
    sharpe_ratio:          float
    calmar_ratio:          float
    max_drawdown_pct:      float
    win_rate:              float   # 0–1
    profit_factor:         float   # gross_profit / gross_loss
    num_trades:            int
    num_wins:              int
    num_losses:            int
    avg_trade_duration_days: float
    best_trade_pct:        float
    worst_trade_pct:       float
    avg_win_pct:           float
    avg_loss_pct:          float
    max_consecutive_wins:  int
    max_consecutive_losses: int


# ── Gesamtergebnis ────────────────────────────────────────────────────────────

class BacktestResult(BaseModel):
    """Vollständiges Ergebnis eines Backtest-Laufs."""
    backtest_id:  str = Field(default_factory=lambda: str(uuid.uuid4()))
    config:       BacktestConfig
    metrics:      BacktestMetrics
    equity_curve: List[EquityCurvePoint]
    trades:       List[TradeRecord]
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    duration_ms:  int = 0  # Laufzeit in Millisekunden
