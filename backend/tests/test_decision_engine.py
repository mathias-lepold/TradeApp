"""
Decision Engine Test
Testet den vollständigen Signal → Regime → Bias → Recommendation Durchlauf.
"""
import pytest
from app.domain.recommendation import RecommendationAction, RecommendationPriority
from app.domain.regime_state import RegimeType
from app.domain.signal import SignalType
from app.layers.decision.engine import DecisionEngine
from app.layers.decision.risk_manager import RiskManager


@pytest.fixture
def engine():
    return DecisionEngine(
        risk_manager=RiskManager(),
        portfolio_value_chf=100_000.0,
        fx_usd_chf=0.889,
    )


# ── Kaufempfehlung ────────────────────────────────────────────────────────────

def test_buy_recommendation_in_bull_market(engine, sample_signal, bull_regime, no_bias):
    rec = engine.decide(sample_signal, bull_regime, no_bias)
    assert rec.action == RecommendationAction.buy
    assert rec.composite_score == sample_signal.score.total


def test_buy_includes_sizing(engine, sample_signal, bull_regime, no_bias):
    rec = engine.decide(sample_signal, bull_regime, no_bias)
    assert rec.sizing is not None
    assert rec.sizing.suggested_chf > 0


# ── Regime-Anpassung ──────────────────────────────────────────────────────────

def test_buy_blocked_in_crisis(engine, sample_signal, no_bias):
    from app.layers.interpretation.regime_detector import RegimeDetector
    from app.domain.regime_state import MacroSnapshot
    crisis = RegimeDetector().detect(MacroSnapshot(vix=55.0, fear_greed_index=5))
    rec = engine.decide(sample_signal, crisis, no_bias)
    assert rec.action in {RecommendationAction.avoid, RecommendationAction.wait}


def test_buy_blocked_in_volatile_with_low_score(engine, no_bias):
    """Volatile Markt + Score < 80 → Wait (Engine-Regel: volatile erfordert Score > 80)."""
    from app.layers.interpretation.regime_detector import RegimeDetector
    from app.domain.regime_state import MacroSnapshot
    from app.domain.signal import Signal, ScoreBreakdown, SignalStrength, SignalConfidence
    volatile = RegimeDetector().detect(
        MacroSnapshot(vix=36.0, yield_curve_10y_2y=-0.5, fear_greed_index=20)
    )
    weak_signal = Signal(
        asset_symbol="NVDA", asset_name="NVIDIA Corp.",
        signal_type=SignalType.buy, strength=SignalStrength.moderate,
        score=ScoreBreakdown(
            fundamental=75, technical=70, management=75,
            sentiment=65, geopolitical=65, macro=68,
            total=71, verdict=SignalType.buy, confidence=SignalConfidence.medium,
        ),
        price_at_signal=880.0, stop_loss=800.0, target_price=1050.0,
    )
    rec = engine.decide(weak_signal, volatile, no_bias)
    assert rec.action in {RecommendationAction.wait, RecommendationAction.avoid}


# ── Bias-Override ──────────────────────────────────────────────────────────────

def test_high_bias_overrides_buy_to_wait(engine, sample_signal, bull_regime, high_bias):
    rec = engine.decide(sample_signal, bull_regime, high_bias)
    assert rec.action == RecommendationAction.wait
    assert "Bias" in rec.rationale or "bias" in rec.rationale.lower()


# ── Score-Schwelle ─────────────────────────────────────────────────────────────

def test_low_score_signal_returns_avoid(engine, bull_regime, no_bias):
    from app.domain.signal import Signal, ScoreBreakdown, SignalStrength, SignalConfidence
    low_signal = Signal(
        asset_symbol="XYZ", asset_name="Low Score Corp.",
        signal_type=SignalType.hold, strength=SignalStrength.weak,
        score=ScoreBreakdown(
            fundamental=45, technical=40, management=45,
            sentiment=40, geopolitical=50, macro=45,
            total=43, verdict=SignalType.hold, confidence=SignalConfidence.low,
        ),
        price_at_signal=50.0,
    )
    rec = engine.decide(low_signal, bull_regime, no_bias)
    assert rec.action == RecommendationAction.avoid


# ── Rückverfolgbarkeit ────────────────────────────────────────────────────────

def test_recommendation_traces_signal_id(engine, sample_signal, bull_regime, no_bias):
    rec = engine.decide(sample_signal, bull_regime, no_bias)
    assert rec.signal_id == sample_signal.id
    assert rec.regime_state_id == bull_regime.id


def test_recommendation_has_invalidation_conditions(engine, sample_signal, bull_regime, no_bias):
    rec = engine.decide(sample_signal, bull_regime, no_bias)
    assert len(rec.conditions_to_invalidate) > 0
