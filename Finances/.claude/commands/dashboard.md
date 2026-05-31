---
description: Baut aus Watchlist, Analyse-Reports und letztem Screening ein übersichtliches HTML-Dashboard (für PC & iPhone).
argument-hint: [optionaler Ausgabepfad, z.B. dein OneDrive-Ordner]
---

Du erstellst das **Finanz-Dashboard** – eine einzige, in sich geschlossene
HTML-Datei mit dem Überblick über das Kern-Portfolio (Ampeln, Kurse, faire
Spannen) und das letzte Screening.

## Ablauf
1. Führe den Generator aus:
   ```bash
   node scripts/build_dashboard.mjs $ARGUMENTS
   ```
   Ohne Argument entsteht `dashboard.html` im Projektordner. Mit Argument
   schreibt er direkt an den angegebenen Pfad (z.B. den OneDrive-Ordner fürs iPhone).

2. Bestätige dem Nutzer kurz, wie viele Werte enthalten sind und wo die Datei liegt.

3. Weise auf die Nutzung hin:
   - **PC:** Datei doppelklicken → öffnet im Browser.
   - **iPhone:** Datei in den OneDrive-Ordner legen, in der OneDrive-App/Safari
     öffnen, dann „Teilen → Zum Home-Bildschirm" für ein App-Icon.

## Hinweis
Das Dashboard ist eine Momentaufnahme. Nach neuen Analysen (`/analyze`) oder
einem Screening (`/screen`) einfach erneut bauen, damit es aktuell ist.
Keine Anlageberatung.
