#!/usr/bin/env bash
#
# run_analysis.sh – Headless-Aktienanalyse für die Automatisierung (VPS/Cron).
#
# Liest die Ticker aus watchlist.md, lässt Claude Code jede Aktie analysieren
# und meldet sich am Ende mit einer Zusammenfassung. Gedacht für den Einsatz
# per Cronjob auf einem durchgehend laufenden Server.
#
# Voraussetzungen:
#   - Claude Code installiert und angemeldet (claude --version funktioniert)
#   - Dieses Skript wird aus dem Finances-Projektordner heraus ausgeführt
#
# Nutzung:
#   bash scripts/run_analysis.sh                 # alle Ticker aus watchlist.md
#   bash scripts/run_analysis.sh NVDA ASML       # nur diese Ticker
#
set -euo pipefail

# In den Projekt-Root wechseln (ein Verzeichnis über diesem Skript)
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

LOG_DIR="$PROJECT_DIR/logs"
mkdir -p "$LOG_DIR"
RUN_LOG="$LOG_DIR/run_$(date +%Y%m%d_%H%M%S).log"

# Ticker bestimmen: entweder aus den Argumenten oder aus watchlist.md
if [ "$#" -gt 0 ]; then
  TICKERS=("$@")
else
  # Erste Spalte der Markdown-Tabelle in watchlist.md auslesen.
  # Nimmt Zeilen wie "| NVDA | ..." und filtert Kopf-/Trennzeilen heraus.
  mapfile -t TICKERS < <(
    grep -E '^\|' watchlist.md \
      | sed -E 's/^\|[[:space:]]*([A-Z0-9.\-]+)[[:space:]]*\|.*/\1/' \
      | grep -E '^[A-Z0-9.\-]+$' \
      | grep -vE '^(Ticker)$'
  )
fi

if [ "${#TICKERS[@]}" -eq 0 ]; then
  echo "Keine Ticker gefunden (weder als Argument noch in watchlist.md)." | tee -a "$RUN_LOG"
  exit 1
fi

echo "=== Analyse-Lauf $(date) ===" | tee -a "$RUN_LOG"
echo "Ticker: ${TICKERS[*]}" | tee -a "$RUN_LOG"

for T in "${TICKERS[@]}"; do
  echo "--- Analysiere $T ---" | tee -a "$RUN_LOG"
  # Headless: Claude Code ohne interaktive Sitzung mit dem analyze-Workflow füttern.
  # --permission-mode acceptEdits, damit Dateien ohne Rückfrage geschrieben werden.
  claude -p "/analyze $T" \
    --permission-mode acceptEdits \
    >> "$RUN_LOG" 2>&1 || echo "WARN: Analyse für $T fehlgeschlagen" | tee -a "$RUN_LOG"
done

echo "=== Fertig. Reports unter research/<TICKER>/00_REPORT.md ===" | tee -a "$RUN_LOG"
echo "Log: $RUN_LOG"

# Optional: nur 🟢-Treffer herausfiltern und z. B. per Mail/Notification melden.
# Hier nur eine einfache Konsolen-Zusammenfassung:
echo ""
echo "=== Ampel-Übersicht ==="
for T in "${TICKERS[@]}"; do
  REPORT="research/$T/00_REPORT.md"
  if [ -f "$REPORT" ]; then
    LIGHT=$(grep -oE '🟢|🟡|🔴' "$REPORT" | head -n1 || true)
    echo "  $T: ${LIGHT:-?}"
  fi
done
