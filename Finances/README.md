# 📊 Finances – Dein persönlicher KI-Finanzanalyst mit Claude Code

Dieses Projekt verwandelt Claude Code in ein **automatisiertes Aktien-Research-System**.
Mit einem einzigen Befehl wie `/analyze NVDA` erstellt Claude einen kompletten
Research-Ordner mit mehreren tiefgehenden Analysen – Bewertung, Quartalszahlen,
Wettbewerbsvergleich und einem zusammenfassenden Report.

> ⚠️ **Haftungsausschluss:** Dieses Tool dient ausschließlich der **Information und
> Bildung**. Es stellt **keine Anlageberatung** dar. Alle Ausgaben können Fehler
> enthalten. Triff keine Investitionsentscheidungen allein auf Basis dieser
> Analysen. Prüfe Zahlen immer an der Primärquelle (Geschäftsberichte, SEC-Filings).

---

## 🧩 Was steckt drin?

| Datei / Ordner | Zweck |
|----------------|-------|
| `SPICKZETTEL.md` | Anfänger-Referenz: Was kann das System, welche Begriffe muss ich kennen? |
| `MASTER_PROMPT.md` | Der feste Ablauf, nach dem Claude jede Aktie analysiert |
| `.claude/agents/` | Die vier spezialisierten Finanz-Agenten (Subagenten) |
| `.claude/commands/analyze.md` | Der `/analyze <TICKER>`-Befehl, der alles orchestriert |
| `watchlist.md` | Deine beobachteten Aktien |
| `research/` | Hier landen die generierten Reports (pro Ticker ein Ordner) |
| `research/_TEMPLATE/` | Vorlagen für die einzelnen Analyse-Dokumente |
| `scripts/run_analysis.sh` | Headless-Analyse für die Automatisierung auf dem Server |
| `scripts/cron_setup.md` | Anleitung: Analysen automatisch per Cron laufen lassen |

---

## 🚀 Zwei Wege – offizielle Plugins ODER eingebaute Agenten

Dieses Projekt funktioniert auf **zwei Arten**. Du kannst sie auch kombinieren.

### Weg A – Offizielle Anthropic Financial Plugins (wie im Video)

Anthropic stellt offizielle Plugins bereit:
**Repo:** https://github.com/anthropics/financial-services

```bash
# Marketplace hinzufügen
claude plugin marketplace add anthropics/financial-services

# Kern-Plugin (Pflicht) + die für uns relevanten Bundles installieren
claude plugin install financial-analysis@claude-for-financial-services
claude plugin install equity-research@claude-for-financial-services
```

Damit bekommst du u. a. diese Slash-Befehle:

| Befehl | Plugin | Zweck |
|--------|--------|-------|
| `/comps` | financial-analysis | Vergleichbare Unternehmen (Multiples) |
| `/dcf` | financial-analysis | DCF-Bewertung |
| `/3-statement-model` | financial-analysis | 3-Statement-Modell |
| `/competitive-analysis` | financial-analysis | Wettbewerbsposition |
| `/earnings` | equity-research | Analyse nach Quartalszahlen |
| `/earnings-preview` | equity-research | Vorschau vor Quartalszahlen |
| `/initiate` | equity-research | Initiation/Erst-Coverage |
| `/thesis` | equity-research | Investment-These |
| `/catalysts` | equity-research | Katalysatoren verfolgen |
| `/screen` | equity-research | Aktien-Screening |

> Die offiziellen Plugins greifen auf professionelle Datenanbieter
> (Daloopa, Morningstar, S&P Global, FactSet u. a.) zu – teils kostenpflichtig
> bzw. mit eigenem Zugang.

### Weg B – Eingebaute Agenten dieses Projekts (offline, kostenlos)

Falls du **keinen** Zugang zu den offiziellen Daten-Connectoren hast, enthält
dieses Projekt vier eigene Subagenten in `.claude/agents/`, die mit **Websuche**
arbeiten:

1. **`equity-research`** – Geschäftsmodell, Markt, Wettbewerb, Moat, Chancen/Risiken.
2. **`financial-analysis`** – Umsatz, Margen, Wachstum, Cashflow, Multiples (KGV/KUV/EV-EBITDA).
3. **`earnings-reviewer`** – Quartalszahlen & Management-Aussagen aus dem letzten Earnings Call.
4. **`model-builder`** – Einfaches Bewertungsmodell (DCF-Light + Szenarien).

Der Befehl `/analyze <TICKER>` orchestriert diese vier zu einem kompletten Report.

---

## 🔧 Einrichtung (lokal)

1. **Claude Code** installieren (siehe https://code.claude.com/docs).
2. Optional: offizielle Plugins installieren (Weg A oben).
3. In diesem Ordner starten:
   ```bash
   cd Finances
   claude
   ```
4. Claude erkennt die Agenten in `.claude/agents/` und den Befehl
   `.claude/commands/analyze.md` automatisch.
5. Loslegen:
   ```
   /analyze NVDA
   ```

Claude legt dann unter `research/NVDA/` mehrere Analyse-Dateien und einen
`00_REPORT.md` mit der Gesamteinschätzung an.

> 💡 Die eingebauten Agenten nutzen **Websuche**, um aktuelle Zahlen zu beschaffen.
> Aktiviere in Claude Code Web-Zugriff bzw. erlaube die Such-Tools, wenn du danach
> gefragt wirst. Sind die offiziellen Plugins installiert, nutzt der Workflow
> bevorzugt deren Befehle (`/dcf`, `/comps`, `/earnings` …).

---

## 🤖 Automatisierung (Server / Cron)

Damit Claude regelmäßig und automatisch Aktien aus deiner Watchlist prüft und sich
**nur meldet, wenn etwas interessant ist**, lässt du das System auf einem
durchgehend laufenden Server (VPS) per Cronjob laufen.
Die komplette Schritt-für-Schritt-Anleitung findest du in
[`scripts/cron_setup.md`](scripts/cron_setup.md).

---

## 🔻 Screener – die ganze US-Börse durchsuchen

Statt tausende Aktien einzeln zu analysieren, filtert der **Screener** die
US-Börse erst nach harten Kennzahlen und übergibt nur die Top-Kandidaten an die
Tiefenanalyse (Trichter-Prinzip). Vier Strategien stehen bereit:
`quality-growth`, `value`, `dividend`, `momentum`.

```
/screen quality-growth        # Shortlist nach Wachstum+Qualität
/screen value                 # günstig bewertete Aktien
/screen dividend              # solide Dividendenzahler
/screen momentum --etf        # ETFs im Aufwärtstrend
```

Einrichtung (kostenloser API-Key) und Details: siehe **[`STRATEGIEN.md`](STRATEGIEN.md)**.

## 📁 Empfohlener Workflow

```
1. Kern-Portfolio in watchlist.md pflegen  →  laufende Tiefenanalyse
2. /screen <strategie>   →  Shortlist neuer Kandidaten aus der ganzen Börse
3. /analyze <TICKER>     →  research/<TICKER>/ mit Gesamt-Report + Ampel
4. Cronjob hält das Kern-Portfolio aktuell und screent wöchentlich automatisch
   (siehe scripts/cron_setup.md)
```
