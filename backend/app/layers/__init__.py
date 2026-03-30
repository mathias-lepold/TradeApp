"""
Trading App — Modulare Layer-Architektur

Datenfluss:
  Reality Layer
      ↓  (Rohdaten → normalisierte Events)
  Interpretation Layer
      ↓  (Events → Signals + RegimeState)
  Behavioral Simulation Layer
      ↓  (Trader-Profil + Signal → BiasRisk)
  Decision Engine
      ↓  (Signal + Regime + Bias → Recommendation)
"""
