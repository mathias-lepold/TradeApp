"""
Behavioral Layer Test: BiasDetector
Testet FOMO, Loss Aversion, Overconfidence, Revenge Trading,
Recency Bias und Confirmation Bias.
"""
import pytest
from datetime import datetime, timedelta
from app.domain.signal import SignalType
from app.layers.behavioral.bias_detector import BiasDetector, TraderContext, TradeHistoryEntry


@pytest.fixture
def detector():
    return BiasDetector()


@pytest.fixture
def clean_context():
    return TraderContext(portfolio_value_chf=100_000.0)


# ── FOMO ─────────────────────────────────────────────────────────────────────

def test_fomo_detected_at_extreme_greed(detector, sample_signal, clean_context):
    result = detector.analyze(sample_signal, clean_context, fear_greed_index=88)
    assert "fomo" in result.detected_biases


def test_no_fomo_at_low_fear_greed(detector, sample_signal, clean_context):
    result = detector.analyze(sample_signal, clean_context, fear_greed_index=30)
    assert "fomo" not in result.detected_biases


# ── Overconfidence ────────────────────────────────────────────────────────────

def test_overconfidence_after_win_streak(detector, sample_signal):
    ctx = TraderContext(consecutive_wins=4, portfolio_value_chf=100_000.0)
    result = detector.analyze(sample_signal, ctx, fear_greed_index=50)
    assert "overconfidence" in result.detected_biases


def test_no_overconfidence_at_start(detector, sample_signal, clean_context):
    result = detector.analyze(sample_signal, clean_context, fear_greed_index=50)
    assert "overconfidence" not in result.detected_biases


# ── Revenge Trading ───────────────────────────────────────────────────────────

def test_revenge_trading_detected_after_recent_loss(detector, sample_signal):
    ctx = TraderContext(
        last_trade_result="loss",
        last_trade_at=datetime.utcnow() - timedelta(minutes=30),
        portfolio_value_chf=100_000.0,
    )
    result = detector.analyze(sample_signal, ctx)
    assert "revenge_trading" in result.detected_biases


def test_no_revenge_trading_day_after_loss(detector, sample_signal):
    ctx = TraderContext(
        last_trade_result="loss",
        last_trade_at=datetime.utcnow() - timedelta(hours=30),
        portfolio_value_chf=100_000.0,
    )
    result = detector.analyze(sample_signal, ctx)
    assert "revenge_trading" not in result.detected_biases


# ── Confirmation Bias ─────────────────────────────────────────────────────────

def test_confirmation_bias_on_losing_position(detector, sample_signal):
    """Buy-Signal für eine Position mit -15% P&L → Confirmation Bias."""
    ctx = TraderContext(
        current_positions={"NVDA": -15.0},
        portfolio_value_chf=100_000.0,
    )
    result = detector.analyze(sample_signal, ctx, fear_greed_index=50)
    assert "confirmation_bias" in result.detected_biases


def test_no_confirmation_bias_without_position(detector, sample_signal, clean_context):
    result = detector.analyze(sample_signal, clean_context, fear_greed_index=50)
    assert "confirmation_bias" not in result.detected_biases


# ── Gesamtscore ───────────────────────────────────────────────────────────────

def test_bias_score_range(detector, sample_signal, clean_context):
    result = detector.analyze(sample_signal, clean_context)
    assert 0 <= result.overall_score <= 100


def test_high_bias_triggers_recommendation_adjusted(detector, sample_signal):
    ctx = TraderContext(
        consecutive_wins=5,
        last_trade_result="loss",
        last_trade_at=datetime.utcnow() - timedelta(minutes=45),
        current_positions={"NVDA": -20.0},
        portfolio_value_chf=100_000.0,
    )
    result = detector.analyze(sample_signal, ctx, fear_greed_index=90)
    assert result.recommendation_adjusted is True
    assert result.overall_score > 50
