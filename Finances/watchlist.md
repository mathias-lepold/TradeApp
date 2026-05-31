# 👀 Watchlist

## ⭐ Kern-Portfolio (laufende Tiefenanalyse)

Diese Werte werden vom Automatik-Lauf (`scripts/run_analysis.sh`) regelmäßig
per `/analyze` auf aktuellem Stand gehalten.

| Ticker | Unternehmen / Fonds | Typ | Letzte Analyse | Ampel | Notiz |
|--------|---------------------|-----|----------------|-------|-------|
| ASML | ASML Holding | Aktie | – | – | Chip-Lithografie |
| AMZN | Amazon | Aktie | – | – | E-Commerce / Cloud |
| ENR.DE | Siemens Energy | Aktie (DE, Xetra) | – | – | Energietechnik |
| GOOGL | Alphabet (Google) | Aktie | – | – | – |
| SPY | SPDR S&P 500 ETF | ETF | – | – | US-Gesamtmarkt |
| MSFT | Microsoft | Aktie | – | – | – |
| ACLN.SW | Accelleron Industries | Aktie (CH, SIX) | – | – | Turbolader (ABB-Spin-off) |
| TSM | Taiwan Semiconductor | Aktie (ADR) | – | – | Chip-Fertigung |
| V | Visa | Aktie | – | – | Zahlungsverkehr |
| VT | Vanguard Total World Stock | ETF | – | – | Weltmarkt |
| NVDA | Nvidia | Aktie | – | 🟡 | KI-Chips (analysiert 2026-05-31) |
| BN | Brookfield Corporation | Aktie | – | – | Asset Management |

> Die erste Spalte (Ticker) wird vom Skript ausgelesen. Europäische Werte
> tragen das Börsenkürzel (`.DE` = Xetra, `.SW` = SIX), damit `/analyze` sie
> eindeutig findet. Der US-Screener betrifft nur Einzelwerte ohne Suffix.

---

## 🔎 Screening-Funde (vom `/screen`-Befehl)

Hier kannst du interessante Kandidaten aus dem Screener sammeln, die (noch)
nicht zum Kern-Portfolio gehören. Die jeweils aktuelle Roh-Shortlist liegt in
`screen_results/latest_shortlist.txt`.

| Ticker | Unternehmen / Fonds | Strategie | Gefunden | Ampel | Notiz |
|--------|---------------------|-----------|----------|-------|-------|
| – | – | – | – | – | – |
