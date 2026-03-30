"""
Behavioral Layer: BiasDetector
Erkennt kognitive Verzerrungen im Trader-Verhalten und bewertet deren Einfluss.

Erkannte Biases:
  FOMO              — Kauf bei Extremgier / nach Kursanstieg
  Loss Aversion     — Halten von Verlustpositionen trotz Verkaufssignal
  Overconfidence    — Übertriebenes Vertrauen nach Gewinnserie
  Revenge Trading   — Schneller Wiedereinstieg nach Verlust
  Recency Bias      — Übergewichtung jüngster Ereignisse
  Confirmation Bias — Suche nach bestätigenden Informationen für bestehende Position
"""
from __future__ import annotations

from typing import List, Optional, Dict
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from app.domain.recommendation import BiasRisk
from app.domain.signal import Signal, SignalType


# ── Daten-Modelle ──────────────────────────────────────────────────────────────

class TradeHistoryEntry(BaseModel):
    """Einzelner Trade für die Bias-Analyse."""
    symbol:         str
    direction:      str           # "buy" / "sell"
    entry_price:    float
    exit_price:     Optional[float] = None
    pnl_chf:        Optional[float] = None
    executed_at:    datetime
    closed_at:      Optional[datetime] = None
    was_profitable: Optional[bool] = None


class TraderContext(BaseModel):
    """Trader-spezifischer Kontext für Bias-Analyse."""
    recent_trades:         List[TradeHistoryEntry] = Field(default_factory=list)
    current_positions:     Dict[str, float]        = Field(
        default_factory=dict,
        description="{symbol: pnl_pct} — aktuelles P&L% pro Position",
    )
    portfolio_value_chf:   float                   = 0.0
    last_trade_result:     Optional[str]           = Field(None, description="'win' oder 'loss'")
    consecutive_wins:      int                     = 0
    consecutive_losses:    int                     = 0
    last_trade_at:         Optional[datetime]      = None


# ── BiasDetector ───────────────────────────────────────────────────────────────

class BiasDetector:
    """
    Analysiert Trader-Verhalten und identifiziert kognitive Verzerrungen.

    Jeder Bias wird mit einer Wahrscheinlichkeit 0.0–1.0 bewertet.
    Der Gesamt-Score (0–100) fließt in die Recommendation ein;
    bei Score > 60 kann der Decision Engine eine Kaufempfehlung zurückhalten.
    """

    BIAS_THRESHOLD = 0.50  # Ab diesem Wert gilt ein Bias als aktiv

    def analyze(
        self,
        signal: Signal,
        context: TraderContext,
        fear_greed_index: int = 50,
    ) -> BiasRisk:
        """
        Hauptmethode: Analysiert Signal + Kontext und gibt BiasRisk zurück.

        Args:
            signal:           Aktuelles Handelssignal
            context:          Trader-Kontext (Trades, Positionen)
            fear_greed_index: Aktueller Fear & Greed Index (0–100)
        """
        detected:   List[str] = []
        warnings:   List[str] = []
        score_parts: List[float] = []

        # ── FOMO ──────────────────────────────────────────
        fomo = self._check_fomo(signal, fear_greed_index, context)
        if fomo > self.BIAS_THRESHOLD:
            detected.append("fomo")
            warnings.append(
                f"FOMO-Risiko: Buy-Signal bei Fear & Greed {fear_greed_index} "
                "— Kauf nahe Allzeithoch möglich"
            )
            score_parts.append(fomo * 30)

        # ── Loss Aversion ─────────────────────────────────
        loss_av = self._check_loss_aversion(signal, context)
        if loss_av > self.BIAS_THRESHOLD:
            detected.append("loss_aversion")
            warnings.append("Loss Aversion: Verlustposition möglicherweise zu lange gehalten")
            score_parts.append(loss_av * 25)

        # ── Overconfidence ────────────────────────────────
        overconf = self._check_overconfidence(context)
        if overconf > self.BIAS_THRESHOLD:
            detected.append("overconfidence")
            warnings.append(
                f"Overconfidence: {context.consecutive_wins} Gewinntrades in Folge "
                "— Positionsgrösse überprüfen"
            )
            score_parts.append(overconf * 20)

        # ── Revenge Trading ───────────────────────────────
        revenge = self._check_revenge_trading(context)
        if revenge > self.BIAS_THRESHOLD:
            detected.append("revenge_trading")
            warnings.append("Revenge Trading: Schneller Wiedereinstieg nach Verlust erkannt")
            score_parts.append(revenge * 35)

        # ── Recency Bias ──────────────────────────────────
        recency = self._check_recency_bias(signal, context)
        if recency > self.BIAS_THRESHOLD:
            detected.append("recency_bias")
            warnings.append(
                "Recency Bias: Entscheidung möglicherweise zu stark "
                "von jüngsten Kursen beeinflusst"
            )
            score_parts.append(recency * 15)

        # ── Confirmation Bias ─────────────────────────────
        confirm = self._check_confirmation_bias(signal, context)
        if confirm > self.BIAS_THRESHOLD:
            detected.append("confirmation_bias")
            warnings.append(
                "Confirmation Bias: Bestehende Verlustposition und neues Buy-Signal "
                "— suchen Sie aktiv nach Gegenargumenten"
            )
            score_parts.append(confirm * 20)

        overall  = min(round(sum(score_parts)), 100)
        adjusted = overall > 50 and signal.signal_type == SignalType.buy

        return BiasRisk(
            overall_score            = overall,
            detected_biases          = detected,
            warnings                 = warnings,
            recommendation_adjusted  = adjusted,
        )

    # ── Einzelne Bias-Checks ───────────────────────────────────────────────────

    @staticmethod
    def _check_fomo(signal: Signal, fear_greed: int, context: TraderContext) -> float:
        """FOMO: Kauf bei extremer Gier oder nach einer Gewinnserie."""
        if signal.signal_type != SignalType.buy:
            return 0.0
        score = 0.0
        if fear_greed > 85:
            score += 0.8
        elif fear_greed > 75:
            score += 0.5
        elif fear_greed > 65:
            score += 0.2
        if context.consecutive_wins >= 3:
            score += 0.2
        return min(score, 1.0)

    @staticmethod
    def _check_loss_aversion(signal: Signal, context: TraderContext) -> float:
        """Loss Aversion: Verkaufs-Signal bei laufender Verlustposition ignoriert."""
        if signal.signal_type not in {SignalType.sell, SignalType.reduce}:
            return 0.0
        pnl = context.current_positions.get(signal.asset_symbol)
        if pnl is None:
            return 0.0
        if pnl < -15:
            return 1.0
        if pnl < -10:
            return 0.9
        if pnl < -5:
            return 0.7
        return 0.0

    @staticmethod
    def _check_overconfidence(context: TraderContext) -> float:
        """Overconfidence steigt nach mehreren Gewinntrades in Folge."""
        wins = context.consecutive_wins
        if wins >= 5:
            return 0.9
        if wins >= 3:
            return 0.65
        if wins >= 2:
            return 0.35
        return 0.0

    @staticmethod
    def _check_revenge_trading(context: TraderContext) -> float:
        """Revenge Trading: Zu früher Wiedereinstieg nach einem Verlust."""
        if context.last_trade_result != "loss" or context.last_trade_at is None:
            return 0.0
        delta = datetime.utcnow() - context.last_trade_at
        if delta < timedelta(hours=1):
            return 1.0
        if delta < timedelta(hours=3):
            return 0.85
        if delta < timedelta(hours=8):
            return 0.55
        if delta < timedelta(hours=24):
            return 0.30
        return 0.0

    @staticmethod
    def _check_recency_bias(signal: Signal, context: TraderContext) -> float:
        """Recency Bias: Gleiche Position zu oft in kurzer Zeit gehandelt."""
        if not context.recent_trades:
            return 0.0
        recent_same = [
            t for t in context.recent_trades[-5:]
            if t.symbol == signal.asset_symbol
        ]
        if len(recent_same) >= 4:
            return 0.8
        if len(recent_same) >= 3:
            return 0.6
        return 0.0

    @staticmethod
    def _check_confirmation_bias(signal: Signal, context: TraderContext) -> float:
        """
        Confirmation Bias: Aktiver Buy-Signal für eine bereits gehaltene Verlustposition.
        Trader sucht nach bestätigenden Informationen um die Fehlentscheidung
        nicht eingestehen zu müssen.
        """
        if signal.signal_type != SignalType.buy:
            return 0.0
        pnl = context.current_positions.get(signal.asset_symbol)
        if pnl is None:
            return 0.0  # keine bestehende Position → kein Confirmation Bias
        # Je tiefer im Minus, desto stärker der Bias
        if pnl < -20:
            return 0.9
        if pnl < -10:
            return 0.75
        if pnl < -5:
            return 0.55
        if pnl < 0:
            return 0.35
        return 0.15  # auch bei Gewinnen: leichte Neigung zur Bestätigung
