"""
Interpretation Layer Test: RegimeDetector
Testet die Klassifikation von Bull/Bear/Sideways/Crisis Regimes.
"""
import pytest
from app.domain.regime_state import RegimeType, SubRegime
from app.layers.interpretation.regime_detector import RegimeDetector


@pytest.fixture
def detector():
    return RegimeDetector()


# ── Regime-Klassifikation ─────────────────────────────────────────────────────

def test_bull_market_detected(detector, bull_macro):
    regime = detector.detect(bull_macro)
    assert regime.regime_type == RegimeType.bull_market
    assert not regime.is_risk_off


def test_bear_market_detected(detector, bear_macro):
    regime = detector.detect(bear_macro)
    assert regime.regime_type in {RegimeType.bear_market, RegimeType.volatile}
    assert regime.is_risk_off


def test_crisis_detected(detector, crisis_macro):
    regime = detector.detect(crisis_macro)
    assert regime.regime_type == RegimeType.crisis
    assert regime.sub_regime == SubRegime.risk_off
    assert regime.max_position_size_pct <= 1.0


def test_sideways_on_neutral_data(detector):
    from app.domain.regime_state import MacroSnapshot
    neutral = MacroSnapshot(vix=17.0, yield_curve_10y_2y=0.1, fear_greed_index=50)
    regime = detector.detect(neutral)
    assert regime.regime_type == RegimeType.sideways


# ── Konfidenz & Stärke ────────────────────────────────────────────────────────

def test_confidence_increases_with_more_data(detector):
    from app.domain.regime_state import MacroSnapshot
    minimal  = MacroSnapshot(vix=25.0)
    complete = MacroSnapshot(
        vix=25.0, yield_curve_10y_2y=-0.3,
        fear_greed_index=30, fed_rate=5.0, cpi_us=4.5,
    )
    assert detector.detect(complete).confidence > detector.detect(minimal).confidence


def test_position_limits_lower_in_crisis(detector, crisis_macro, bull_macro):
    crisis = detector.detect(crisis_macro)
    bull   = detector.detect(bull_macro)
    assert crisis.max_position_size_pct < bull.max_position_size_pct


# ── Charakteristiken ─────────────────────────────────────────────────────────

def test_characteristics_not_empty(detector, bull_macro):
    regime = detector.detect(bull_macro)
    assert len(regime.characteristics) > 0


def test_active_risks_in_crisis(detector, crisis_macro):
    regime = detector.detect(crisis_macro)
    assert len(regime.active_risks) > 0


def test_label_readable(detector, bull_macro):
    regime = detector.detect(bull_macro)
    assert isinstance(regime.label, str)
    assert len(regime.label) > 3
