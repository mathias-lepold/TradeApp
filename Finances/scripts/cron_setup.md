# ⏰ Automatisierung: Watchlist-Analysen per Cronjob (VPS)

Damit Claude **regelmäßig automatisch** deine Watchlist prüft, lässt du das
Projekt auf einem durchgehend laufenden Server (VPS) per Cronjob laufen.

> Hinweis: Du kannst jeden beliebigen VPS-Anbieter nutzen (Hetzner, Hostinger,
> DigitalOcean, IONOS …). Wähle einen Standort in der EU, wenn dir Datenschutz
> wichtig ist. Dieses Projekt ist anbieter-unabhängig.

---

## 1. Server vorbereiten

Auf dem VPS (Ubuntu/Debian) einmalig einrichten:

```bash
# Node.js (für Claude Code) installieren – je nach Distro ggf. anpassen
sudo apt update && sudo apt install -y nodejs npm git

# Claude Code installieren
npm install -g @anthropic-ai/claude-code   # bzw. offizielles Setup-Skript

# Anmelden (folge dem Login-Flow / Autorisierungscode)
claude
```

## 2. Projekt auf den Server bringen

Variante A – per Git (empfohlen):
```bash
git clone <DEIN-REPO-URL>
cd <repo>/Finances
```

Variante B – per SCP vom lokalen Rechner (Windows PowerShell):
```powershell
scp -r "C:\Users\Mathias Lepold\Source\Finance\*" user@SERVER_IP:/home/user/Finances/
```

## 3. (Optional) Offizielle Plugins auf dem Server installieren
```bash
claude plugin marketplace add anthropics/financial-services
claude plugin install financial-analysis@claude-for-financial-services
claude plugin install equity-research@claude-for-financial-services
```

## 4. Skript testen
```bash
cd /pfad/zu/Finances
bash scripts/run_analysis.sh NVDA      # einzelner Test
bash scripts/run_analysis.sh           # ganze Watchlist
```

## 5. Cronjob einrichten

Crontab öffnen:
```bash
crontab -e
```

Eine Zeile am Ende einfügen. Empfohlenes Setup (zwei Jobs):

```cron
# 1) KERN-PORTFOLIO: jeden Werktag 07:00 die Watchlist auf Stand halten
0 7 * * 1-5 cd /pfad/zu/Finances && set -a && . ./.env && set +a && /usr/bin/bash scripts/run_analysis.sh >> logs/cron.log 2>&1

# 2) SCREENING-TRICHTER: jeden Samstag 06:00 die US-Börse screenen + Top 10 tief analysieren
0 6 * * 6 cd /pfad/zu/Finances && set -a && . ./.env && set +a && /usr/bin/bash scripts/screen_and_analyze.sh quality-growth 10 >> logs/cron.log 2>&1
```

> `. ./.env` lädt deinen `FMP_API_KEY` (für den Screener). Lege dazu im
> Finances-Ordner eine `.env` mit `FMP_API_KEY=dein_key` an (siehe `STRATEGIEN.md`).
> Du kannst die Strategie im zweiten Job wechseln (`value`, `dividend`, `momentum`)
> oder mehrere Zeilen für verschiedene Strategien an unterschiedlichen Tagen anlegen.

Einfacheres Beispiel (nur Kern-Portfolio, einmal pro Woche):
```cron
30 6 * * 1 cd /pfad/zu/Finances && /usr/bin/bash scripts/run_analysis.sh >> logs/cron.log 2>&1
```

Aufbau einer Cron-Zeile:
```
┌ Minute (0-59)
│ ┌ Stunde (0-23)
│ │ ┌ Tag des Monats (1-31)
│ │ │ ┌ Monat (1-12)
│ │ │ │ ┌ Wochentag (0-7, 0 und 7 = Sonntag)
│ │ │ │ │
0 7 * * 1-5   → 07:00 Uhr, Montag–Freitag
```

> 💡 Unsicher bei der Zeile? Lass sie dir von Claude erzeugen:
> „Erstelle eine Cron-Zeile, die `scripts/run_analysis.sh` werktags um 7 Uhr startet."
> Tools wie crontab.guru helfen beim Überprüfen.

## 6. Nur bei interessanten Treffern benachrichtigt werden

`run_analysis.sh` gibt am Ende eine Ampel-Übersicht aus. Um **nur bei 🟢**
eine Nachricht zu bekommen, kannst du das Skript erweitern (z. B. Mail per
`mail`/`msmtp`, Telegram-Bot, Discord-Webhook). Beispiel-Idee:

```bash
GREENS=$(grep -rl '🟢' research/*/00_REPORT.md 2>/dev/null || true)
if [ -n "$GREENS" ]; then
  echo "Interessante Aktien gefunden:" && echo "$GREENS"
  # hier z. B. curl an einen Discord-/Telegram-Webhook
fi
```

---

Damit arbeitet das System **dauerhaft für dich** und meldet sich, wenn eine
Aktie einen genaueren Blick wert ist. Weiterhin gilt: **keine Anlageberatung.**
