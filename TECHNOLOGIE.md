# TradeApp — Technologie-Empfehlung

## Empfohlener Stack: React + FastAPI + PostgreSQL

### Warum dieser Stack?

| Schicht | Technologie | Begründung |
|---|---|---|
| **Frontend Framework** | React 18 + TypeScript | Komponentenbasiert, riesiges Ökosystem, Typsicherheit |
| **Build Tool** | Vite 5 | 50× schneller als Webpack, HMR <100ms |
| **Styling** | Tailwind CSS + CSS Variables | Design-System, Dark Mode, kein CSS-Bloat |
| **State Management** | Zustand + React Query | Minimal-Setup, keine Boilerplate |
| **Charts** | Lightweight Charts (TradingView) | Professionelle Finanz-Charts, performant |
| **Backend** | FastAPI (Python) | Async, automatische OpenAPI-Docs, schnell |
| **Primäre DB** | PostgreSQL | ACID-konform, JSON-Support, bewährt |
| **Zeitreihendaten** | InfluxDB | Optimiert für OHLCV-Kursdaten |
| **Cache** | Redis | Live-Kurse <5ms Latenz |
| **Live-Daten** | WebSockets | Echtzeitkurse ohne Polling |
| **Broker-API** | IBKR TWS API | Trading, Kurse, Portfolio |
| **Fundamentaldaten** | Financial Modeling Prep | Earnings, KGVs, Balance Sheet |
| **KI-Analyse** | Anthropic Claude API | Scoring, Chat, Reports |
| **Auth** | Auth0 / Supabase Auth | JWT, OAuth2, 2FA |
| **Deployment** | Docker + Railway / Vercel | CI/CD, Skalierung |

## Alternativen (falls andere Präferenz)

### Option B: Next.js + Node.js (Full-Stack JS)
- **Vorteil**: Ein Sprache (TypeScript) für alles, SSR, Vercel-Deployment trivial
- **Nachteil**: Node.js weniger geeignet für numerische Berechnungen, schwächeres Daten-Ökosystem
- **Empfohlen wenn**: Team nur JS/TS kennt

### Option C: Electron (Desktop-App)
- **Vorteil**: Native Desktop-App, direkter IBKR-Zugriff, offline-fähig
- **Nachteil**: Schwergewichtig, Update-Prozess aufwändig
- **Empfohlen wenn**: Kein Browser gewünscht, maximale Performance

### Option D: Python + Streamlit (Schnellst-Prototyp)
- **Vorteil**: In 2 Tagen lauffähig, natives Pandas/NumPy-Ökosystem
- **Nachteil**: Nicht production-ready, UI-Limitierungen
- **Empfohlen wenn**: Nur für eigene Nutzung, schnellste MVP

## Entwicklungsphasen

### Phase 1 — MVP (8 Wochen)
- Dashboard + Heatmap (Sektoren, Länder)
- Portfolio-Tracking (IBKR-Integration)
- Live-Kurse via WebSocket
- Basis-Signale (RSI, MACD)
- Trade-Ausführung (Market/Limit)

### Phase 2 — V1 (16 Wochen)
- Scoring-Modell Hard Facts (0–100)
- Vollständige technische Analyse
- Watchlist + Alarm-System
- Trading-Journal

### Phase 3 — V2 (6 Monate)
- KI-Analyse (Claude API)
- Soft Facts (Management, Sentiment)
- Geopolitik-Radar
- Bias-Analyse

### Phase 4 — V3 (12 Monate)
- Backtesting-Engine
- Steuer-Assistent (Schweiz)
- Alternative Daten
- Mobile App (React Native)

## Projektstruktur

```
tradeapp/
├── frontend/                 # React + TypeScript
│   ├── src/
│   │   ├── components/       # Wiederverwendbare UI-Komponenten
│   │   │   ├── ui/           # Button, Tag, Card, Input, Modal
│   │   │   ├── charts/       # Preischart, Heatmap, Sparkline
│   │   │   ├── layout/       # TopBar, NavTabs, Sidebar, DetailPanel
│   │   │   └── domain/       # SignalCard, PositionRow, MacroTile
│   │   ├── pages/            # Home, Heatmap, Signals, Portfolio, Macro, Journal
│   │   ├── hooks/            # useMarketData, usePortfolio, useSignals
│   │   ├── store/            # Zustand stores (ui, market, portfolio, alerts)
│   │   ├── services/         # API-Calls, WebSocket-Client
│   │   ├── types/            # TypeScript Interfaces
│   │   └── utils/            # Formatter, Farb-Helfer, Berechnungen
│   ├── public/
│   ├── package.json
│   └── vite.config.ts
│
├── backend/                  # FastAPI Python
│   ├── app/
│   │   ├── routers/          # market, portfolio, signals, analysis, auth
│   │   ├── services/         # ibkr_client, scoring, ai_analysis, websocket
│   │   ├── models/           # SQLAlchemy DB-Modelle
│   │   ├── schemas/          # Pydantic Request/Response Schemas
│   │   └── main.py           # App Entry Point
│   ├── requirements.txt
│   └── Dockerfile
│
├── docker-compose.yml
└── README.md
```
