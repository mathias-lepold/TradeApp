# TradeApp — Professional Trading Dashboard

> Institutionelle Analyse-Power für Schweizer Privatanleger

## Quick Start (Demo)

Die einfachste Art die App zu sehen: `index.html` direkt im Browser öffnen.
Keine Installation nötig — vollständig funktional als Single-File-App.

```bash
open index.html
```

---

## Vollständiger Stack starten

### Voraussetzungen

- Docker + Docker Compose
- Python 3.12+
- Node.js 20+

### 1. Infrastructure starten (PostgreSQL + Redis)

```bash
# Im Root-Verzeichnis
docker-compose up -d postgres redis

# Status prüfen
docker-compose ps
# postgres   running (healthy)
# redis      running (healthy)
```

### 2. Backend-Abhängigkeiten installieren

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Datenbank-Migration ausführen

```bash
# Im backend/ Verzeichnis (venv aktiv)
alembic upgrade head

# Ausgabe:
# INFO  [alembic.runtime.migration] Running upgrade  -> 001, Initial migration
```

### 4. Backend starten

```bash
# Im backend/ Verzeichnis (venv aktiv)
uvicorn app.main:app --reload --port 8000

# API-Docs: http://localhost:8000/api/docs
# Health:   http://localhost:8000/api/health
```

### 5. Frontend starten

```bash
cd frontend
npm install
npm run dev

# → http://localhost:5173
```

---

## Vollständiger Docker-Stack

```bash
# Alle Services (inkl. Frontend + Backend als Container)
docker-compose up -d

# Logs beobachten
docker-compose logs -f backend

# Stoppen
docker-compose down
```

---

## Umgebungsvariablen

Datei: `backend/.env`

```env
# Anthropic Claude API
ANTHROPIC_API_KEY=sk-ant-...

# IBKR TWS API
IBKR_HOST=127.0.0.1
IBKR_PORT=7497
IBKR_CLIENT_ID=2

# Datenbank (Docker)
DATABASE_URL=postgresql+asyncpg://trader:tradepass@localhost:5432/tradeapp
REDIS_URL=redis://localhost:6379/0

# Sicherheit
SECRET_KEY=min-32-zeichen-langer-geheimer-schluessel

# Externe APIs (optional)
FMP_API_KEY=
ALPHA_VANTAGE_KEY=
NEWS_API_KEY=
```

---

## Datenbankmigrationen (Alembic)

```bash
cd backend

# Aktuelle Version anzeigen
alembic current

# Alle Migrationen ausführen
alembic upgrade head

# Zur vorherigen Version zurück
alembic downgrade -1

# Neue Migration generieren (nach Modelländerungen)
alembic revision --autogenerate -m "Beschreibung der Änderung"
```

---

## Services & Ports

| Service    | Port | Beschreibung                    |
|------------|------|---------------------------------|
| Frontend   | 5173 | React Dev Server (Vite)         |
| Backend    | 8000 | FastAPI (uvicorn)               |
| PostgreSQL | 5432 | Primärdatenbank                 |
| Redis      | 6379 | Live-Kurs Cache (<5ms Latenz)   |
| InfluxDB   | 8086 | Zeitreihen-Kursdaten (optional) |

---

## API-Endpunkte

```
GET  /api/health                     Health-Check (DB + Redis)
GET  /api/quotes/{symbol}            Echtzeit-Kurs (Redis-Cache)
GET  /api/macro                      Makro-Indikatoren
GET  /api/signals                    Handelssignale
GET  /api/signals/{symbol}           Signal für ein Symbol
GET  /api/regime                     Marktregime
GET  /api/portfolio                  Portfolio-Daten
POST /api/orders/validate            Order-Validierung (1%-Regel, CRV)
POST /api/orders/execute             Order via IBKR ausführen
GET  /api/journal/stats              Journal-Statistiken & Bias-Analyse
WS   /ws/quotes                      Live-Kurs WebSocket
```

Vollständige Dokumentation: http://localhost:8000/api/docs

---

## Technologie-Stack

| Schicht    | Technologie                    | Warum                                        |
|------------|--------------------------------|----------------------------------------------|
| Frontend   | React 18 + TypeScript + Vite   | Schnell, typsicher                           |
| Styling    | Tailwind CSS                   | Design-System, Dark Mode                     |
| Backend    | FastAPI (Python 3.12)          | Async, OpenAPI-Docs, Daten-Ökosystem         |
| ORM        | SQLAlchemy 2.0 + asyncpg       | Async PostgreSQL, typsichere Modelle         |
| Migrationen| Alembic                        | Versionierte Schema-Migrationen              |
| Cache      | Redis 7 + redis.asyncio        | Live-Kurse <5ms Latenz                       |
| Primäre DB | PostgreSQL 16                  | ACID, bewährt, JSON-Support                  |
| Zeitreihen | InfluxDB 2.7                   | Optimiert für OHLCV-Kursdaten                |
| Broker     | IBKR TWS API                   | Trading, Kurse, Portfolio                    |
| KI-Analyse | Anthropic Claude API           | Scoring, Chat, Briefings                     |
| Deployment | Docker + Docker Compose        | Reproduzierbare Umgebung                     |

---

## Datenbank-Schema

Tabellen (verwaltet via Alembic):

| Tabelle          | Beschreibung                              |
|------------------|-------------------------------------------|
| `assets`         | Handelbare Instrumente (Aktien, ETFs, ...) |
| `events`         | Event-Bus-Protokoll aller Layer           |
| `signals`        | Generierte Handelssignale mit Scores      |
| `regime_states`  | Historischer Marktregime-Verlauf          |
| `recommendations`| Entscheidungsempfehlungen (Decision Engine)|
| `trades`         | Trading-Journal mit P&L und Bias-Analyse  |
| `watchlist`      | Beobachtungsliste mit Zielpreisen         |
| `alerts`         | Kursalarme (above/below threshold)        |

---

## Nächste Entwicklungsschritte

### Phase 2
- [ ] IBKR TWS API Live-Integration
- [ ] Claude API vollständige KI-Analyse
- [ ] WebSocket Live-Kurse
- [ ] Auth (JWT + 2FA)

### Phase 3
- [ ] Backtesting-Engine
- [ ] Earnings-Call-Analyse (NLP)
- [ ] Sentiment-Pipeline (NewsAPI + X API)

### Phase 4
- [ ] Mobile App (React Native)
- [ ] Steuer-Report automatisiert (ESTV)

---

## Lizenz

Privates Repository — nur für den persönlichen Gebrauch.
