---
description: Komplette Aktienanalyse für einen Ticker – erstellt einen Research-Ordner mit Equity Research, Finanzanalyse, Earnings Review, Bewertungsmodell und einem Gesamt-Report.
argument-hint: <TICKER> [optional: Firmenname]
---

Du führst jetzt eine **vollständige Aktienanalyse** durch. Folge dem
Master-Prompt-Workflow exakt. Lies dazu zuerst `MASTER_PROMPT.md` und `SPICKZETTEL.md`.

**Zu analysieren:** $ARGUMENTS

## Ablauf (strikt einhalten)

1. **Setup**: Bestimme den Ticker aus `$ARGUMENTS`. Lege den Ordner
   `research/<TICKER>/` an (verwende den Großbuchstaben-Ticker).

2. **Datenstand prüfen**: Stelle sicher, dass du **aktuelle** Daten verwendest.
   Heutiges Datum als Bezugspunkt nehmen. Jede Zahl mit Periode + Quelle versehen.

3. **Vier Bausteine erstellen** – delegiere an die jeweiligen Subagenten
   (bzw. nutze die offiziellen Plugin-Befehle, falls installiert):
   - `equity-research`   → `research/<TICKER>/01_equity_research.md`
   - `financial-analysis`→ `research/<TICKER>/02_financial_analysis.md`  (offiziell: `/comps`, `/dcf`)
   - `earnings-reviewer` → `research/<TICKER>/03_earnings_review.md`      (offiziell: `/earnings`)
   - `model-builder`     → `research/<TICKER>/04_valuation_model.md`      (offiziell: `/dcf`, `/3-statement-model`)

4. **Gesamt-Report** `research/<TICKER>/00_REPORT.md` schreiben – nutze die
   Vorlage aus `research/_TEMPLATE/00_REPORT.md`. Enthält:
   - Kurz-Steckbrief & aktueller Kurs (mit Datum)
   - **Ampel** 🟢/🟡/🔴 mit einem Satz Begründung
   - Die 3 wichtigsten Pro- und die 3 wichtigsten Contra-Punkte
   - Faire Wertspanne aus dem Modell vs. aktueller Kurs
   - Verlinkung der vier Detail-Dateien
   - Standard-Disclaimer (keine Anlageberatung)

5. **Watchlist-Notiz**: Wenn der Ticker in `watchlist.md` steht, ergänze dort
   Datum der letzten Analyse und die Ampel-Farbe.

## Regeln
- **Keine Anlageberatung.** Die Ampel ist Orientierung, keine Empfehlung.
- Bei fehlenden/unsicheren Daten: explizit kennzeichnen, niemals raten.
- Quellen mit Abrufdatum in jeder Datei.
