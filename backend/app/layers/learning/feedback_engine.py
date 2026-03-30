"""
FeedbackEngine — speichert Empfehlungen, beobachtet Marktreaktion
nach 1/5/20 Tagen und bewertet Ergebnis mit Fehlerklassifikation.

Fehlerarten:
  - wrong_regime       Regime-Einschätzung war falsch
  - wrong_dominance    Dominante Ebene wurde falsch gewichtet
  - wrong_psychology   Psychologie-Faktor unterschätzt
  - wrong_liquidity    Liquiditätsbedingungen fehlbewertet
  - wrong_timing       Richtung korrekt, Timing falsch
  - correct            Empfehlung war korrekt
  - unknown            Fehlerursache unklar
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from app.domain.evaluation import Evaluation


# ── Demo-Datengenerator ────────────────────────────────────────────────────────

def _demo_evaluations() -> List[Evaluation]:
    """
    Generiert realistische Demo-Evaluationen für das Lernsystem-Dashboard.
    In Produktion: Empfehlungen werden gespeichert und nach X Tagen
    mit echten Preisdaten automatisch bewertet.
    """
    now = datetime.utcnow()

    records = [
        {
            "symbol": "NVDA", "predicted_action": "buy",
            "actual_outcome": "price_up_12pct",
            "price_at_recommendation": 875.0,
            "price_after_5d": 980.0, "return_5d_pct": 12.0,
            "accuracy_score": 0.91, "correct": True,
            "error_type": "correct",
            "lesson_learned": "Momentum + niedriger VIX = starkes Kaufsignal bei NVDA",
            "horizon_days": 5,
            "days_ago": 12,
        },
        {
            "symbol": "MSFT", "predicted_action": "hold",
            "actual_outcome": "price_down_6pct",
            "price_at_recommendation": 420.0,
            "price_after_5d": 394.8, "return_5d_pct": -6.0,
            "accuracy_score": 0.35, "correct": False,
            "error_type": "wrong_regime",
            "lesson_learned": "Regime-Wechsel zu Bear-Market nicht rechtzeitig erkannt — Hold statt Reduce",
            "horizon_days": 5,
            "days_ago": 18,
        },
        {
            "symbol": "NOVN", "predicted_action": "accumulate",
            "actual_outcome": "price_up_3pct",
            "price_at_recommendation": 91.5,
            "price_after_5d": 94.2, "return_5d_pct": 3.0,
            "accuracy_score": 0.72, "correct": True,
            "error_type": "correct",
            "lesson_learned": "Defensive Healthcare-Position im volatilen Umfeld bewährt",
            "horizon_days": 5,
            "days_ago": 25,
        },
        {
            "symbol": "ZGLD", "predicted_action": "buy",
            "actual_outcome": "sideways",
            "price_at_recommendation": 182.0,
            "price_after_5d": 181.5, "return_5d_pct": -0.3,
            "accuracy_score": 0.55, "correct": True,
            "error_type": "wrong_timing",
            "lesson_learned": "Gold-Impuls kam 3 Wochen später — Timing zu früh, Richtung korrekt",
            "horizon_days": 5,
            "days_ago": 30,
        },
        {
            "symbol": "NVDA", "predicted_action": "reduce",
            "actual_outcome": "price_up_8pct",
            "price_at_recommendation": 790.0,
            "price_after_5d": 853.2, "return_5d_pct": 8.0,
            "accuracy_score": 0.18, "correct": False,
            "error_type": "wrong_psychology",
            "lesson_learned": "FOMO-Momentum unterschätzt — Markt war in Greed-Modus, nicht bereit für Korrektur",
            "horizon_days": 5,
            "days_ago": 40,
        },
        {
            "symbol": "MSFT", "predicted_action": "buy",
            "actual_outcome": "price_up_5pct",
            "price_at_recommendation": 398.0,
            "price_after_5d": 417.9, "return_5d_pct": 5.0,
            "accuracy_score": 0.84, "correct": True,
            "error_type": "correct",
            "lesson_learned": "RSI-Übertreibung nach unten korrekt als Kaufgelegenheit erkannt",
            "horizon_days": 5,
            "days_ago": 45,
        },
        {
            "symbol": "NOVN", "predicted_action": "sell",
            "actual_outcome": "price_down_4pct",
            "price_at_recommendation": 87.0,
            "price_after_5d": 83.5, "return_5d_pct": -4.0,
            "accuracy_score": 0.79, "correct": True,
            "error_type": "correct",
            "lesson_learned": "Negative Makro-Überraschung + schwaches Sentiment = korrekte Sell-Empfehlung",
            "horizon_days": 5,
            "days_ago": 52,
        },
        {
            "symbol": "ZGLD", "predicted_action": "hold",
            "actual_outcome": "price_up_7pct",
            "price_at_recommendation": 170.0,
            "price_after_5d": 181.9, "return_5d_pct": 7.0,
            "accuracy_score": 0.42, "correct": False,
            "error_type": "wrong_dominance",
            "lesson_learned": "Geopolitischer Schock als dominante Ebene unterschätzt — Gold-Rally nicht antizipiert",
            "horizon_days": 5,
            "days_ago": 60,
        },
        {
            "symbol": "NVDA", "predicted_action": "hold",
            "actual_outcome": "price_down_15pct",
            "price_at_recommendation": 920.0,
            "price_after_5d": 782.0, "return_5d_pct": -15.0,
            "accuracy_score": 0.12, "correct": False,
            "error_type": "wrong_liquidity",
            "lesson_learned": "Liquiditätsstress durch Fed-Signalling führte zu Sell-Off — Liquiditätsebene unterschätzt",
            "horizon_days": 5,
            "days_ago": 70,
        },
        {
            "symbol": "MSFT", "predicted_action": "accumulate",
            "actual_outcome": "price_up_4pct",
            "price_at_recommendation": 410.0,
            "price_after_5d": 426.4, "return_5d_pct": 4.0,
            "accuracy_score": 0.77, "correct": True,
            "error_type": "correct",
            "lesson_learned": "Earnings-Überraschung + stabiles Regime = Accumulate korrekt",
            "horizon_days": 5,
            "days_ago": 78,
        },
    ]

    result = []
    for r in records:
        days_ago = r.pop("days_ago")
        eval_time = now - timedelta(days=days_ago)
        result.append(Evaluation(
            id=str(uuid.uuid4())[:8],
            recommendation_id=str(uuid.uuid4())[:8],
            evaluated_at=eval_time.isoformat(),
            **r,
        ))

    return result


# ── FeedbackEngine ─────────────────────────────────────────────────────────────

class FeedbackEngine:
    """
    In-Memory Feedback-System für Demo-Betrieb.
    Produktion: Evaluationen werden in PostgreSQL gespeichert und täglich
    via Cron-Job mit echten Marktpreisen berechnet.
    """

    def __init__(self) -> None:
        self._evaluations: List[Evaluation] = _demo_evaluations()

    def get_all(self) -> List[Evaluation]:
        return sorted(self._evaluations, key=lambda e: e.evaluated_at or "", reverse=True)

    def get_stats(self) -> Dict:
        evals = self._evaluations
        if not evals:
            return {"total": 0, "accuracy": 0, "by_error_type": {}}

        correct  = [e for e in evals if e.correct]
        by_type: Dict[str, Dict] = {}
        for e in evals:
            et = e.error_type or "unknown"
            if et not in by_type:
                by_type[et] = {"count": 0, "correct": 0, "avg_accuracy": 0.0, "scores": []}
            by_type[et]["count"]  += 1
            by_type[et]["correct"] += 1 if e.correct else 0
            by_type[et]["scores"].append(e.accuracy_score)

        for et, d in by_type.items():
            d["avg_accuracy"] = round(sum(d["scores"]) / len(d["scores"]), 3)
            d["win_rate"]     = round(d["correct"] / d["count"], 3) if d["count"] else 0
            del d["scores"]

        return {
            "total":        len(evals),
            "correct":      len(correct),
            "win_rate":     round(len(correct) / len(evals), 3),
            "avg_accuracy": round(sum(e.accuracy_score for e in evals) / len(evals), 3),
            "by_error_type": by_type,
        }
