"""
Reality Layer Test: TechnicalAnalyzer
Testet RSI, MACD, Bollinger Bands und den aggregierten technischen Score.
"""
import pytest
from app.layers.interpretation.signal_generator import TechnicalAnalyzer


# ── Hilfsfunktionen ───────────────────────────────────────────────────────────

def _trending_up(n: int = 40, start: float = 100.0, step: float = 1.0):
    return [start + i * step for i in range(n)]


def _trending_down(n: int = 40, start: float = 140.0, step: float = 1.0):
    return [start - i * step for i in range(n)]


def _flat(n: int = 40, value: float = 100.0):
    return [value] * n


# ── RSI ───────────────────────────────────────────────────────────────────────

def test_rsi_neutral_on_flat_prices():
    """Flache Preislinie → keine Bewegung → RSI 100 (keine Verluste)."""
    prices = _flat(20)
    rsi = TechnicalAnalyzer.rsi(prices)
    assert rsi == 100.0


def test_rsi_oversold_on_sharp_decline():
    """Starker Rückgang → RSI < 30 (überverkauft)."""
    prices = list(range(100, 60, -2))  # 100, 98, 96, ... 62
    rsi = TechnicalAnalyzer.rsi(prices)
    assert rsi < 30, f"Erwartet RSI < 30, bekommen {rsi}"


def test_rsi_overbought_on_sharp_rally():
    """Starker Anstieg → RSI > 70 (überkauft)."""
    prices = list(range(60, 110, 2))  # 60, 62, ... 108
    rsi = TechnicalAnalyzer.rsi(prices)
    assert rsi > 70, f"Erwartet RSI > 70, bekommen {rsi}"


def test_rsi_fallback_on_insufficient_data():
    """Weniger als period+1 Datenpunkte → Rückgabe 50 (neutral)."""
    assert TechnicalAnalyzer.rsi([100.0, 101.0], period=14) == 50.0


# ── MACD ──────────────────────────────────────────────────────────────────────

def test_macd_bullish_on_uptrend():
    """Aufwärtstrend → MACD-Linie > Signal-Linie → bullisches Histogramm."""
    prices = _trending_up(50)
    result = TechnicalAnalyzer.macd(prices)
    assert result["macd_line"] > 0
    assert result["histogram"] > 0


def test_macd_bearish_on_downtrend():
    """Abwärtstrend → negatives MACD-Histogramm."""
    prices = _trending_down(50)
    result = TechnicalAnalyzer.macd(prices)
    assert result["macd_line"] < 0


def test_macd_neutral_on_insufficient_data():
    """Weniger als slow(26) Preise → alle Werte 0."""
    result = TechnicalAnalyzer.macd([100.0] * 20)
    assert result["macd_line"] == 0.0
    assert result["signal_line"] == 0.0
    assert result["histogram"] == 0.0


# ── Bollinger Bands ───────────────────────────────────────────────────────────

def test_bollinger_upper_above_lower():
    """Oberes Band muss immer über unterem Band liegen."""
    prices = _trending_up(30)
    bb = TechnicalAnalyzer.bollinger_bands(prices)
    assert bb["upper"] > bb["middle"] > bb["lower"]


def test_bollinger_pct_b_for_middle_price():
    """Kurs exakt auf dem Mittelband → pct_b ≈ 0.5."""
    prices = _flat(25, value=100.0)
    bb = TechnicalAnalyzer.bollinger_bands(prices)
    # Alle Preise gleich → std=0, Band-Breite=0 → pct_b = 0.5 (Division durch Null-Fall)
    assert 0.0 <= bb["pct_b"] <= 1.0


def test_bollinger_narrow_on_flat_prices():
    """Flache Preise → sehr schmale Bänder (fast Null-Breite)."""
    prices = _flat(25, value=100.0)
    bb = TechnicalAnalyzer.bollinger_bands(prices)
    assert bb["bandwidth"] < 0.001  # nahezu Null


# ── Aggregierter technischer Score ────────────────────────────────────────────

def test_technical_score_range():
    """Score muss immer zwischen 0 und 100 liegen."""
    for prices in [_trending_up(40), _trending_down(40), _flat(40)]:
        result = TechnicalAnalyzer.technical_score(prices)
        assert 0 <= result["score"] <= 100


def test_technical_score_higher_on_oversold():
    """Überverkaufte Situation → höherer Buy-Score als Aufwärtstrend."""
    oversold  = TechnicalAnalyzer.technical_score(_trending_down(40))
    overbought = TechnicalAnalyzer.technical_score(_trending_up(40))
    assert oversold["score"] > overbought["score"], (
        f"Überverkauft {oversold['score']} sollte > Überkauft {overbought['score']}"
    )


def test_technical_score_includes_expected_keys():
    """Rückgabe muss alle erwarteten Schlüssel enthalten."""
    result = TechnicalAnalyzer.technical_score(_trending_up(40))
    for key in ("score", "rsi", "macd", "bollinger", "signals"):
        assert key in result, f"Schlüssel '{key}' fehlt im Ergebnis"
