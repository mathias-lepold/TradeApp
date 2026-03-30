"""
Decision Engine Test: RiskManager
Testet 1%-Regel, CRV-Check und Positionsgrößen-Berechnung.
"""
import pytest
from app.layers.decision.risk_manager import RiskManager


@pytest.fixture
def rm():
    return RiskManager(max_risk_per_trade_pct=1.0, max_position_pct=10.0)


# ── Positionsgrössen-Berechnung ───────────────────────────────────────────────

def test_sizing_respects_1pct_rule(rm, bull_regime):
    pv     = 100_000.0
    result = rm.calculate_sizing(
        entry_price=100.0, stop_loss=95.0,
        portfolio_value_chf=pv, regime=bull_regime,
    )
    # Max Risiko = 1% von 100k = 1000 CHF
    # Risk/Share = 5.0 → max 200 Shares → max 20k CHF
    assert result.risk_per_trade_chf == 1000.0
    assert result.suggested_pct <= bull_regime.max_position_size_pct


def test_sizing_limited_by_regime(rm, bull_regime):
    """Regime-Limit darf nicht überschritten werden."""
    result = rm.calculate_sizing(
        entry_price=10.0, stop_loss=9.99,  # winziger Stop → riesige Menge
        portfolio_value_chf=100_000.0, regime=bull_regime,
    )
    assert result.suggested_pct <= bull_regime.max_position_size_pct


def test_kelly_calculated_with_win_rate(rm, bull_regime):
    result = rm.calculate_sizing(
        entry_price=100.0, stop_loss=90.0,
        portfolio_value_chf=100_000.0, regime=bull_regime,
        win_rate=0.6, avg_win_loss_ratio=2.0,
    )
    assert result.kelly_fraction is not None
    assert 0.0 <= result.kelly_fraction <= 0.5  # Half-Kelly


# ── Order-Validierung ─────────────────────────────────────────────────────────

def test_validate_valid_order(rm, bull_regime):
    result = rm.validate_order(
        cost_chf=5000.0, stop_loss=95.0, entry_price=100.0,
        target_price=120.0, portfolio_value_chf=100_000.0, regime=bull_regime,
    )
    assert result["valid"] is True
    assert len(result["errors"]) == 0


def test_validate_rejects_bad_crv(rm, bull_regime):
    """CRV < 2.0 → Fehler."""
    result = rm.validate_order(
        cost_chf=5000.0, stop_loss=98.0, entry_price=100.0,
        target_price=101.0, portfolio_value_chf=100_000.0, regime=bull_regime,
    )
    assert result["valid"] is False
    assert any("CRV" in e for e in result["errors"])


def test_validate_warns_on_no_stop_loss(rm, bull_regime):
    result = rm.validate_order(
        cost_chf=5000.0, stop_loss=None, entry_price=100.0,
        target_price=None, portfolio_value_chf=100_000.0, regime=bull_regime,
    )
    assert any("Stop-Loss" in w for w in result["warnings"])


def test_stamp_tax_calculated(rm, bull_regime):
    result = rm.validate_order(
        cost_chf=10_000.0, stop_loss=95.0, entry_price=100.0,
        target_price=None, portfolio_value_chf=100_000.0, regime=bull_regime,
    )
    assert result["stamp_tax_chf"] == pytest.approx(7.5, abs=0.1)  # 0.075%


def test_validate_rejects_oversized_position(rm, bull_regime):
    """Mehr als 10% → Fehler."""
    result = rm.validate_order(
        cost_chf=15_000.0, stop_loss=95.0, entry_price=100.0,
        target_price=130.0, portfolio_value_chf=100_000.0, regime=bull_regime,
    )
    assert result["valid"] is False
    assert any("%" in e for e in result["errors"])
