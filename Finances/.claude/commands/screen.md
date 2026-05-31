---
description: Durchsucht die US-Börse nach einer Strategie (quality-growth / value / dividend / momentum), erstellt eine Shortlist und bietet an, die Top-Kandidaten tief zu analysieren.
argument-hint: [quality-growth|value|dividend|momentum] [--etf]
---

Du führst ein **Aktien-/ETF-Screening** durch. Ziel: aus der gesamten US-Börse
schnell eine kurze Liste der interessantesten Kandidaten nach einer Strategie
herausfiltern – als Vorstufe zur Tiefenanalyse (`/analyze`).

**Strategie/Argumente:** $ARGUMENTS  (Standard: `quality-growth`)

## Ablauf

1. Prüfe, ob die Umgebungsvariable `FMP_API_KEY` gesetzt ist. Falls nicht,
   weise freundlich darauf hin (Setup siehe `STRATEGIEN.md`) und stoppe.

2. Führe den Screener aus (er nutzt die FMP-API, kein jq/Python nötig):
   ```bash
   node scripts/screen.mjs $ARGUMENTS
   ```
   Für ETFs hängt der Nutzer `--etf` an.

3. Lies das erzeugte Ergebnis aus `screen_results/` (die neueste Datei) und
   **präsentiere die Shortlist** als übersichtliche Tabelle. Erkläre in 1–2
   Sätzen, was die jeweilige Strategie bevorzugt (siehe `STRATEGIEN.md`).

4. **Biete an**, die Top-Kandidaten direkt tief zu analysieren:
   *„Soll ich die Top 10 jetzt mit `/analyze` durchrechnen? (dauert ~2–3 Std.)
   Oder nur einzelne davon?"*
   Führe die Tiefenanalyse nur nach Bestätigung aus – pro Ticker den
   `/analyze <TICKER>`-Workflow (Reihenfolge: wie in der Shortlist).

## Regeln
- Das Screening ist eine **Vorauswahl anhand harter Zahlen**, keine Empfehlung
  und **keine Anlageberatung**.
- Nenne immer die Datenquelle (FMP) und das Datum.
- Sei sparsam mit API-Calls (die Gratis-Stufe hat ~250 Anfragen/Tag) – nicht
  unnötig mehrfach screenen.
