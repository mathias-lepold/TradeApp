# TradeApp — Professional Trading Dashboard

> Institutionelle Analyse-Power für Schweizer Privatanleger

## Quick Start (Demo)

Die einfachste Art die App zu sehen: `index.html` direkt im Browser öffnen.
Keine Installation nötig — vollständig funktional als Single-File-App.

```bash
# Einfach öffnen
open index.html
```

## Vollständige Entwicklungs-Installation

### Voraussetzungen
- Node.js 20+
- Python 3.12+
- Docker + Docker Compose
- IBKR TWS / Gateway (für echtes Trading)

### Frontend (React + TypeScript)

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
# → http://localhost:3000
```

### Backend (FastAPI)

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env

# Direkt starten (Development)
uvicorn main:app --reload --port 8000
# → http://localhost:8000/api/docs
```

### Vollständiger Stack (Docker)

```bash
# Environment konfigurieren
cp .env.example .env
# ANTHROPIC_API_KEY eintragen

# Starten
docker-compose up -d

# Logs
docker-compose logs -f backend
```

## Umgebungsvariablen (.env)

```env
# Anthropic Claude API (für KI-Analyse)
ANTHROPIC_API_KEY=sk-ant-...

# IBKR TWS API
IBKR_HOST=127.0.0.1
IBKR_PORT=7497
IBKR_CLIENT_ID=1

# Fundamentaldaten
FMP_API_KEY=...           # Financial Modeling Prep
ALPHA_VANTAGE_KEY=...     # Alpha Vantage Backup

# Nachrichten
NEWS_API_KEY=...

# Datenbank
DATABASE_URL=postgresql+asyncpg://tradeapp:secret@localhost:5432/tradeapp
REDIS_URL=redis://localhost:6379/0

# Auth
SECRET_KEY=your-secret-key-min-32-chars
```

## Technologie-Stack

| Schicht | Technologie | Warum |
|---|---|---|
| Frontend | React 18 + TypeScript + Vite | Schnell, typsicher, grosse Ökosystem |
| Styling | Tailwind CSS + CSS Variables | Design-System, Dark Mode |
| State | Zustand + React Query | Minimal, kein Redux-Overhead |
| Charts | Chart.js + Recharts | Performante Finanz-Charts |
| Backend | FastAPI (Python) | Async, OpenAPI-Docs, Daten-Ökosystem |
| Primäre DB | PostgreSQL | ACID, bewährt, JSON-Support |
| Zeitreihen | InfluxDB | Optimiert für OHLCV-Kursdaten |
| Cache | Redis | Live-Kurse <5ms Latenz |
| Live-Daten | WebSockets | Echtzeitkurse ohne Polling |
| Broker | IBKR TWS API | Trading, Kurse, Portfolio |
| Fundamentals | Financial Modeling Prep | Earnings, KGVs, Balance Sheet |
| KI-Analyse | Anthropic Claude API | Scoring, Chat, Reports |
| Deployment | Docker + Railway/Vercel | CI/CD, Skalierung |

## API-Endpunkte

```
GET    /api/quotes/{symbol}          Echtzeit-Kurs
GET    /api/macro                    Makro-Indikatoren
GET    /api/signals                  Handelssignale
GET    /api/portfolio                Portfolio-Daten
POST   /api/orders/validate          Order-Validierung (1%-Regel, CRV, etc.)
POST   /api/orders/execute           Order via IBKR ausführen
POST   /api/ai/analyze               KI-Analyse via Claude API
GET    /api/journal/stats            Journal-Statistiken & Bias-Analyse
POST   /api/tax/calculate            Schweizer Steuer-Kalkulator
WS     /ws/quotes                    Live-Kurs WebSocket
```

## Funktionen (aktuell implementiert)

- [x] Dashboard mit Echtzeit-Marktübersicht
- [x] Sektor-Heatmap (Finviz-Style) — Sektoren, Kontinente, Länder, Währungen
- [x] Signale mit Score-System (0–100) und CRV-Anzeige
- [x] Portfolio-Tracking mit Performance-Charts
- [x] Makro-Dashboard (Fed, SNB, EZB, Inflation, Arbeitsmarkt)
- [x] Trading-Journal mit Bias-Analyse
- [x] Trade-Modal mit Validierung (1%-Regel, Stempelsteuer, CRV)
- [x] Detail-Panel für jede Position/Marktvariable
- [x] Dark/Light Mode
- [x] KI-Briefings (Tagesbriefing, Signalanalyse)
- [x] FastAPI Backend mit allen Endpunkten
- [x] Docker-Setup (PostgreSQL + Redis + InfluxDB)

## Nächste Entwicklungsschritte

### Phase 2 (geplant)
- [ ] IBKR TWS API Live-Integration
- [ ] Claude API vollständige KI-Analyse
- [ ] WebSocket Live-Kurse
- [ ] Datenbank-Schema + Migrations
- [ ] Auth (JWT + 2FA)

### Phase 3 (geplant)
- [ ] Backtesting-Engine
- [ ] Earnings-Call-Analyse (NLP)
- [ ] Sentiment-Pipeline (NewsAPI + X API)
- [ ] Geopolitik-Frühwarnsystem

### Phase 4 (geplant)
- [ ] Mobile App (React Native)
- [ ] Steuer-Report automatisiert (ESTV)
- [ ] Alternative Daten (Google Trends, SimilarWeb)

## Lizenz

Privates Repository — nur für den persönlichen Gebrauch.
