#!/usr/bin/env bash
#
# screen_and_analyze.sh - Screening + automatische Tiefenanalyse der Top-Kandidaten.
# Gedacht fuer den Cronjob auf dem Server (siehe scripts/cron_setup.md).
#
# Ablauf:
#   1. node scripts/screen.mjs <strategie>   -> erzeugt screen_results/latest_shortlist.txt
#   2. Fuer die ersten N Ticker daraus:  claude -p "/analyze <TICKER>"
#
# Nutzung:
#   bash scripts/screen_and_analyze.sh [strategie] [anzahl]
#   Beispiel:  bash scripts/screen_and_analyze.sh quality-growth 10
#
# Voraussetzungen: FMP_API_KEY gesetzt, Claude Code installiert & angemeldet.
set -euo pipefail

STRATEGY="${1:-quality-growth}"
TOP="${2:-10}"

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"
mkdir -p logs
LOG="logs/screen_$(date +%Y%m%d_%H%M%S).log"

echo "=== Screening ($STRATEGY) $(date) ===" | tee -a "$LOG"
node scripts/screen.mjs "$STRATEGY" --top "$TOP" >> "$LOG" 2>&1

SHORTLIST="screen_results/latest_shortlist.txt"
if [ ! -s "$SHORTLIST" ]; then
  echo "Keine Shortlist erzeugt - Abbruch (siehe $LOG)." | tee -a "$LOG"
  exit 1
fi

echo "--- Tiefenanalyse der Top $TOP ---" | tee -a "$LOG"
COUNT=0
while IFS= read -r T && [ "$COUNT" -lt "$TOP" ]; do
  [ -z "$T" ] && continue
  echo "Analysiere $T …" | tee -a "$LOG"
  claude -p "/analyze $T" --permission-mode acceptEdits >> "$LOG" 2>&1 \
    || echo "WARN: Analyse fuer $T fehlgeschlagen" | tee -a "$LOG"
  COUNT=$((COUNT + 1))
done < "$SHORTLIST"

echo "=== Fertig. Reports unter research/<TICKER>/00_REPORT.md ===" | tee -a "$LOG"

# 🟢-Treffer hervorheben
echo "" ; echo "=== Interessante Treffer (gruene Ampel) ==="
grep -rl '🟢' research/*/00_REPORT.md 2>/dev/null || echo "  (keine gruenen Treffer in diesem Lauf)"
