# 👀 Watchlist

## ⭐ Kern-Portfolio (laufende Tiefenanalyse)

Diese Werte werden vom Automatik-Lauf (`scripts/run_analysis.sh`) regelmäßig
per `/analyze` auf aktuellem Stand gehalten.

| Ticker | Unternehmen / Fonds | Typ | Letzte Analyse | Ampel | Trend | Notiz |
|--------|---------------------|-----|----------------|-------|-------|-------|
| ACLN.SW | Accelleron Industries | Aktie (CH, SIX) | 2026-05-31 | 🟡 | ↗ | Turbolader (ABB-Spin-off) |
| AMZN | Amazon | Aktie | 2026-05-31 | 🟢 | ↗ | E-Commerce / Cloud |
| ASML | ASML Holding | Aktie | 2026-05-31 | 🟡 | → | Chip-Lithografie |
| BN | Brookfield Corporation | Aktie | 2026-05-31 | 🟢 | ↗ | Asset Management |
| ENR.DE | Siemens Energy | Aktie (DE, Xetra) | 2026-05-31 | 🟡 | ↗ | Energietechnik |
| GOOGL | Alphabet (Google) | Aktie | 2026-05-31 | 🟢 | ↗ | – |
| MSFT | Microsoft | Aktie | 2026-05-31 | 🟢 | ↗ | – |
| NVDA | Nvidia | Aktie | 2026-05-31 | 🟡 | ↗ | KI-Chips (analysiert 2026-05-31) |
| SPY | SPDR S&P 500 ETF | ETF | 2026-05-31 | 🔴 | ↗ | US-Gesamtmarkt |
| TSM | Taiwan Semiconductor | Aktie (ADR) | 2026-05-31 | 🟡 | ↗ | Chip-Fertigung |
| V | Visa | Aktie | 2026-05-31 | 🟢 | → | Zahlungsverkehr |
| VT | Vanguard Total World Stock | ETF | 2026-05-31 | 🟡 | ↗ | Weltmarkt |

> Die erste Spalte (Ticker) wird vom Skript ausgelesen. Europäische Werte
> tragen das Börsenkürzel (`.DE` = Xetra, `.SW` = SIX), damit `/analyze` sie
> eindeutig findet. Der US-Screener betrifft nur Einzelwerte ohne Suffix.
>
> **Ampel:** 🟢 günstig/solide · 🟡 fair bis teuer · 🔴 erhöhtes Risiko.
> **Trend:** ↗ aufwärts · → seitwärts · ↘ abwärts. Beides ist eine
> Kurz-Orientierung (Stand der Spalte „Letzte Analyse"), **keine Anlageberatung**;
> eine echte Tiefenanalyse liefert `/analyze <Ticker>` (überschreibt die Ampel).

---

## 🔎 Screening-Funde (vom `/screen`-Befehl)

Hier kannst du interessante Kandidaten aus dem Screener sammeln, die (noch)
nicht zum Kern-Portfolio gehören. Die jeweils aktuelle Roh-Shortlist liegt in
`screen_results/latest_shortlist.txt`.

| Ticker | Unternehmen / Fonds | Strategie | Gefunden | Ampel | Notiz |
|--------|---------------------|-----------|----------|-------|-------|
| – | – | – | – | – | – |
