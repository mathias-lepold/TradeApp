"""
Evaluation Domain Model — bewertet vergangene Empfehlungen.

Nach 1/5/20 Tagen wird die tatsächliche Kursreaktion mit der
Empfehlung verglichen und eine Accuracy berechnet.
"""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel


class Evaluation(BaseModel):
    """Bewertung einer Einzelempfehlung nach Marktreaktion."""

    id: str
    recommendation_id: str
    symbol: str

    # Was wurde empfohlen
    predicted_action: str          # buy / sell / hold / reduce …

    # Was passierte tatsächlich
    actual_outcome: str            # "price_up_5pct" | "price_down_3pct" | "sideways" …
    price_at_recommendation: float
    price_after_1d: Optional[float] = None
    price_after_5d: Optional[float] = None
    price_after_20d: Optional[float] = None
    return_1d_pct: Optional[float] = None
    return_5d_pct: Optional[float] = None
    return_20d_pct: Optional[float] = None

    # Qualitätsbewertung
    accuracy_score: float          # 0.0 – 1.0 (wie gut war die Empfehlung)
    correct: bool                  # True wenn Richtung stimmte

    # Fehleranalyse
    error_type: Optional[str] = None  # "wrong_regime" | "wrong_dominance" |
                                       # "wrong_psychology" | "wrong_liquidity" |
                                       # "wrong_timing" | "correct" | "unknown"
    lesson_learned: Optional[str] = None  # Kurzer Text was man daraus lernt

    # Metadaten
    evaluated_at: Optional[str] = None
    horizon_days: int = 5         # nach wie vielen Tagen bewertet
