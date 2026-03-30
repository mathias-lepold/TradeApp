"""
Behavioral Simulation Layer
Verantwortlich für: Erkennung kognitiver Verzerrungen im Trader-Verhalten.

Empfängt: Signal + Trader-Kontext (Trade-History, aktuelle Positionen)
Produziert: BiasRisk-Bewertung für den Decision Engine

Erkannte Biases:
  - FOMO (Fear Of Missing Out): Kauf bei extremer Gier/Allzeithochs
  - Loss Aversion: Zu langes Halten von Verlustpositionen
  - Overconfidence: Zu grosse Positionen nach Gewinnserie
  - Anchoring: Festhalten an historischen Einstiegspreisen
  - Revenge Trading: Sofortiger Wiedereinstieg nach Verlust
  - Recency Bias: Übergewichtung der letzten Marktbewegungen
"""
from .bias_detector import BiasDetector
from .behavioral_scorer import BehavioralScorer

__all__ = ["BiasDetector", "BehavioralScorer"]
