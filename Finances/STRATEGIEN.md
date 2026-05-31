# 🎯 Screening-Strategien & Einrichtung

Dieses Dokument erklärt den **Screener** (`/screen`) – das Werkzeug, das die
ganze US-Börse nach Kennzahlen durchsucht und dir eine kurze Kandidatenliste
liefert. Nur die Top-Kandidaten gehen danach in die teure Tiefenanalyse.

> ⚠️ Screening = schnelle Vorauswahl anhand harter Zahlen. **Keine Empfehlung,
> keine Anlageberatung.** Die eigentliche Prüfung macht `/analyze`.

---

## 1. Einmalige Einrichtung: kostenloser API-Key

Der Screener braucht Finanzdaten der ganzen Börse. Quelle: **Financial Modeling
Prep (FMP)** – es gibt eine kostenlose Stufe (~250 Anfragen/Tag).

1. Konto anlegen: https://site.financialmodelingprep.com/developer/docs
2. Den **API-Key** kopieren.
3. Key hinterlegen – zwei Wege:

   **a) Schnell (Git Bash / pro Sitzung):**
   ```bash
   export FMP_API_KEY="dein_key_hier"
   ```

   **b) Dauerhaft (empfohlen):** Lege im `Finances`-Ordner eine Datei `.env` an:
   ```
   FMP_API_KEY=dein_key_hier
   ```
   und lade sie vor dem Start:
   ```bash
   set -a; source .env; set +a
   ```
   (`.env` ist in `.gitignore` – dein Key landet **nicht** auf GitHub.)

4. Test:
   ```bash
   node scripts/screen.mjs quality-growth --top 5
   ```

---

## 2. Die vier Strategien

| Strategie | Sucht nach … | Bevorzugt Kennzahlen |
|-----------|--------------|----------------------|
| `quality-growth` | profitablen Wachstumsfirmen | hohes Umsatzwachstum, hohe ROE, hohe Nettomarge |
| `value` | günstig bewerteten Firmen | niedriges KGV & KBV, positive Gewinne, solide ROE |
| `dividend` | verlässlichen Dividendenzahlern | Div.-Rendite 1,5–12 %, tragfähige Ausschüttungsquote |
| `momentum` | Aktien im Aufwärtstrend | starke 3-/6-/12-Monats-Kursentwicklung |

Hard-Filter für alle (Einzelaktien): US-Börse (NASDAQ/NYSE), aktiv gehandelt,
Marktkapitalisierung > 2 Mrd. $ (keine spekulativen Micro-Caps).

---

## 3. Nutzung

**In Claude Code (interaktiv):**
```
/screen quality-growth
/screen value
/screen dividend
/screen momentum
/screen momentum --etf      ← ETFs statt Einzelaktien
```
Claude zeigt dir die Shortlist und fragt, ob die Top-Kandidaten tief analysiert
werden sollen.

**Direkt im Terminal (ohne Claude):**
```bash
node scripts/screen.mjs value --top 15
```

**Automatisch (Screening + Tiefenanalyse Top 10):**
```bash
bash scripts/screen_and_analyze.sh quality-growth 10
```

---

## 4. Realistische Erwartung (wichtig!)

- Eine Tiefenanalyse dauert ~15 Min. **Top 10 ≈ 2–3 Stunden** Rechenzeit.
- Auf **Claude Pro** ist das machbar, kann aber das Nutzungslimit treffen.
  Für intensiven Dauerbetrieb (großes Kern-Portfolio + tägliches Screening)
  lohnt sich ein höheres Abo oder das Verteilen über die Woche (siehe
  `scripts/cron_setup.md`).
- Der Screener ist eine **v1** mit klaren, nachvollziehbaren Regeln. Die
  Schwellenwerte in `scripts/screen.mjs` kannst du jederzeit anpassen.
