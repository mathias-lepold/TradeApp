"""
DominanceEngine — erkennt welche der 6 Marktebenen aktuell dominant ist.

Die 6 Ebenen:
  1. fundamental   — Gewinne, Bewertungen, Wachstum
  2. geopolitical  — Geopolitik, Makropolitik, Zentralbanken
  3. liquidity     — Liquidität, Funding-Konditionen, Marktstruktur
  4. psychology    — Stimmung, Bias, Fear & Greed
  5. microstructure — Technische Signale, Momentum, Volumen
  6. narrative     — Narrative, Themen, Medien-Hype

Erkennt Dominanzwechsel und berechnet Trend (gaining/losing).
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)


# ── Pydantic Schema ───────────────────────────────────────────────────────────

class DominanceState(BaseModel):
    dominant_layer: str                  # z.B. "geopolitical"
    dominant_label: str                  # z.B. "Geopolitik"
    dominance_strength: float            # 0.0 – 1.0
    layer_scores: Dict[str, float]       # Scores je Ebene (0–1)
    gaining_layers: List[str]            # Ebenen mit zunehmendem Einfluss
    losing_layers: List[str]             # Ebenen mit abnehmendem Einfluss
    narrative_explanation: str           # z.B. "Geopolitik dominiert, verliert jedoch Einfluss…"
    assessed_at: Optional[str] = None


# ── Label-Map ─────────────────────────────────────────────────────────────────

_LAYER_LABELS: Dict[str, str] = {
    "fundamental":   "Fundamentaldaten",
    "geopolitical":  "Geopolitik/Makro",
    "liquidity":     "Liquidität",
    "psychology":    "Psychologie",
    "microstructure": "Mikrostruktur",
    "narrative":     "Narrativ",
}


# ── Engine ────────────────────────────────────────────────────────────────────

class DominanceEngine:
    """
    Bewertet die relative Dominanz der 6 Marktebenen aus verfügbaren
    Eingangssignalen und leitet Trendrichtung ab.
    """

    # Inneres State für Trend-Tracking (letzte Scores)
    _prev_scores: Optional[Dict[str, float]] = None

    def assess(
        self,
        *,
        vix: float = 20.0,
        fear_greed: float = 50.0,
        yield_curve: float = 0.0,
        fed_rate: float = 3.0,
        rsi_avg: float = 50.0,
        volume_ratio: float = 1.0,   # aktuelles Volumen / 20-Tage-Durchschnitt
        momentum_5d: float = 0.0,    # 5-Tage-Kursveränderung in %
        macro_surprise: float = 0.0, # Abweichung Makro-Konsensus (positiv = besser als erwartet)
        fund_score_avg: float = 75.0,
        narrative_intensity: float = 0.5,  # 0–1, extern oder geschätzt
        regime_type: str = "bull_market",
    ) -> DominanceState:
        """
        Berechnet einen Score 0–1 für jede der 6 Ebenen.
        Gibt DominanceState zurück mit Dominanz-Leader, Stärke und Trend.
        """
        scores: Dict[str, float] = {}

        # ── 1. Fundamental ──
        # Hoher Fund-Score + positive Makro-Überraschung → fundamental dominant
        fund_base = (fund_score_avg - 50) / 50  # normiert auf -1…+1
        macro_boost = max(-1.0, min(1.0, macro_surprise / 3))
        scores["fundamental"] = round(
            max(0.0, min(1.0, 0.5 + fund_base * 0.35 + macro_boost * 0.15)), 3
        )

        # ── 2. Geopolitisch/Makro ──
        # Inverse Yield-Kurve + hohe Zinsraten + Krisenregime → geo dominant
        yield_stress = 1.0 if yield_curve < -0.2 else (0.5 if yield_curve < 0.1 else 0.2)
        rate_stress = min(1.0, fed_rate / 6.0)
        crisis_boost = 0.3 if "crisis" in regime_type else 0.0
        scores["geopolitical"] = round(
            min(1.0, 0.25 + yield_stress * 0.35 + rate_stress * 0.25 + crisis_boost), 3
        )

        # ── 3. Liquidität ──
        # Hoher VIX + tightening-Umfeld → Liquiditäts-Stress dominant
        vix_norm = min(1.0, max(0.0, (vix - 15) / 45))
        scores["liquidity"] = round(
            min(1.0, 0.1 + vix_norm * 0.6 + rate_stress * 0.25), 3
        )

        # ── 4. Psychologie ──
        # Fear & Greed Extreme (< 25 oder > 75) + Krisenregime
        fg_deviation = abs(fear_greed - 50) / 50  # 0 = neutral, 1 = extreme
        psych_base = 0.2 + fg_deviation * 0.6
        if "crisis" in regime_type or "bear" in regime_type:
            psych_base = min(1.0, psych_base + 0.2)
        scores["psychology"] = round(min(1.0, psych_base), 3)

        # ── 5. Mikrostruktur ──
        # Hohes Volumen + starkes Momentum + extreme RSI → Marktstruktur dominant
        vol_signal = min(1.0, max(0.0, (volume_ratio - 0.8) / 1.5))
        mom_signal = min(1.0, abs(momentum_5d) / 8)
        rsi_signal = abs(rsi_avg - 50) / 50
        scores["microstructure"] = round(
            min(1.0, 0.15 + vol_signal * 0.35 + mom_signal * 0.35 + rsi_signal * 0.15), 3
        )

        # ── 6. Narrativ ──
        # Extern geliefert oder approximiert aus Hype-Indikatoren
        narrative_base = max(0.0, min(1.0, narrative_intensity))
        # Booste wenn Momentum sehr hoch aber Fundamentals nicht rechtfertigen
        if abs(momentum_5d) > 5 and fund_score_avg < 60:
            narrative_base = min(1.0, narrative_base + 0.3)
        scores["narrative"] = round(narrative_base, 3)

        # ── Dominanz ermitteln ──
        dominant_layer = max(scores, key=lambda k: scores[k])
        dominance_strength = scores[dominant_layer]

        # ── Trend: gaining / losing (Vergleich mit letztem Aufruf) ──
        gaining: List[str] = []
        losing: List[str] = []
        if self._prev_scores:
            for layer, score in scores.items():
                delta = score - self._prev_scores.get(layer, score)
                if delta > 0.03:
                    gaining.append(layer)
                elif delta < -0.03:
                    losing.append(layer)

        # Scores speichern für nächsten Aufruf
        self._prev_scores = dict(scores)

        logger.debug(
            "DominanceEngine: dominant=%s (%.0f%%) gaining=%s losing=%s",
            dominant_layer, dominance_strength * 100, gaining, losing,
        )

        # ── Narrative Erklärung ──
        label = _LAYER_LABELS.get(dominant_layer, dominant_layer)
        explanation = self._build_explanation(
            dominant_layer, label, dominance_strength,
            gaining, losing, scores, regime_type, vix, fear_greed
        )

        return DominanceState(
            dominant_layer=dominant_layer,
            dominant_label=label,
            dominance_strength=round(dominance_strength, 3),
            layer_scores=scores,
            gaining_layers=gaining,
            losing_layers=losing,
            narrative_explanation=explanation,
        )

    # ── Private: Erklärungstext ───────────────────────────────────────────────

    def _build_explanation(
        self,
        dominant: str,
        label: str,
        strength: float,
        gaining: List[str],
        losing: List[str],
        scores: Dict[str, float],
        regime_type: str,
        vix: float,
        fear_greed: float,
    ) -> str:
        strength_word = (
            "stark" if strength > 0.7
            else "moderat" if strength > 0.45
            else "schwach"
        )

        # Zweit-dominante Ebene
        sorted_layers = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        second = sorted_layers[1][0] if len(sorted_layers) > 1 else None
        second_label = _LAYER_LABELS.get(second, second) if second else None

        parts: List[str] = [
            f"{label} {strength_word} dominant (Score {strength:.0%})"
        ]

        if second_label:
            parts.append(f"gefolgt von {second_label} ({scores[second]:.0%})")

        if gaining:
            g_labels = [_LAYER_LABELS.get(g, g) for g in gaining[:2]]
            parts.append(f"zunehmend: {', '.join(g_labels)}")

        if losing:
            l_labels = [_LAYER_LABELS.get(l, l) for l in losing[:2]]
            parts.append(f"abnehmend: {', '.join(l_labels)}")

        # Kontextuelle Hinweise
        if vix > 30:
            parts.append("erhöhter VIX deutet auf Risiko-Off-Umfeld")
        if fear_greed < 25:
            parts.append("extreme Angst im Markt")
        elif fear_greed > 75:
            parts.append("extreme Gier — Überhitzungsrisiko")

        return " · ".join(parts) + "."
