"""Shared pytest fixtures für alle Layer-Tests."""
import pytest
from app.domain.regime_state import MacroSnapshot, RegimeState, RegimeType, SubRegime
from app.domain.signal import Signal, SignalType, SignalStrength, SignalConfidence, ScoreBreakdown
from app.domain.recommendation import BiasRisk


@pytest.fixture
def bull_macro() -> MacroSnapshot:
    return MacroSnapshot(
        vix=14.0, yield_curve_10y_2y=0.6,
        fear_greed_index=68, fed_rate=3.75,
        cpi_us=2.4, unemployment_us=4.1,
    )


@pytest.fixture
def bear_macro() -> MacroSnapshot:
    return MacroSnapshot(
        vix=38.0, yield_curve_10y_2y=-0.6,
        fear_greed_index=18, fed_rate=5.5,
        cpi_us=6.2, unemployment_us=5.8,
    )


@pytest.fixture
def crisis_macro() -> MacroSnapshot:
    return MacroSnapshot(vix=55.0, yield_curve_10y_2y=-1.2, fear_greed_index=5, fed_rate=5.5)


@pytest.fixture
def sample_signal() -> Signal:
    """Starkes Buy-Signal für NVDA."""
    return Signal(
        asset_symbol="NVDA",
        asset_name="NVIDIA Corp.",
        signal_type=SignalType.buy,
        strength=SignalStrength.strong,
        score=ScoreBreakdown(
            fundamental=85, technical=80, management=85,
            sentiment=75, geopolitical=70, macro=75,
            total=80, verdict=SignalType.buy, confidence=SignalConfidence.high,
        ),
        price_at_signal=880.0,
        stop_loss=800.0,
        target_price=1050.0,
    )


@pytest.fixture
def bull_regime(bull_macro) -> RegimeState:
    from app.layers.interpretation.regime_detector import RegimeDetector
    return RegimeDetector().detect(bull_macro)


@pytest.fixture
def no_bias() -> BiasRisk:
    return BiasRisk(overall_score=0, detected_biases=[], warnings=[])


@pytest.fixture
def high_bias() -> BiasRisk:
    return BiasRisk(
        overall_score=75,
        detected_biases=["fomo", "overconfidence"],
        warnings=["FOMO erkannt", "Overconfidence nach 3 Gewinnen"],
        recommendation_adjusted=True,
    )
