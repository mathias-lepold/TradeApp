# 🧾 Spickzettel – Claude Code als Finanzanalyst (für Anfänger)

Dieser Spickzettel fasst alles zusammen, was du brauchst, um dieses Projekt zu
verstehen und zu nutzen – ohne Vorwissen. Er dient gleichzeitig als Referenz für
Claude während der Analysen.

---

## 1. Worum geht es?

Claude Code kann mit den richtigen Anweisungen **eigenständig Aktien recherchieren
und analysieren**. Was früher Analysten-Teams und stundenlange Recherche brauchte,
fasst das System hier verständlich und strukturiert zusammen.

Du gibst einen Befehl wie `/analyze NVDA` ein → Claude erstellt einen Ordner mit
mehreren Analysen und einem Gesamt-Report.

---

## 2. Die vier Analyse-Bausteine (Agenten)

| Agent | Was er beantwortet | Einfach gesagt |
|-------|--------------------|----------------|
| **Equity Research** | Was macht das Unternehmen? Wie stark ist es im Markt? | „Ist das ein gutes Geschäft?" |
| **Financial Analysis** | Wie sehen Umsatz, Margen, Schulden, Cashflow aus? Ist die Aktie zu teuer? | „Ist der Preis gerechtfertigt?" |
| **Earnings Review** | Was sagten die letzten Quartalszahlen & das Management? | „Was ist gerade los?" |
| **Model Builder** | Ein einfaches Rechenmodell für den fairen Wert | „Was könnte die Aktie wert sein?" |

### Offizielle Plugins vs. eingebaute Agenten

- **Offizielle Anthropic-Plugins** (Repo: `anthropics/financial-services`):
  ```bash
  claude plugin marketplace add anthropics/financial-services
  claude plugin install financial-analysis@claude-for-financial-services
  claude plugin install equity-research@claude-for-financial-services
  ```
  Liefern Profi-Befehle wie `/dcf`, `/comps`, `/earnings`, `/initiate`, `/thesis`.
  Nutzen z. T. kostenpflichtige Datenanbieter.
- **Eingebaute Agenten** (in diesem Projekt, `.claude/agents/`): kostenlos,
  arbeiten mit Websuche. Der Befehl `/analyze <TICKER>` steuert sie automatisch.

---

## 3. Wichtige Begriffe (Mini-Glossar)

- **Ticker** – Kürzel einer Aktie an der Börse (z. B. `NVDA` für Nvidia, `ASML` für ASML).
- **Umsatz (Revenue)** – Wie viel Geld das Unternehmen einnimmt.
- **Marge** – Wie viel vom Umsatz als Gewinn übrig bleibt (in %).
- **Wachstum** – Wie schnell Umsatz/Gewinn steigen (z. B. „+25 % pro Jahr").
- **KGV (P/E)** – Kurs-Gewinn-Verhältnis. Wie viele Jahresgewinne kostet die Aktie? Hoch = teuer/hohe Erwartungen.
- **KUV (P/S)** – Kurs-Umsatz-Verhältnis. Nützlich bei Firmen mit wenig Gewinn.
- **EV/EBITDA** – Unternehmenswert im Verhältnis zum operativen Gewinn. Gut für Vergleiche.
- **Cashflow** – Tatsächlich geflossenes Geld (schwerer zu „schönen" als der Gewinn).
- **Moat (Burggraben)** – Wettbewerbsvorteil, der Konkurrenz fernhält (Marke, Patente, Netzwerk).
- **Earnings Call** – Telefonkonferenz, in der das Management die Quartalszahlen erklärt.
- **Guidance** – Prognose des Managements für die kommenden Quartale.
- **DCF** – „Discounted Cash Flow": künftige Geldflüsse auf heute abgezinst = fairer Wert.

---

## 4. Wie lese ich den Report?

Nach `/analyze <TICKER>` findest du unter `research/<TICKER>/`:

```
00_REPORT.md            ← Hier zuerst lesen: Gesamteinschätzung + Ampel
01_equity_research.md   ← Geschäftsmodell & Wettbewerb
02_financial_analysis.md← Zahlen & Bewertung
03_earnings_review.md   ← Letzte Quartalszahlen
04_valuation_model.md   ← Bewertungsmodell mit Szenarien
```

Im `00_REPORT.md` gibt es eine einfache **Ampel**:
- 🟢 = interessant / genauer ansehen
- 🟡 = beobachten / abwarten
- 🔴 = aktuell eher uninteressant / zu teuer / zu riskant

> Die Ampel ist eine **Orientierung, keine Kaufempfehlung.**

---

## 5. Häufige Befehle

| Befehl | Wirkung |
|--------|---------|
| `/analyze NVDA` | Komplette Analyse für Nvidia |
| `/analyze ASML` | Komplette Analyse für ASML |
| „Aktualisiere den Earnings Review für AAPL" | Nur ein Baustein neu |
| „Vergleiche NVDA und AMD anhand der Bewertung" | Vergleich aus vorhandenen Analysen |

---

## 6. Goldene Regeln

1. **Zahlen immer mit Datum & Quelle.** Veraltete Zahlen sind gefährlich.
2. **Keine Anlageberatung.** Das System hilft beim Verstehen, nicht beim Entscheiden.
3. **Primärquellen schlagen alles.** Geschäftsbericht & offizielle Filings > Schätzungen.
4. **Unsicherheit benennen.** Wenn Daten fehlen, soll Claude das sagen – nicht raten.
