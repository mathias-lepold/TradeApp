"""
PromptOptimizer — analysiert Fehlerarten aus dem FeedbackEngine
und generiert direkt nutzbare Optimierungsvorschläge als Prompts.

PromptSuggestion Schema:
  category        — welche Ebene betrifft es (regime, dominance, psychology, liquidity, timing)
  problem         — was lief schief
  suggestion_prompt — direkt kopierbarer Prompt zur Systemverbesserung
  priority        — high | medium | low
"""
from __future__ import annotations

from typing import Dict, List
from pydantic import BaseModel

from app.layers.learning.feedback_engine import FeedbackEngine


# ── Schema ────────────────────────────────────────────────────────────────────

class PromptSuggestion(BaseModel):
    id: str
    category: str           # "regime" | "dominance" | "psychology" | "liquidity" | "timing" | "general"
    category_label: str     # Lesbares Label
    problem: str            # Was war das Problem
    suggestion_prompt: str  # Direkt kopierbarer Prompt
    priority: str           # "high" | "medium" | "low"
    based_on_errors: int    # Wie viele Fehler dieser Art liegen zugrunde
    example_case: str       # Konkretes Beispiel aus den Daten


# ── Statische Prompt-Bibliothek ────────────────────────────────────────────────

_PROMPT_LIBRARY: Dict[str, Dict] = {
    "wrong_regime": {
        "category": "regime",
        "category_label": "Regime-Erkennung",
        "problem": "Regime-Wechsel zu spät erkannt — Empfehlung passte nicht zum tatsächlichen Marktumfeld",
        "suggestion_prompt": (
            "Analysiere das aktuelle Marktregime mit folgendem Framework:\n"
            "1. VIX-Trend der letzten 10 Tage (steigend = Regime-Wechsel-Signal)\n"
            "2. Yield-Kurve: 10Y-2Y Spread (< 0 = invertiertert = Warnung)\n"
            "3. Fear & Greed Index Trend (schnelle Richtungsänderung = Regime-Instabilität)\n"
            "4. Frage explizit: 'Könnte sich das Regime in den nächsten 5 Tagen ändern?'\n"
            "5. Wenn Regime-Fragility > 0.6: No-Trade-Flag setzen\n"
            "Wende dies auf die aktuelle Empfehlung an, bevor du eine Aktion vorschlägst."
        ),
        "priority": "high",
        "example_case": "MSFT Hold-Empfehlung ignorierte Regime-Shift zu Bear Market → -6% in 5 Tagen",
    },
    "wrong_dominance": {
        "category": "dominance",
        "category_label": "Dominanz-Analyse",
        "problem": "Dominante Marktebene falsch gewichtet — z.B. Geopolitik ignoriert während Liquidität/Narrativ dominierte",
        "suggestion_prompt": (
            "Führe vor jeder Empfehlung eine Dominanz-Analyse durch:\n"
            "1. Welche der 6 Ebenen dominiert aktuell? (Fundamental / Geopolitik / Liquidität / Psychologie / Mikrostruktur / Narrativ)\n"
            "2. Welche Ebene gewinnt an Einfluss? Welche verliert?\n"
            "3. Wenn Geopolitik oder Liquidität dominant (Score > 0.65): Fundamentalanalyse UNTERGEWICHTEN\n"
            "4. Wenn Narrativ dominant (Score > 0.6): Momentum-Effekt einkalkulieren — kein konträr-Trade\n"
            "5. Finale Empfehlung erst NACH Dominanz-Einschätzung formulieren\n"
            "Beispiel-Trigger: Gold-Rally durch geopolitischen Schock → 'Geopolitik dominant' erklärt +7%"
        ),
        "priority": "high",
        "example_case": "ZGLD Hold statt Buy: Geopolitischer Schock als dominante Ebene nicht erkannt → +7% verpasst",
    },
    "wrong_psychology": {
        "category": "psychology",
        "category_label": "Psychologie & Sentiment",
        "problem": "Psychologische Marktdynamik (FOMO, Greed-Modus) unterschätzt",
        "suggestion_prompt": (
            "Integriere Psychologie-Check in Empfehlungsprozess:\n"
            "1. Fear & Greed Index: > 70 = Greed-Modus → konträr-bullische Empfehlungen zurückhalten\n"
            "2. Wenn F&G > 75 UND Momentum > +5% in 5 Tagen: FOMO-Modus aktiv → kein Reduce/Sell ohne starkes Fundamental-Signal\n"
            "3. Frage: 'Würde ein rationaler Investor JETZT kaufen oder ist es Gruppendenken?'\n"
            "4. RSI > 75 + F&G > 70: Überhitzung — Position halten aber kein Nachkaufen\n"
            "5. Sentiment-Shift schneller als Fundamentals: Narrativ schlägt Fundamental kurzfristig\n"
            "Korrektur-Prompt: 'Bin ich gerade im Greed-Modus? Würde ich diese Aktie auch bei -10% noch kaufen?'"
        ),
        "priority": "medium",
        "example_case": "NVDA Reduce-Empfehlung im Greed-Modus → Markt stieg weitere +8%",
    },
    "wrong_liquidity": {
        "category": "liquidity",
        "category_label": "Liquiditätsanalyse",
        "problem": "Liquiditätsstress nicht als Haupttreiber erkannt — Sell-Off durch Funding-Probleme",
        "suggestion_prompt": (
            "Prüfe Liquiditätsbedingungen vor jeder Kaufempfehlung:\n"
            "1. VIX > 28: Erhöhtes Liquiditätsrisiko — Positionsgrössen reduzieren\n"
            "2. Fed-Rate > 4.5% + steigende Kurve: Tight-Money-Umfeld → Value über Growth\n"
            "3. Forced-Selling-Risk hoch (VIX-Anstieg > 20% in 5 Tagen): Abwarten\n"
            "4. Funding-Conditions 'tight' oder 'stressed': Keine neuen Kaufpositionen\n"
            "5. Liquiditäts-Warnsignal: Bid-Ask-Spreads weiten sich, Volumen sinkt bei fallenden Kursen\n"
            "Regel: Bei Liquiditätsstress immer 50% kleinere Positionsgrösse als berechnet."
        ),
        "priority": "high",
        "example_case": "NVDA Hold während Fed-Signalling führte zu -15% durch Liquiditäts-Sell-Off",
    },
    "wrong_timing": {
        "category": "timing",
        "category_label": "Entry-Timing",
        "problem": "Richtung korrekt, aber Timing zu früh — Signal vor Katalysator ausgelöst",
        "suggestion_prompt": (
            "Verbessere Timing-Präzision mit Bestätigungsfiltern:\n"
            "1. Warte auf Bestätigung durch 2 aufeinanderfolgend höhere Schlusskurse (für Kaufsignale)\n"
            "2. Keine Antizipation von Nachrichten — nur auf bestätigte Preis-Reaktion reagieren\n"
            "3. Für Gold/Rohstoffe: Geopolitische Events haben 10-20 Tage Lag bis zur vollen Einpreisung\n"
            "4. RSI-Kaufsignal < 30: Warte auf RSI > 35 als Bestätigung des Bodens\n"
            "5. Timing-Filter: 'Würde ich in 3 Tagen immer noch kaufen?' — Wenn ja: Kaufen. Wenn nein: Warten.\n"
            "Taktik: Einstieg in 2-3 Tranchen über 5-10 Tage statt Komplettkauf"
        ),
        "priority": "medium",
        "example_case": "ZGLD Buy zu früh — Gold-Rally kam 3 Wochen später durch verzögerten geopolitischen Einfluss",
    },
}


# ── PromptOptimizer ────────────────────────────────────────────────────────────

class PromptOptimizer:

    def __init__(self, feedback_engine: FeedbackEngine) -> None:
        self._fb = feedback_engine

    def generate_suggestions(self) -> List[PromptSuggestion]:
        """
        Analysiert Fehlerarten aus dem FeedbackEngine und gibt priorisierte
        Optimierungsvorschläge zurück.
        """
        stats      = self._fb.get_stats()
        by_type    = stats.get("by_error_type", {})
        suggestions: List[PromptSuggestion] = []

        # Fehlertyp-basierte Vorschläge
        for error_type, data in by_type.items():
            if error_type in ("correct", "unknown"):
                continue

            template = _PROMPT_LIBRARY.get(error_type)
            if not template:
                continue

            count        = data["count"]
            avg_accuracy = data["avg_accuracy"]
            win_rate     = data["win_rate"]

            # Priorität dynamisch anpassen
            priority = template["priority"]
            if count >= 3 and avg_accuracy < 0.4:
                priority = "high"
            elif count == 1 and avg_accuracy > 0.5:
                priority = "low"

            # Suggestion erstellen
            problem_detail = (
                f"{template['problem']} "
                f"({count}× aufgetreten, Ø Accuracy {avg_accuracy:.0%}, "
                f"Trefferquote {win_rate:.0%})"
            )

            suggestions.append(PromptSuggestion(
                id=error_type,
                category=template["category"],
                category_label=template["category_label"],
                problem=problem_detail,
                suggestion_prompt=template["suggestion_prompt"],
                priority=priority,
                based_on_errors=count,
                example_case=template["example_case"],
            ))

        # Allgemeiner Vorschlag wenn Gesamt-Win-Rate niedrig
        total_win_rate = stats.get("win_rate", 1.0)
        if total_win_rate < 0.6 and stats.get("total", 0) >= 5:
            suggestions.append(PromptSuggestion(
                id="general_quality",
                category="general",
                category_label="Allgemeine Qualität",
                problem=(
                    f"Gesamt-Trefferquote {total_win_rate:.0%} unter Zielwert 60% "
                    f"({stats.get('total', 0)} Empfehlungen bewertet)"
                ),
                suggestion_prompt=(
                    "System-Review: Führe eine vollständige Neukalibrierung durch:\n"
                    "1. Überprüfe Min-Score-Schwelle (aktuell 65) — ggf. auf 70 erhöhen\n"
                    "2. Regime-Gewichtung in Decision Engine erhöhen (von 0.3 auf 0.4)\n"
                    "3. No-Trade-Flag Schwelle senken: regime_fragility > 0.6 statt 0.7\n"
                    "4. Backtest mit erhöhten Qualitätsfiltern auf letzten 90 Tagen durchführen\n"
                    "5. Prüfe ob Sector-Rotation-Effekte berücksichtigt werden\n"
                    "Ziel: Min. 65% Trefferquote über Rolling 20-Empfehlungen"
                ),
                priority="high",
                based_on_errors=stats.get("total", 0),
                example_case=f"Letzte {stats.get('total', 0)} Empfehlungen: {total_win_rate:.0%} Trefferquote",
            ))

        # Nach Priorität sortieren
        prio_order = {"high": 0, "medium": 1, "low": 2}
        suggestions.sort(key=lambda s: (prio_order.get(s.priority, 3), -s.based_on_errors))

        return suggestions
