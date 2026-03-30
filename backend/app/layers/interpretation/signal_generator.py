"""
Interpretation Layer: SignalGenerator + TechnicalAnalyzer
----------------------------------------------------------
TechnicalAnalyzer  — berechnet RSI, MACD, Bollinger Bands, Volume aus Preishistorie
SignalGenerator    — erstellt typisierte Signal-Objekte aus Scores + Preis-Kontext
"""
from __future__ import annotations

import math
from typing import Dict, Any, List, Optional, Tuple

from app.domain.signal import Signal, SignalType, SignalStrength, SignalConfidence, ScoreBreakdown
from app.domain.event import Event, EventType, EventSource


# ── TechnicalAnalyzer ──────────────────────────────────────────────────────────

class TechnicalAnalyzer:
    """
    Stateless Sammlung technischer Indikatoren.
    Alle Methoden arbeiten auf rohen Preislisten (List[float]).

    Mindest-Datenpunkte:
      RSI(14):          15 Preise
      MACD(12,26,9):    35 Preise (26 + 9 Signal-EMA)
      Bollinger(20,2):  20 Preise
    """

    # ── Kern-Indikatoren ───────────────────────────────────────────────────────

    @staticmethod
    def rsi(prices: List[float], period: int = 14) -> float:
        """
        Relative Strength Index (Wilder-Methode).
        Rückgabe: 0–100; < 30 = überverkauft, > 70 = überkauft.
        """
        if len(prices) < period + 1:
            return 50.0  # neutral bei unzureichenden Daten

        deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
        recent = deltas[-period:]
        gains  = [max(d, 0.0) for d in recent]
        losses = [abs(min(d, 0.0)) for d in recent]

        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period

        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return round(100.0 - (100.0 / (1.0 + rs)), 2)

    @staticmethod
    def ema(values: List[float], period: int) -> List[float]:
        """Exponential Moving Average — gibt komplette EMA-Reihe zurück."""
        if not values:
            return []
        k = 2.0 / (period + 1)
        ema_vals = [values[0]]
        for v in values[1:]:
            ema_vals.append(v * k + ema_vals[-1] * (1.0 - k))
        return ema_vals

    @classmethod
    def macd(
        cls,
        prices: List[float],
        fast: int = 12,
        slow: int = 26,
        signal_period: int = 9,
    ) -> Dict[str, float]:
        """
        MACD (Moving Average Convergence/Divergence).
        Rückgabe: {macd_line, signal_line, histogram}
        Positives Histogramm = bullisch.
        """
        neutral = {"macd_line": 0.0, "signal_line": 0.0, "histogram": 0.0}
        if len(prices) < slow:
            return neutral

        ema_fast = cls.ema(prices, fast)
        ema_slow = cls.ema(prices, slow)

        # MACD-Linie: EMA(fast) - EMA(slow), ab Index slow-1 gültig
        macd_series = [ema_fast[i] - ema_slow[i] for i in range(len(prices))]

        if len(macd_series) < signal_period:
            return {
                "macd_line": round(macd_series[-1], 6),
                "signal_line": 0.0,
                "histogram": round(macd_series[-1], 6),
            }

        sig_series = cls.ema(macd_series, signal_period)
        macd_line  = macd_series[-1]
        sig_line   = sig_series[-1]

        return {
            "macd_line":   round(macd_line, 6),
            "signal_line": round(sig_line, 6),
            "histogram":   round(macd_line - sig_line, 6),
        }

    @staticmethod
    def bollinger_bands(
        prices: List[float],
        period: int = 20,
        std_dev: float = 2.0,
    ) -> Dict[str, float]:
        """
        Bollinger Bands (SMA ± n×σ).
        Rückgabe: {upper, middle, lower, pct_b, bandwidth}
        pct_b: 0.0 = am unteren Band, 1.0 = am oberen Band.
        """
        window = prices[-period:] if len(prices) >= period else prices
        n = len(window)
        sma = sum(window) / n
        variance = sum((p - sma) ** 2 for p in window) / n
        std = math.sqrt(variance)

        upper = sma + std_dev * std
        lower = sma - std_dev * std
        current = prices[-1]
        band_width = upper - lower

        pct_b = (current - lower) / band_width if band_width > 0 else 0.5
        bandwidth = band_width / sma if sma > 0 else 0.0

        return {
            "upper":     round(upper, 4),
            "middle":    round(sma, 4),
            "lower":     round(lower, 4),
            "pct_b":     round(pct_b, 4),
            "bandwidth": round(bandwidth, 4),
        }

    @staticmethod
    def volume_score(volumes: List[int], lookback: int = 20) -> Tuple[int, str]:
        """
        Vergleicht aktuelles Volumen mit dem Durchschnitt.
        Rückgabe: (score_delta −15 bis +15, Beschreibung)
        """
        if not volumes or len(volumes) < 2:
            return 0, ""
        window = volumes[-min(lookback, len(volumes)):]
        avg_vol = sum(window[:-1]) / max(len(window) - 1, 1)
        last_vol = volumes[-1]

        if avg_vol == 0:
            return 0, ""

        ratio = last_vol / avg_vol
        if ratio >= 2.0:
            return 15, f"Starkes Volumen ({ratio:.1f}× Ø) — Bestätigung"
        if ratio >= 1.5:
            return 10, f"Überdurchschnittliches Volumen ({ratio:.1f}× Ø)"
        if ratio >= 1.2:
            return 5, ""
        if ratio < 0.5:
            return -10, "Sehr geringes Volumen — schwache Aussagekraft"
        if ratio < 0.7:
            return -5, ""
        return 0, ""

    # ── Gesamtbewertung ────────────────────────────────────────────────────────

    @classmethod
    def technical_score(
        cls,
        prices: List[float],
        volumes: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """
        Aggregiert RSI, MACD, Bollinger und Volume zu einem technischen Buy-Score 0–100.

        Score-Logik (Basiswert 50 — neutral):
          RSI:        −25 bis +25 Punkte
          MACD:       −15 bis +15 Punkte
          Bollinger:  −15 bis +20 Punkte
          Volume:     −10 bis +15 Punkte

        Rückgabe: {score, rsi, macd, bollinger, signals[]}
        """
        score   = 50
        signals: List[str] = []

        # ── RSI ───────────────────────────────────────────
        rsi_val = cls.rsi(prices)

        if rsi_val < 25:
            score += 25
            signals.append(f"RSI {rsi_val:.0f} — stark überverkauft ↑")
        elif rsi_val < 35:
            score += 18
            signals.append(f"RSI {rsi_val:.0f} — überverkauft ↑")
        elif rsi_val < 45:
            score += 10
            signals.append(f"RSI {rsi_val:.0f} — niedrig")
        elif rsi_val > 80:
            score -= 25
            signals.append(f"RSI {rsi_val:.0f} — stark überkauft ↓")
        elif rsi_val > 70:
            score -= 18
            signals.append(f"RSI {rsi_val:.0f} — überkauft ↓")
        elif rsi_val > 62:
            score -= 8

        # ── MACD ──────────────────────────────────────────
        macd_data = cls.macd(prices)
        hist = macd_data["histogram"]
        ml   = macd_data["macd_line"]
        sl   = macd_data["signal_line"]

        if hist > 0 and ml > sl:
            score += 15
            signals.append("MACD bullisch — über Signal-Linie ↑")
        elif hist > 0:
            score += 8
        elif hist < 0 and ml < sl:
            score -= 15
            signals.append("MACD bearisch — unter Signal-Linie ↓")
        elif hist < 0:
            score -= 8

        # ── Bollinger Bands ───────────────────────────────
        bb = cls.bollinger_bands(prices)
        pb = bb["pct_b"]

        if pb < 0.05:
            score += 20
            signals.append("Bollinger: Kurs am unteren Band ↑")
        elif pb < 0.20:
            score += 12
            signals.append("Bollinger: Kurs nahe unterem Band ↑")
        elif pb < 0.35:
            score += 6
        elif pb > 0.95:
            score -= 15
            signals.append("Bollinger: Kurs am oberen Band ↓")
        elif pb > 0.80:
            score -= 8
            signals.append("Bollinger: Kurs nahe oberem Band ↓")
        elif pb > 0.65:
            score -= 4

        # ── Volume ────────────────────────────────────────
        vol_delta = 0
        if volumes:
            vol_delta, vol_msg = cls.volume_score(volumes)
            score += vol_delta
            if vol_msg:
                signals.append(vol_msg)

        score = max(0, min(100, score))

        return {
            "score":     round(score),
            "rsi":       rsi_val,
            "macd":      macd_data,
            "bollinger": bb,
            "signals":   signals,
        }


# ── SignalGenerator ────────────────────────────────────────────────────────────

class SignalGenerator:
    """
    Erzeugt Handelssignale aus normierten Marktdaten.

    Zwei Eingabewege:
      1. `generate(symbol, name, price, scores, ...)` — nimmt fertig berechnete Scores
      2. `generate_from_prices(symbol, name, prices, fund_scores, ...)` — berechnet
         technische Scores automatisch via TechnicalAnalyzer
    """

    def __init__(self, min_score_threshold: int = 65) -> None:
        self.min_score_threshold = min_score_threshold

    # ── Haupt-API ──────────────────────────────────────────────────────────────

    def generate(
        self,
        symbol: str,
        name: str,
        price: float,
        scores: Dict[str, int],
        stop_loss: Optional[float] = None,
        target_price: Optional[float] = None,
        reasons: Optional[List[str]] = None,
        risks: Optional[List[str]] = None,
        catalyst: Optional[str] = None,
        regime_context: Optional[str] = None,
    ) -> Optional[Signal]:
        """
        Erstellt ein Signal aus vorberechneten Scores.
        Gibt None zurück wenn der Gesamt-Score unter dem Schwellenwert liegt.
        """
        total = self._weighted_total(scores)
        if total < self.min_score_threshold:
            return None

        verdict, strength, confidence = self._classify(total)
        breakdown = ScoreBreakdown(
            fundamental  = scores.get("fundamental",  50),
            technical    = scores.get("technical",    50),
            management   = scores.get("management",   50),
            sentiment    = scores.get("sentiment",    50),
            geopolitical = scores.get("geopolitical", 50),
            macro        = scores.get("macro",        50),
            total        = total,
            verdict      = verdict,
            confidence   = confidence,
        )

        return Signal(
            asset_symbol    = symbol,
            asset_name      = name,
            signal_type     = verdict,
            strength        = strength,
            score           = breakdown,
            price_at_signal = price,
            stop_loss       = stop_loss,
            target_price    = target_price,
            reasons         = reasons or [],
            risks           = risks or [],
            catalyst        = catalyst,
            regime_context  = regime_context,
        )

    def generate_from_prices(
        self,
        symbol: str,
        name: str,
        prices: List[float],
        fund_scores: Dict[str, int],
        volumes: Optional[List[int]] = None,
        sentiment_score: int = 50,
        regime_context: Optional[str] = None,
    ) -> Optional[Signal]:
        """
        Berechnet technische Indikatoren aus Preishistorie und erstellt ein Signal.

        Args:
            symbol:          Ticker-Symbol
            name:            Vollständiger Instrumentenname
            prices:          Preishistorie (mind. 15 Werte, besser 35+)
            fund_scores:     Vordefinierte Scores: {fundamental, management, geopolitical, macro}
            volumes:         Optionale Volumenhistorie
            sentiment_score: Sentiment-Score 0–100 (z.B. aus Fear & Greed)
            regime_context:  Aktuelles Marktregime (Label-String)

        Returns:
            Signal-Objekt oder None wenn Score zu niedrig
        """
        if len(prices) < 5:
            return None

        tech = TechnicalAnalyzer.technical_score(prices, volumes)
        price = prices[-1]

        scores: Dict[str, int] = {
            "fundamental":  fund_scores.get("fundamental",  50),
            "technical":    tech["score"],
            "management":   fund_scores.get("management",   50),
            "sentiment":    sentiment_score,
            "geopolitical": fund_scores.get("geopolitical", 50),
            "macro":        fund_scores.get("macro",        50),
        }

        # Stop-Loss: etwas unter dem unteren Bollinger-Band
        bb = tech["bollinger"]
        stop_loss    = round(bb["lower"] * 0.985, 4) if price > bb["lower"] else round(price * 0.92, 4)
        target_price = round(price + (price - stop_loss) * 2.5, 4)

        reasons = list(tech["signals"])
        if fund_scores.get("fundamental", 0) >= 82:
            reasons.append("Starke Fundamentaldaten")
        if fund_scores.get("management", 0) >= 85:
            reasons.append("Top-Management (Governance-Score > 85)")

        risks: List[str] = []
        if tech["rsi"] > 65:
            risks.append("RSI nähert sich überkauftem Bereich")
        if tech["macd"]["histogram"] < 0:
            risks.append("MACD-Histogramm negativ")

        return self.generate(
            symbol        = symbol,
            name          = name,
            price         = price,
            scores        = scores,
            stop_loss     = stop_loss,
            target_price  = target_price,
            reasons       = reasons,
            risks         = risks,
            regime_context= regime_context,
        )

    def to_event(self, signal: Signal) -> Event:
        """Konvertiert ein Signal in ein Event für den Event-Bus."""
        return Event.signal_generated(
            symbol    = signal.asset_symbol,
            signal_id = signal.id,
            verdict   = signal.signal_type,
            score     = signal.score.total,
        )

    # ── Hilfsmethoden ─────────────────────────────────────────────────────────

    @staticmethod
    def _weighted_total(scores: Dict[str, int]) -> int:
        """Gewichteter Gesamt-Score (muss mit ScoreBreakdown-Validator übereinstimmen)."""
        return round(
            scores.get("fundamental",  50) * 0.25
            + scores.get("technical",  50) * 0.20
            + scores.get("management", 50) * 0.15
            + scores.get("sentiment",  50) * 0.15
            + scores.get("geopolitical", 50) * 0.10
            + scores.get("macro",      50) * 0.15
        )

    @staticmethod
    def _classify(total: int) -> Tuple[SignalType, SignalStrength, SignalConfidence]:
        """Leitet Urteil, Stärke und Konfidenz aus dem Gesamt-Score ab."""
        if total >= 82:
            return SignalType.buy,  SignalStrength.strong,   SignalConfidence.high
        if total >= 75:
            return SignalType.buy,  SignalStrength.strong,   SignalConfidence.medium
        if total >= 65:
            return SignalType.buy,  SignalStrength.moderate, SignalConfidence.medium
        if total >= 55:
            return SignalType.hold, SignalStrength.weak,     SignalConfidence.low
        return SignalType.avoid, SignalStrength.moderate, SignalConfidence.medium
