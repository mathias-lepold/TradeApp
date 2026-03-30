"""
Interpretation Layer
Verantwortlich für: Signal-Generierung, Regime-Erkennung, technische Analyse.

Empfängt: normalisierte Events vom Reality Layer
Produziert: Signal-Objekte + RegimeState

Komponenten:
  - SignalGenerator: Erstellt Handelssignale aus Preis/Indikator-Daten
  - RegimeDetector:  Klassifiziert das aktuelle Marktregime
"""
from .signal_generator   import SignalGenerator
from .regime_detector    import RegimeDetector
from .cycle_engine       import MarketCycleEngine, MarketCycleState, CyclePhase
from .expectation_engine import ExpectationEngine, ExpectationModel
from .feedback_detector  import FeedbackLoopDetector, FeedbackState, FeedbackType

__all__ = [
    "SignalGenerator", "RegimeDetector",
    "MarketCycleEngine", "MarketCycleState", "CyclePhase",
    "ExpectationEngine", "ExpectationModel",
    "FeedbackLoopDetector", "FeedbackState", "FeedbackType",
]
