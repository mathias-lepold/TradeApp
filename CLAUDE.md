# TradeApp — Projektdokumentation

Professionelles Trading-Dashboard zur Verwaltung eines CHF-Portfolios.
Backend: Python/FastAPI · Frontend: React/TypeScript · Daten: MockFeed (Dev) / IBKR TWS (Prod)

---

## Schnellstart (ohne IBKR, ohne Docker)

```bash
# Backend
cd backend
python -m venv venv
./venv/Scripts/activate        # Windows
# source venv/bin/activate     # Mac/Linux
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (separates Terminal)
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

**API-Docs:** http://localhost:8000/api/docs

---

## Architektur

```
IBKR TWS ──►┐
             │  Reality Layer         IBKRFeed / MockFeed + EventPublisher
MockFeed ───►│  (ibkr_feed.py,        Preise als Event-Stream
             │   market_feed.py,      DataNormalizer: Rohdaten → Domain
             │   event_publisher)
             ↓
        Interpretation Layer          SignalGenerator  (RSI/MACD/Bollinger)
        (signal_generator.py,         RegimeDetector   (Bull/Bear/Crisis)
         regime_detector.py,          MarketCycleEngine (6 Phasen, Intensität 0–1)
         cycle_engine.py,             ExpectationEngine (Consensus vs. Outcome)
         expectation_engine.py,       FeedbackLoopDetector (Blasen/Panik/Stab.)
         feedback_detector.py)
             ↓
        Liquidity Layer               LiquidityLayer   (Stress, FundingConditions,
        (liquidity/                   ForcedSellingRisk — VIX-Proxy aus MockFeed)
         liquidity_layer.py)
             ↓
        Behavioral Layer              BiasDetector     (FOMO/Overconf/Revenge/Confirm)
        (bias_detector.py,            BehavioralScorer
         behavioral_scorer.py)
             ↓
        Decision Engine               DecisionEngine   (Signal+Regime+Bias → Rec.)
        (engine.py,                   RiskManager      (1%-Regel, CRV, Sizing)
         risk_manager.py,             HypothesisEngine (Basis+Gegen-Hypothese)
         hypothesis_engine.py)
             ↓
        FastAPI (main.py)          REST + WebSocket → Frontend
```

---

## Layer-Beschreibungen

### Reality Layer (`backend/app/layers/reality/`)

| Datei | Zweck |
|---|---|
| `market_feed.py` | Abstrakte Basis `MarketFeed` + `MockFeed` (Brownsche Bewegung) |
| `ibkr_feed.py` | IBKR TWS über ib_insync (Real-time + Historical Fallback + Reconnect) |
| `event_publisher.py` | Konvertiert Feed-Events → `QuoteEvent`, leitet Downstream weiter |
| `normalizer.py` | IBKR-Bars → Domain-Objekte, Symbol-Metadaten |

**MockFeed:** Simuliert realistische Preisbewegungen für AAPL, MSFT, NVDA, SPY, NOVN, ZGLD via Brownsche Bewegung mit Mean-Reversion.

### Interpretation Layer (`backend/app/layers/interpretation/`)

| Datei | Zweck |
|---|---|
| `signal_generator.py` | `TechnicalAnalyzer` (RSI/MACD/Bollinger/Volume) + `SignalGenerator` |
| `regime_detector.py` | Bull/Bear/Sideways/Crisis/Recovery via VIX, Zinskurve, Fear&Greed |

**TechnicalAnalyzer:**
- RSI(14): < 30 überverkauft, > 70 überkauft
- MACD(12,26,9): Histogramm positiv = bullisch
- Bollinger(20,2σ): pct_b < 0.2 = Kaufgelegenheit
- Volume: > 1.5× Durchschnitt = Bestätigung

### Liquidity Layer (`backend/app/layers/liquidity/`)

| Datei | Zweck |
|---|---|
| `liquidity_layer.py` | `LiquidityLayer`: `liquidity_stress`, `funding_conditions`, `forced_selling_risk` — VIX-Proxy aus MockFeed-Preishistorie |

**FundingCondition:** `ample → normal → tightening → tight → stressed`
**VIX-Proxy:** Annualisierte Volatilität der Preishistorien (VIX-ähnliche Skala, kein externer Feed)

### Behavioral Layer (`backend/app/layers/behavioral/`)

| Datei | Zweck |
|---|---|
| `bias_detector.py` | Erkennt: FOMO, Loss Aversion, Overconfidence, Revenge Trading, Recency Bias, Confirmation Bias |
| `behavioral_scorer.py` | Aggregiert BiasRisk → Quality Score 0–100 |

### Decision Engine (`backend/app/layers/decision/`)

| Datei | Zweck |
|---|---|
| `engine.py` | Signal + Regime + Bias → `Recommendation` v2: Szenarioanalyse, No-Trade-Flag, Unsicherheitslevel |
| `risk_manager.py` | 1%-Regel, CRV min. 2.0, Positionsgrösse, Schweizer Stempelsteuer |
| `hypothesis_engine.py` | `HypothesisEngine`: Basishypothese + Gegenhypothese + Phasenwechsel-Trigger |

**Decision Engine v2 Erweiterungen:**
- `no_trade_flag=True` wenn `regime_fragility > 0.7`
- `scenario_analysis`: `{bull, base, bear}` Wahrscheinlichkeiten
- `uncertainty_level`: `low / medium / high`
- `base_hypothesis` + `counter_hypothesis` als Kurztext

---

## Domain Models (`backend/app/domain/`)

| Datei | Objekt | Erweiterungen v2 |
|---|---|---|
| `event.py` | `Event` | + `relevance`, `confidence`, `expected_half_life`, `expected_lag`, `direct_impact`, `indirect_impact`, `narrative_tag` |
| `signal.py` | `Signal` | + `decay_function` (`linear/exponential/step`), `lag_seconds` |
| `regime_state.py` | `RegimeState` | + `regime_fragility` (0–1), `dominant_layer`, `transition_speed` |
| `recommendation.py` | `Recommendation` | + `no_trade_flag`, `base_hypothesis`, `counter_hypothesis`, `scenario_analysis`, `uncertainty_level` |
| `asset.py` | `Asset` | Handelbares Finanzinstrument (unverändert) |

Alle neuen Felder sind `Optional` mit Defaults — keine Breaking Changes.

---

## API-Endpunkte

| Method | Path | Beschreibung |
|---|---|---|
| GET | `/health` | Status: MockFeed, Redis, DB, Regime |
| GET | `/api/quotes/{symbol}` | Aktueller Kurs aus MockFeed-Cache |
| GET | `/api/macro` | Makroökonomische Indikatoren |
| GET | `/api/regime` | Aktuelles Marktregime |
| GET | `/api/signals` | Handelssignale (mit RSI/MACD/Bollinger) |
| GET | `/api/signals/{symbol}` | Signal für ein Symbol |
| GET | `/api/recommendations` | Finale Empfehlungen (vollständige Pipeline) |
| GET | `/api/recommendations/{symbol}` | Empfehlung für ein Symbol |
| GET | `/api/portfolio` | Portfolio mit MockFeed-Preisen |
| POST | `/api/orders/validate` | Order-Validierung (RiskManager) |
| POST | `/api/orders/execute` | Order ausführen (Demo/IBKR) |
| GET | `/api/journal/stats` | Trade-Journal Statistiken |
| GET | `/api/journal/bias-analysis/{symbol}` | Bias-Analyse für Symbol |
| POST | `/api/ai/analyze` | KI-Analyse (Claude API, Demo-Modus) |
| WS | `/ws/quotes` | Live-Kurse alle 8s |
| **GET** | **`/api/cycle`** | **Aktuelle Marktphasen (6 Phasen, Intensität 0–1, Transition Speed)** |
| **GET** | **`/api/liquidity`** | **LiquidityState: Stress, FundingConditions, ForcedSellingRisk** |
| **GET** | **`/api/expectations`** | **ExpectationModel: Consensus vs. Outcome, Surprise-Score (Portfolio oder ?symbol=X)** |
| **GET** | **`/api/hypothesis/{symbol}`** | **Basis- + Gegenhypothese + Phasenwechsel-Trigger** |

---

## Frontend (`frontend/src/`)

| Datei | Zweck |
|---|---|
| `App.tsx` | Hauptkomponente (6 Seiten: Home, Heatmap, Signals, Portfolio, Macro, Journal) |
| `api.ts` | Typisierter API-Client (alle Endpunkte) |
| `useBackendData.ts` | React Hooks: `usePortfolio`, `useSignals`, `useRecommendations`, `useMacro`, `useRegime`, `useJournalStats`, `useBackendStatus` |

---

## Tests (`backend/tests/`)

```bash
cd backend
pytest -v
```

| Datei | Layer | Testet |
|---|---|---|
| `test_technical.py` | Interpretation | RSI, MACD, Bollinger Bands, Volume Score |
| `test_regime_detector.py` | Interpretation | Bull/Bear/Crisis Klassifikation |
| `test_risk_manager.py` | Decision | 1%-Regel, CRV, Positionsgrösse, Stempelsteuer |
| `test_bias_detector.py` | Behavioral | Alle 6 Bias-Typen inkl. Confirmation Bias |
| `test_decision_engine.py` | Decision | Vollständige Pipeline, Regime-Override, Bias-Override |
| `test_mock_feed.py` | Reality | Async Verbindung, Event-Bus, Streaming |

---

## Konfiguration (`.env`)

```env
# Pflichtfelder für Produktion — für Dev-Betrieb nicht nötig
IBKR_HOST=127.0.0.1
IBKR_PORT=7497
IBKR_CLIENT_ID=1
ANTHROPIC_API_KEY=sk-ant-...
DATABASE_URL=postgresql+asyncpg://tradeapp:secret@localhost:5432/tradeapp
REDIS_URL=redis://localhost:6379/0
```

---

## Entwicklungs-Modi

### Ohne IBKR (Standard)
MockFeed startet automatisch. Alle Preise sind simuliert.
Kein `.env` nötig — läuft sofort.

### Mit IBKR TWS
1. TWS Paper Trading auf Port 7497 starten
2. API-Verbindungen in TWS aktivieren
3. `IBKRFeed` statt `MockFeed` in `main.py` verwenden:
   ```python
   from app.layers.reality import IBKRFeed, EventPublisher
   _state.feed = IBKRFeed()
   ```

### Mit PostgreSQL + Redis
```bash
docker compose up -d  # falls vorhanden
```
Oder im `.env` entsprechende URLs setzen.
Beide sind optional — der Server läuft auch ohne.

---

## Portfolio

Echte Positionen in `backend/app/main.py → _MY_POSITIONS`:

| Symbol | Anzahl | Avg. Einstand | Währung |
|---|---|---|---|
| NVDA | 59 | 748.20 | USD |
| MSFT | 130 | 405.10 | USD |
| ZGLD | 210 | 176.80 | CHF |
| NOVN | 282 | 88.60 | CHF |

**Produktionsumstellung:** Positionen aus PostgreSQL laden (Tabelle `trades`).

---

## Risiko-Regeln

- **1%-Regel:** Max. 1% des Portfolios als Risiko pro Trade
- **CRV:** Minimum 1:2.0 (Reward/Risk)
- **Positionslimit:** Max. 10% des Portfolios in eine Position
- **Regime-Anpassung:** Krisenregime → keine neuen Käufe
- **Stempelsteuer CH:** 0.075% auf Käufe/Verkäufe

---

## Geplante Erweiterungen (Prod)

- [ ] PostgreSQL-Integration: Trades, Journal, Watchlist aus DB
- [ ] IBKRFeed aktivieren: `IBKRFeed` statt `MockFeed` in `main.py`
- [ ] Claude API aktivieren: `POST /api/ai/analyze` mit echtem Anthropic-Key
- [ ] Auth: JWT-Tokens via `python-jose`
- [ ] Redis: Preiscaching aktivieren (derzeit In-Memory)
- [ ] Docker Compose: Backend + Frontend + DB + Redis
