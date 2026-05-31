# 📂 research/

Hier landen die generierten Analysen. Pro Ticker entsteht ein Unterordner:

```
research/
  _TEMPLATE/              ← Vorlagen (nicht löschen)
    00_REPORT.md
  NVDA/                   ← Beispielergebnis nach /analyze NVDA
    00_REPORT.md          ← zuerst lesen: Gesamteinschätzung + Ampel
    01_equity_research.md
    02_financial_analysis.md
    03_earnings_review.md
    04_valuation_model.md
```

Die Ordner pro Ticker werden automatisch erstellt. Du kannst sie gefahrlos
löschen – eine neue `/analyze`-Ausführung legt sie neu an.
