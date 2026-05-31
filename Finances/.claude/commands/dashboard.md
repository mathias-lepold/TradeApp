---
description: Baut ein übersichtliches HTML-Dashboard – Kern-Portfolio plus durchsuchbare Liste ALLER US-Aktien (anklickbar für Details). Für PC & iPhone.
argument-hint: [optionaler Ausgabepfad, z.B. dein OneDrive-Ordner]
---

Du erstellst das **Finanz-Dashboard** – eine einzige, in sich geschlossene
HTML-Datei mit:
1. dem **Kern-Portfolio** (Ampeln, faire Spannen, Pro/Contra aus den Analysen)
2. einem **Markt-Explorer**: alle US-Aktien (1 FMP-Abruf), durchsuchbar/sortierbar,
   anklickbar → Detailkarte mit allen Kennzahlen + fertigem `/analyze`-Befehl.

## Ablauf
1. Stelle sicher, dass `FMP_API_KEY` verfügbar ist (Umgebungsvariable oder `.env`).
   Ohne Key wird nur das Portfolio gebaut, die US-Liste bleibt leer.
2. Führe den Generator aus:
   ```bash
   node scripts/build_dashboard.mjs $ARGUMENTS
   ```
   - Ohne Argument → `dashboard.html` im Projektordner.
   - Mit Pfad-Argument → schreibt direkt dorthin (z.B. den OneDrive-Ordner fürs iPhone).
   - `--mock` → Demo ohne API-Key (zum Anschauen).
3. Sag dem Nutzer kurz, wie viele Portfolio-Werte und US-Aktien enthalten sind
   und wo die Datei liegt.

## Nutzungshinweis an den Nutzer
- **PC:** Datei doppelklicken → Browser.
- **iPhone:** Datei in OneDrive legen, in Safari öffnen, „Teilen → Zum
  Home-Bildschirm" für ein App-Icon.
- Tiefe Kennzahlen je Aktie entstehen erst per `/analyze <TICKER>`; danach
  `/dashboard` erneut bauen, dann erscheint die volle Auswertung in der Liste.

Keine Anlageberatung.
