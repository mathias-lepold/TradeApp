"""
Behavioral Layer: BehavioralScorer
Aggregiert Bias-Analyse zu einem einzigen Trader-Qualitäts-Score.
Auch: Verfolgt Bias-Statistiken über Zeit (für Journal-View).
"""
from __future__ import annotations

from typing import List, Dict
from collections import Counter

from app.domain.recommendation import BiasRisk


class BehavioralScorer:
    """
    Berechnet den Behavioral Quality Score eines Traders
    und aggregiert Bias-Statistiken für das Journal.

    Score-Bedeutung:
      80–100: Disziplinierter Trader — kaum Bias-Einfluss
      60–79:  Guter Trader — gelegentliche Biases
      40–59:  Entwicklungspotential — mehrere Biases aktiv
      0–39:   Hohes Bias-Risiko — emotionales Trading
    """

    def quality_score(self, bias_risk: BiasRisk) -> int:
        """Kehrt den Bias-Score um → 0 Bias = 100 Qualität."""
        return max(0, 100 - bias_risk.overall_score)

    def aggregate_stats(self, bias_history: List[BiasRisk]) -> Dict:
        """
        Aggregiert eine Liste von BiasRisk-Objekten zu Statistiken.
        Ausgabe geeignet für den Journal-Endpoint.
        """
        if not bias_history:
            return {
                "total_analyzed": 0,
                "bias_counts": {},
                "avg_bias_score": 0,
                "avg_quality_score": 100,
                "most_common_bias": None,
                "estimated_cost_opportunity": 0.0,
            }

        all_biases = [b for bh in bias_history for b in bh.detected_biases]
        counts = Counter(all_biases)
        avg_bias = round(sum(bh.overall_score for bh in bias_history) / len(bias_history))
        avg_quality = 100 - avg_bias

        return {
            "total_analyzed": len(bias_history),
            "bias_counts": dict(counts),
            "avg_bias_score": avg_bias,
            "avg_quality_score": avg_quality,
            "most_common_bias": counts.most_common(1)[0][0] if counts else None,
            "bias_adjusted_decisions": sum(1 for bh in bias_history if bh.recommendation_adjusted),
        }

    @staticmethod
    def format_bias_label(bias_key: str) -> str:
        """Konvertiert internen Bias-Key zu lesbarem Label."""
        labels = {
            "fomo": "FOMO",
            "loss_aversion": "Loss Aversion",
            "overconfidence": "Overconfidence",
            "revenge_trading": "Revenge Trading",
            "recency_bias": "Recency Bias",
            "anchoring": "Anchoring",
        }
        return labels.get(bias_key, bias_key.replace("_", " ").title())
