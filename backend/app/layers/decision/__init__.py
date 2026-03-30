"""
Decision Engine
Verantwortlich für: Finale Handlungsempfehlungen.

Empfängt: Signal + RegimeState + BiasRisk
Produziert: Recommendation

Der Decision Engine ist der einzige Layer der alle anderen Layer kennt.
Er integriert alle Informationen zu einer konkreten, actionable Empfehlung.

Entscheidungslogik:
  1. Signal vorhanden und nicht abgelaufen?
  2. Signal passt zum aktuellen Regime?
  3. Bias-Risiko akzeptabel?
  4. Positionsgrösse regelkonform (1%-Regel, 10%-Limit)?
  5. CRV ≥ 2.0?
  → Recommendation(action=buy/sell/hold, sizing, warnings)
"""
from .engine           import DecisionEngine
from .risk_manager     import RiskManager
from .hypothesis_engine import HypothesisEngine, HypothesisSet, HypothesisScenario

__all__ = ["DecisionEngine", "RiskManager", "HypothesisEngine", "HypothesisSet", "HypothesisScenario"]
