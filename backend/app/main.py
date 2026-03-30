"""
TradeApp Backend — FastAPI v2.0.0
==================================
Architektur: Reality Layer → Interpretation → Behavioral → Decision → API

Ohne IBKR und ohne Docker starten:
    cd backend
    uvicorn app.main:app --reload --port 8000

MockFeed startet automatisch beim Serverstart und simuliert Live-Kurse.
Redis und PostgreSQL sind optional — der Server läuft auch ohne sie.
"""
from __future__ import annotations

import asyncio
import logging
from collections import deque
from datetime import datetime
from typing import Deque, Dict, List, Optional

logger = logging.getLogger("tradeapp")

# ── Backtesting ───────────────────────────────────────────────────────────────
from app.domain.backtest import BacktestConfig, BacktestResult
from app.layers.backtesting.engine import BacktestEngine

# ── Portfolio ─────────────────────────────────────────────────────────────────
from app.domain.portfolio import PortfolioTradeCreate
from app.services.portfolio_service import PortfolioService

# ── Watchlist ─────────────────────────────────────────────────────────────────
from app.domain.watchlist import WatchlistAdd
from app.services.watchlist_service import WatchlistService

# ── Alerts ────────────────────────────────────────────────────────────────────
from app.domain.alerts import AlertCreate
from app.services.alert_service import AlertService

# ── News ──────────────────────────────────────────────────────────────────────
from app.layers.reality.news_feed import NewsFeed

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── Core ──────────────────────────────────────────────────────────────────────
from app.core.config import get_settings

# ── Domain Models ─────────────────────────────────────────────────────────────
from app.domain.event import Event, EventType
from app.domain.regime_state import MacroSnapshot
from app.domain.signal import Signal

# ── Reality Layer ─────────────────────────────────────────────────────────────
from app.layers.reality import MarketFeed, MockFeed, YahooFeed, FeedManager, EventPublisher, DataNormalizer

# ── Interpretation Layer ──────────────────────────────────────────────────────
from app.layers.interpretation.signal_generator import SignalGenerator, TechnicalAnalyzer
from app.layers.interpretation.regime_detector import RegimeDetector
from app.layers.interpretation.cycle_engine import MarketCycleEngine
from app.layers.interpretation.expectation_engine import ExpectationEngine
from app.layers.interpretation.feedback_detector import FeedbackLoopDetector

# ── Liquidity Layer ───────────────────────────────────────────────────────────
from app.layers.liquidity import LiquidityLayer

# ── Behavioral Layer ──────────────────────────────────────────────────────────
from app.layers.behavioral.bias_detector import BiasDetector, TraderContext
from app.layers.behavioral.behavioral_scorer import BehavioralScorer

# ── Decision Engine ───────────────────────────────────────────────────────────
from app.layers.decision.engine import DecisionEngine
from app.layers.decision.risk_manager import RiskManager
from app.layers.decision.hypothesis_engine import HypothesisEngine

settings = get_settings()

# ── FastAPI App ───────────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.app_name,
    description="Professional Trading Dashboard — CHF Portfolio Management",
    version=settings.app_version,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Symbol-Konfiguration ──────────────────────────────────────────────────────

TRACKED_SYMBOLS = ["MSFT", "NVDA", "AAPL", "NOVN", "ZGLD"]

# Fundamentale + Management Scores (statisch — Prod: aus Research-DB)
_FUND_SCORES: Dict[str, Dict[str, int]] = {
    "MSFT": {"fundamental": 84, "management": 91, "geopolitical": 55, "macro": 68},
    "NVDA": {"fundamental": 88, "management": 86, "geopolitical": 72, "macro": 76},
    "AAPL": {"fundamental": 82, "management": 89, "geopolitical": 60, "macro": 72},
    "NOVN": {"fundamental": 79, "management": 82, "geopolitical": 88, "macro": 74},
    "ZGLD": {"fundamental": 75, "management": 70, "geopolitical": 85, "macro": 82},
}

_MY_POSITIONS = [
    {"id": "p1", "symbol": "NVDA", "name": "NVIDIA",    "quantity": 59,  "avg_price": 748.20,
     "currency": "USD", "exchange": "NASDAQ", "score": 85, "sector": "Technology"},
    {"id": "p2", "symbol": "MSFT", "name": "Microsoft", "quantity": 130, "avg_price": 405.10,
     "currency": "USD", "exchange": "NASDAQ", "score": 80, "sector": "Technology"},
    {"id": "p3", "symbol": "ZGLD", "name": "ZKB Gold",  "quantity": 210, "avg_price": 176.80,
     "currency": "CHF", "exchange": "SIX",    "score": 74, "sector": "Commodities"},
    {"id": "p4", "symbol": "NOVN", "name": "Novartis",  "quantity": 282, "avg_price": 88.60,
     "currency": "CHF", "exchange": "SIX",    "score": 78, "sector": "Healthcare"},
]

# Globaler Makro-Snapshot (Prod: Fed/ECB/SNB API)
_MACRO = MacroSnapshot(
    fed_rate=3.75, snb_rate=0.50, vix=24.5, yield_curve_10y_2y=0.27,
    usd_chf=settings.usd_chf_rate, eur_chf=0.9372,
    gold_xau_usd=4850.0, oil_wti=99.40,
    fear_greed_index=32, cpi_us=2.4, unemployment_us=4.4,
)

# ── App State ─────────────────────────────────────────────────────────────────

class _PriceState:
    """In-Memory Preis-Cache + rollierende Preishistorie (kein Redis nötig)."""

    def __init__(self) -> None:
        self.cache:   Dict[str, Dict]           = {}
        self.history: Dict[str, Deque[float]]   = {}
        self.volumes: Dict[str, Deque[int]]     = {}
        self.feed:      Optional[MarketFeed]     = None
        self.feed_mode: str                      = "mock"
        self.publisher: Optional[EventPublisher] = None
        self._task:     Optional[asyncio.Task]   = None

    def update(self, sym: str, price: float, change: float,
               change_pct: float, volume: int, source: str) -> None:
        self.cache[sym] = {
            "price": price, "change": change,
            "change_percent": change_pct, "volume": volume,
            "source": source, "updated_at": datetime.utcnow().isoformat(),
        }
        self.history.setdefault(sym, deque(maxlen=100)).append(price)
        self.volumes.setdefault(sym, deque(maxlen=100)).append(volume)

    def price(self, sym: str) -> float:
        return self.cache.get(sym, {}).get("price") or 100.0


_state = _PriceState()

# ── Layer-Instanzen ───────────────────────────────────────────────────────────

_normalizer      = DataNormalizer()
_signal_gen      = SignalGenerator(min_score_threshold=62)
_regime_det      = RegimeDetector()
_bias_det        = BiasDetector()
_behavioral_scr  = BehavioralScorer()
_risk_mgr        = RiskManager()
_decision_eng    = DecisionEngine(
    risk_manager        = _risk_mgr,
    portfolio_value_chf = settings.portfolio_value_chf,
    fx_usd_chf          = settings.usd_chf_rate,
)

# ── Neue Engine-Instanzen ─────────────────────────────────────────────────────
_cycle_eng       = MarketCycleEngine()
_expect_eng      = ExpectationEngine()
_feedback_det    = FeedbackLoopDetector()
_liquidity_layer = LiquidityLayer()
_hypothesis_eng  = HypothesisEngine()

# Regime wird einmalig berechnet und gecacht
_current_regime = _regime_det.detect(_MACRO)

# ── Event-Handler ─────────────────────────────────────────────────────────────

async def _on_price_event(event: Event) -> None:
    sym = event.asset_symbol
    if not sym or event.event_type != "price_update":
        return
    p = event.payload
    q = p.get("quote", p)
    _state.update(
        sym        = sym,
        price      = q.get("price", p.get("price", 0)),
        change     = q.get("change", p.get("change", 0)),
        change_pct = q.get("change_percent", p.get("change_percent", 0)),
        volume     = int(q.get("volume", p.get("volume", 0))),
        source     = q.get("data_source", "mock"),
    )

# ── Startup / Shutdown ────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup() -> None:
    global _current_regime
    print(f"[TradeApp] Backend {settings.app_version} startet…")

    # Schritt 1: Redis optional verbinden (kein Fehler wenn nicht verfügbar)
    try:
        from app.services.cache import get_cache
        await get_cache().connect()
        print("[TradeApp] Redis verbunden")
    except Exception as e:
        print(f"[TradeApp] Redis nicht verfügbar (kein Problem): {e}")

    all_syms = list({p["symbol"] for p in _MY_POSITIONS} | set(TRACKED_SYMBOLS))

    # Schritt 2: Feed erstellen (Yahoo oder Mock je nach FEED_MODE / Verfügbarkeit)
    live_feed, feed_mode = await FeedManager.create(seed=None)
    _state.feed_mode = feed_mode

    # Schritt 3: Preishistorie vorbelegen
    if feed_mode == "yahoo" and isinstance(live_feed, YahooFeed):
        # Historische Yahoo-Daten laden (30 Tage Schlusskurse)
        print(f"[TradeApp] Lade Yahoo-Preishistorie für: {all_syms}")
        for sym in all_syms:
            prices_init = await live_feed.fetch_history(sym, days=60)
            if prices_init:
                _state.history[sym] = deque(prices_init, maxlen=100)
                # Volume: kein historisches Volume aus Yahoo — Dummy setzen
                _state.volumes[sym] = deque([1_000_000] * len(prices_init), maxlen=100)
                prev = prices_init[-2] if len(prices_init) > 1 else prices_init[0]
                curr = prices_init[-1]
                chg  = round(curr - prev, 4)
                chg_pct = round(chg / prev * 100, 3) if prev else 0.0
                _state.cache[sym] = {
                    "price": curr, "change": chg, "change_percent": chg_pct,
                    "volume": 1_000_000,
                    "source": "yahoo_history", "updated_at": datetime.utcnow().isoformat(),
                }
        print(f"[TradeApp] Yahoo-Preishistorie geladen für: {all_syms}")
    else:
        # MockFeed-Seed für Preishistorie
        seeder = MockFeed(seed=42)
        await seeder.connect()
        for sym in all_syms:
            prices_init: List[float] = []
            vols_init:   List[int]   = []
            for _ in range(60):
                snap = seeder.get_snapshot(sym)
                if snap:
                    prices_init.append(snap["price"])
                    vols_init.append(snap.get("volume", 0))
            if prices_init:
                _state.history[sym] = deque(prices_init, maxlen=100)
                _state.volumes[sym] = deque(vols_init, maxlen=100)
                prev = prices_init[-2] if len(prices_init) > 1 else prices_init[0]
                curr = prices_init[-1]
                chg  = round(curr - prev, 4)
                chg_pct = round(chg / prev * 100, 3) if prev else 0.0
                _state.cache[sym] = {
                    "price": curr, "change": chg, "change_percent": chg_pct,
                    "volume": vols_init[-1] if vols_init else 0,
                    "source": "mock_seed", "updated_at": datetime.utcnow().isoformat(),
                }
        await seeder.disconnect()
        print(f"[TradeApp] Preishistorie (60 Candles) geladen für: {all_syms}")

    # Schritt 4: Services aus DB laden (optional)
    await _portfolio_service.load_from_db()
    await _watchlist_service.load_from_db()
    await _alert_service.load_from_db()

    # Schritt 5: Regime berechnen
    _current_regime = _regime_det.detect(_MACRO)
    print(f"[TradeApp] Regime: {_current_regime.label} "
          f"(Konfidenz {_current_regime.confidence:.0%})")

    # Schritt 6: Live-Feed starten
    _state.feed      = live_feed
    _state.publisher = EventPublisher(_state.feed)
    _state.publisher.add_downstream(_on_price_event)
    _state._task = asyncio.create_task(
        _state.feed.start_streaming(all_syms, interval_sec=30.0 if feed_mode == "yahoo" else 8.0)
    )
    print(f"[TradeApp] {feed_mode.upper()}Feed live — {len(all_syms)} Symbole")

    # Schritt 7: Alert-Background-Checker starten
    def _score_fn(sym: str) -> Optional[int]:
        hist = list(_state.history.get(sym, []))
        if len(hist) < 20:
            return None
        try:
            sig = _signal_gen.generate_from_prices(sym, hist, {})
            return sig.score.total if sig else None
        except Exception:
            return None

    asyncio.create_task(_alert_service.run_background_checker(
        price_fn=_state.price,
        score_fn=_score_fn,
        regime_fn=lambda: _current_regime.label,
        interval=30,
    ))
    print("[TradeApp] Alert-Checker aktiv (alle 30s)")


@app.on_event("shutdown")
async def shutdown() -> None:
    if _state._task and not _state._task.done():
        _state._task.cancel()
    if _state.feed:
        await _state.feed.disconnect()
    try:
        from app.services.cache import get_cache
        await get_cache().disconnect()
    except Exception:
        pass
    print("[TradeApp] Backend gestoppt")

# ── Health & Status ───────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "status":  f"{settings.app_name} API {settings.app_version}",
        "feed":    type(_state.feed).__name__ if _state.feed else "not started",
        "regime":  _current_regime.label,
        "docs":    "/api/docs",
        "layers":  ["reality", "interpretation", "behavioral", "decision"],
    }


@app.get("/health")
async def health():
    redis_ok = False
    db_ok    = False
    try:
        from app.services.cache import get_cache
        redis_ok = await get_cache().health()
    except Exception:
        pass
    try:
        from app.services.database import health_check as db_health
        db_ok = await db_health()
    except Exception:
        pass

    last_fetch = None
    if isinstance(_state.feed, YahooFeed) and _state.feed.last_fetch:
        last_fetch = _state.feed.last_fetch.isoformat()

    # ── IBKR-Verbindungsstatus via TCP-Probe ───────────────────────────────
    # Reiner Socket-Check auf 127.0.0.1:7497 — kein ib_insync, kein Handshake.
    # True  → TWS / IB Gateway lauscht auf dem Port
    # False → Port geschlossen oder Timeout
    ibkr_ok = False
    try:
        _writer = None
        _, _writer = await asyncio.wait_for(
            asyncio.open_connection("127.0.0.1", 7497),
            timeout=2.0,
        )
        ibkr_ok = True
    except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
        ibkr_ok = False
    finally:
        if _writer is not None:
            try:
                _writer.close()
                await _writer.wait_closed()
            except Exception:
                pass

    return {
        "status":          "ok",
        "ibkr_connected":  ibkr_ok,
        "mock_feed":       _state.feed.is_connected if _state.feed else False,
        "redis":           redis_ok,
        "database":        db_ok,
        "regime":          _current_regime.label,
        "cached_symbols":  list(_state.cache.keys()),
        "feed_mode":       _state.feed_mode,
        "last_data_fetch": last_fetch,
        "timestamp":       int(datetime.utcnow().timestamp()),
    }

# ── Reality Layer: Marktdaten ─────────────────────────────────────────────────

@app.get("/api/quotes/{symbol}")
async def get_quote(symbol: str):
    sym  = symbol.upper()
    info = _state.cache.get(sym)
    if not info:
        raise HTTPException(404, f"Symbol {sym} nicht im Cache — noch kein MockFeed-Tick")
    asset = _normalizer.symbol_to_asset(sym)
    return {
        "symbol":         sym,
        "name":           asset.name,
        "price":          info["price"],
        "change":         info["change"],
        "change_percent": info["change_percent"],
        "volume":         info["volume"],
        "currency":       asset.currency,
        "exchange":       asset.exchange,
        "source":         info.get("source", "mock"),
        "timestamp":      int(datetime.utcnow().timestamp()),
    }


@app.get("/api/macro")
async def get_macro():
    m = _MACRO
    return {
        "fed_rate": m.fed_rate, "snb_rate": m.snb_rate, "ecb_rate": 2.40, "boj_rate": 0.50,
        "cpi_us": m.cpi_us, "nfp_latest": -92000, "nfp_expected": 60000,
        "unemployment": m.unemployment_us, "oil_wti": m.oil_wti,
        "gold_xau_usd": m.gold_xau_usd, "silver_xag_usd": 70.10,
        "eur_chf": m.eur_chf, "usd_chf": m.usd_chf,
        "vix": m.vix, "fear_greed_index": m.fear_greed_index,
        "yield_curve_10y_2y": m.yield_curve_10y_2y,
        "last_updated": int(datetime.utcnow().timestamp()),
    }

# ── Interpretation Layer: Regime ──────────────────────────────────────────────

@app.get("/api/regime")
async def get_regime():
    r = _current_regime
    return {
        "regime_type":    r.regime_type,     "sub_regime":   r.sub_regime,
        "label":          r.label,           "confidence":   r.confidence,
        "strength":       r.strength,        "is_risk_off":  r.is_risk_off,
        "vix_category":   r.vix_category,
        "characteristics": r.characteristics, "active_risks": r.active_risks,
        "max_position_size_pct":       r.max_position_size_pct,
        "recommended_cash_buffer_pct": r.recommended_cash_buffer_pct,
        "sector_preferences":          r.sector_preferences,
        "detected_at":    r.detected_at.isoformat(),
    }

# ── Interpretation Layer: Signals ─────────────────────────────────────────────

@app.get("/api/signals")
async def get_signals(min_score: int = 70, max_results: int = 10):
    """
    Handelssignale vom Interpretation Layer.
    RSI, MACD, Bollinger Bands aus der MockFeed-Preishistorie.
    """
    fear_greed  = _MACRO.fear_greed_index or 50
    sent_score  = max(15, min(90, int(90 - fear_greed * 0.7)))
    results: List[Dict] = []

    for sym in TRACKED_SYMBOLS:
        prices  = list(_state.history.get(sym, deque()))
        volumes = list(_state.volumes.get(sym, deque()))
        fund    = _FUND_SCORES.get(sym, {})
        asset   = _normalizer.symbol_to_asset(sym)

        if len(prices) < 10:
            continue

        signal = _signal_gen.generate_from_prices(
            symbol          = sym,
            name            = asset.name,
            prices          = prices,
            fund_scores     = fund,
            volumes         = volumes or None,
            sentiment_score = sent_score,
            regime_context  = _current_regime.label,
        )
        if signal and signal.score.total >= min_score:
            results.append(_signal_to_response(signal))

    results.sort(key=lambda x: x["score"]["total"], reverse=True)
    return results[:max_results]


@app.get("/api/signals/{symbol}")
async def get_signal_for_symbol(symbol: str):
    sym     = symbol.upper()
    prices  = list(_state.history.get(sym, deque()))
    fund    = _FUND_SCORES.get(sym, {})
    asset   = _normalizer.symbol_to_asset(sym)

    if len(prices) < 5:
        raise HTTPException(404, f"Zu wenig Preisdaten für {sym}")

    sent = max(15, min(90, int(90 - (_MACRO.fear_greed_index or 50) * 0.7)))
    signal = _signal_gen.generate_from_prices(
        sym, asset.name, prices, fund, sentiment_score=sent,
        regime_context=_current_regime.label,
    )
    if not signal:
        raise HTTPException(404, f"Kein Signal für {sym} (Score unter Schwelle)")
    return _signal_to_response(signal)

# ── Decision Engine: Recommendations ─────────────────────────────────────────

@app.get("/api/recommendations")
async def get_recommendations(min_score: int = 65):
    """Signal → Regime → Bias → Decision Engine → Recommendation."""
    sent     = max(15, min(90, int(90 - (_MACRO.fear_greed_index or 50) * 0.7)))
    ctx      = TraderContext(
        current_positions={"NVDA": -4.2, "MSFT": -10.1},
        consecutive_wins=1, consecutive_losses=0,
        portfolio_value_chf=settings.portfolio_value_chf,
    )
    results: List[Dict] = []

    for sym in TRACKED_SYMBOLS:
        prices = list(_state.history.get(sym, deque()))
        fund   = _FUND_SCORES.get(sym, {})
        asset  = _normalizer.symbol_to_asset(sym)
        if len(prices) < 10:
            continue

        signal = _signal_gen.generate_from_prices(
            sym, asset.name, prices, fund,
            sentiment_score=sent, regime_context=_current_regime.label,
        )
        if not signal or signal.score.total < min_score:
            continue

        bias = _bias_det.analyze(signal, ctx, _MACRO.fear_greed_index or 50)
        rec  = _decision_eng.decide(signal, _current_regime, bias)
        results.append({
            "id": rec.id, "symbol": rec.asset_symbol, "name": rec.asset_name,
            "action": rec.action, "priority": rec.priority,
            "rationale": rec.rationale,
            "entry_price": rec.entry_price, "stop_loss": rec.stop_loss,
            "target_price": rec.target_price, "crv": rec.crv,
            "composite_score": rec.composite_score,
            "regime_summary": rec.regime_summary,
            "has_bias_warning": rec.has_bias_warning,
            "bias_score": rec.bias_risk.overall_score if rec.bias_risk else 0,
            "detected_biases": rec.bias_risk.detected_biases if rec.bias_risk else [],
            "key_risks": rec.key_risks,
            "sizing": rec.sizing.model_dump() if rec.sizing else None,
            "created_at": rec.created_at.isoformat(),
        })

    results.sort(key=lambda x: x["composite_score"] or 0, reverse=True)
    return results


@app.get("/api/recommendations/{symbol}")
async def get_recommendation_for_symbol(symbol: str):
    sym    = symbol.upper()
    prices = list(_state.history.get(sym, deque()))
    fund   = _FUND_SCORES.get(sym, {})
    asset  = _normalizer.symbol_to_asset(sym)
    if len(prices) < 5:
        raise HTTPException(404, f"Zu wenig Daten für {sym}")
    sent   = max(15, min(90, int(90 - (_MACRO.fear_greed_index or 50) * 0.7)))
    signal = _signal_gen.generate_from_prices(
        sym, asset.name, prices, fund,
        sentiment_score=sent, regime_context=_current_regime.label,
    )
    if not signal:
        raise HTTPException(404, f"Kein Signal für {sym}")
    ctx  = TraderContext(portfolio_value_chf=settings.portfolio_value_chf)
    bias = _bias_det.analyze(signal, ctx, _MACRO.fear_greed_index or 50)
    rec  = _decision_eng.decide(signal, _current_regime, bias)
    return rec.model_dump()

# ── Portfolio ─────────────────────────────────────────────────────────────────

@app.get("/api/portfolio")
async def get_portfolio():
    positions: List[Dict] = []
    total_value = 0.0
    total_cost  = 0.0

    for p in _MY_POSITIONS:
        sym   = p["symbol"]
        price = _state.price(sym)
        fx    = settings.usd_chf_rate if p["currency"] == "USD" else 1.0

        value_chf = round(price * p["quantity"] * fx, 2)
        cost_chf  = round(p["avg_price"] * p["quantity"] * fx, 2)
        pnl_chf   = round(value_chf - cost_chf, 2)
        pnl_pct   = round(pnl_chf / cost_chf * 100, 2) if cost_chf else 0.0

        total_value += value_chf
        total_cost  += cost_chf

        info = _state.cache.get(sym, {})
        positions.append({
            **p,
            "current_price":  round(price, 4),
            "value_chf":      value_chf,
            "cost_basis_chf": cost_chf,
            "pnl_chf":        pnl_chf,
            "pnl_percent":    pnl_pct,
            "weight_percent": 0,
            "source":         info.get("source", "mock"),
        })

    total_with_cash = total_value + settings.cash_chf
    for pos in positions:
        pos["weight_percent"] = round(pos["value_chf"] / total_with_cash * 100, 1)

    total_pnl = round(total_value - total_cost, 2)
    total_pnl_pct = round(total_pnl / total_cost * 100, 2) if total_cost else 0.0

    today_pnl = sum(
        _state.price(p["symbol"]) * p["quantity"]
        * (settings.usd_chf_rate if p["currency"] == "USD" else 1.0)
        * _state.cache.get(p["symbol"], {}).get("change_percent", 0.0) / 100
        for p in _MY_POSITIONS
    )
    today_pnl = round(today_pnl, 2)

    return {
        "total_value_chf":   round(total_value, 2),
        "total_pnl_chf":     total_pnl,
        "total_pnl_percent": total_pnl_pct,
        "today_pnl_chf":     today_pnl,
        "today_pnl_percent": round(today_pnl / total_value * 100, 2) if total_value else 0.0,
        "cash_chf":          settings.cash_chf,
        "score":             74,
        "positions":         positions,
        "last_updated":      int(datetime.utcnow().timestamp()),
    }

# ── Orders ────────────────────────────────────────────────────────────────────

class OrderRequest(BaseModel):
    symbol:      str
    direction:   str
    quantity:    Optional[float] = None
    amount_chf:  Optional[float] = None
    order_type:  str             = "market"
    limit_price: Optional[float] = None
    stop_loss:   Optional[float] = None
    take_profit: Optional[float] = None
    oco_enabled: bool            = False


@app.post("/api/orders/validate")
async def validate_order(order: OrderRequest):
    sym   = order.symbol.upper()
    price = _state.price(sym)
    asset = _normalizer.symbol_to_asset(sym)

    if order.amount_chf:
        cost_chf = order.amount_chf
    elif order.quantity:
        fx = settings.usd_chf_rate if asset.currency == "USD" else 1.0
        cost_chf = order.quantity * price * fx
    else:
        raise HTTPException(400, "Menge oder Betrag erforderlich")

    result = _risk_mgr.validate_order(
        cost_chf            = cost_chf,
        stop_loss           = order.stop_loss,
        entry_price         = price,
        target_price        = order.take_profit,
        portfolio_value_chf = settings.portfolio_value_chf,
        regime              = _current_regime,
    )
    result["estimated_cost_chf"] = round(cost_chf, 2)
    result["entry_price"]        = price
    return result


@app.post("/api/orders/execute")
async def execute_order(order: OrderRequest):
    return {
        "status":    "accepted",
        "order_id":  f"ORD-{int(datetime.utcnow().timestamp())}",
        "symbol":    order.symbol.upper(),
        "direction": order.direction,
        "message":   "Demo-Modus — echte Ausführung via IBKR TWS in Produktion",
    }

# ── Behavioral Layer: Journal ─────────────────────────────────────────────────

@app.get("/api/journal/stats")
async def get_journal_stats():
    return {
        "total_trades":  34,   "win_rate":      0.62,
        "avg_win_chf":   3840, "avg_loss_chf":  -2960,
        "avg_crv":       1.29, "profit_factor": 1.81,
        "potential_alpha_chf": 8240,
        "bias_stats": {
            "fomo":              {"count": 8,  "cost_chf": 4120},
            "loss_aversion":     {"count": 6,  "cost_chf": 2880},
            "revenge_trade":     {"count": 4,  "cost_chf": 980},
            "confirmation_bias": {"count": 5,  "cost_chf": 1240},
            "overconfidence":    {"count": 3,  "cost_chf": 840},
            "rational":          {"count": 20, "cost_chf": 0},
        },
    }


@app.get("/api/journal/bias-analysis/{symbol}")
async def get_bias_analysis(symbol: str):
    sym    = symbol.upper()
    prices = list(_state.history.get(sym, deque()))
    fund   = _FUND_SCORES.get(sym, {})
    asset  = _normalizer.symbol_to_asset(sym)
    if len(prices) < 5:
        raise HTTPException(404, f"Zu wenig Daten für {sym}")
    sent   = max(15, min(90, int(90 - (_MACRO.fear_greed_index or 50) * 0.7)))
    signal = _signal_gen.generate_from_prices(sym, asset.name, prices, fund, sentiment_score=sent)
    if not signal:
        raise HTTPException(404, f"Kein Signal für {sym}")
    ctx     = TraderContext(consecutive_wins=2, last_trade_result="win",
                            portfolio_value_chf=settings.portfolio_value_chf)
    bias    = _bias_det.analyze(signal, ctx, _MACRO.fear_greed_index or 50)
    quality = _behavioral_scr.quality_score(bias)
    return {**bias.model_dump(), "quality_score": quality}

# ── AI Analysis ───────────────────────────────────────────────────────────────

class AIAnalysisRequest(BaseModel):
    subject: str
    context: Optional[str]   = None
    question: Optional[str]  = None

@app.post("/api/ai/analyze")
async def ai_analyze(req: AIAnalysisRequest):
    # Prod: anthropic.Anthropic().messages.create(model="claude-opus-4-6", ...)
    return {
        "analysis":     f"Demo-Analyse für '{req.subject}'. In Produktion via Claude API.",
        "subject":      req.subject,
        "generated_at": datetime.utcnow().isoformat(),
    }

# ── Tax ───────────────────────────────────────────────────────────────────────

@app.post("/api/tax/calculate")
async def calculate_tax(year: int = 2024):
    return {
        "year": year, "realized_gains_chf": 4792,
        "stamp_tax_paid_chf": 89.40, "verrechnungssteuer_chf": 840,
        "vermoegenssteuerwert_chf": settings.portfolio_value_chf,
        "note": "Prod: Berechnung aus Trade-History in PostgreSQL",
    }

# ── WebSocket Live-Kurse ──────────────────────────────────────────────────────

class _WSManager:
    def __init__(self): self.active: List[WebSocket] = []
    async def connect(self, ws: WebSocket):
        await ws.accept(); self.active.append(ws)
    def disconnect(self, ws: WebSocket):
        if ws in self.active: self.active.remove(ws)

_ws = _WSManager()

@app.websocket("/ws/quotes")
async def ws_quotes(websocket: WebSocket):
    await _ws.connect(websocket)
    try:
        while True:
            data = [
                {"symbol": sym, **_state.cache[sym],
                 "timestamp": int(datetime.utcnow().timestamp())}
                for sym in TRACKED_SYMBOLS if sym in _state.cache
            ]
            await websocket.send_json({"type": "quotes", "data": data})
            await asyncio.sleep(8)
    except WebSocketDisconnect:
        _ws.disconnect(websocket)

# ── Helper ────────────────────────────────────────────────────────────────────

def _signal_to_response(signal: Signal) -> Dict:
    price = signal.price_at_signal
    sl    = signal.stop_loss    or round(price * 0.92, 2)
    tp    = signal.target_price or round(price * 1.20, 2)
    crv   = signal.crv
    if crv is None:
        risk   = abs(price - sl)
        reward = abs(tp - price)
        crv    = round(reward / risk, 2) if risk > 0 else 2.0
    return {
        "id": signal.id, "symbol": signal.asset_symbol, "name": signal.asset_name,
        "verdict": signal.signal_type, "strength": signal.strength,
        "price": price, "stop_loss": sl, "target": tp, "crv": crv,
        "score": {
            "total":        signal.score.total,
            "fundamental":  signal.score.fundamental,
            "technical":    signal.score.technical,
            "management":   signal.score.management,
            "sentiment":    signal.score.sentiment,
            "geopolitical": signal.score.geopolitical,
            "macro":        signal.score.macro,
            "verdict":      signal.score.verdict,
            "confidence":   signal.score.confidence,
        },
        "reasons":   signal.reasons,
        "timestamp": int(signal.generated_at.timestamp()),
    }


# ── MarketCycleEngine ─────────────────────────────────────────────────────────

@app.get("/api/cycle")
async def get_market_cycle():
    """Aktuelle Marktphase(n) mit Intensität für alle Tracked Symbols (aggregiert)."""
    all_prices = list(_state.history.get("NVDA", deque())) or []
    # Verwende NVDA als Leitindex-Proxy, fallback auf ersten verfügbaren
    for sym in TRACKED_SYMBOLS:
        p = list(_state.history.get(sym, deque()))
        if len(p) > len(all_prices):
            all_prices = p

    cycle = _cycle_eng.detect(
        prices      = all_prices,
        vix         = _MACRO.vix,
        fear_greed  = _MACRO.fear_greed_index,
        regime_type = _current_regime.regime_type,
    )
    return {
        **cycle.model_dump(),
        "regime":      _current_regime.label,
        "assessed_at": datetime.utcnow().isoformat(),
    }


# ── LiquidityLayer ────────────────────────────────────────────────────────────

@app.get("/api/liquidity")
async def get_liquidity():
    """Liquiditätsbedingungen und Zwangsverkaufsrisiko aus MockFeed-Daten."""
    price_histories = {
        sym: list(_state.history.get(sym, deque()))
        for sym in TRACKED_SYMBOLS
        if _state.history.get(sym)
    }
    state = _liquidity_layer.assess(
        price_histories = price_histories,
        vix             = _MACRO.vix,
        fear_greed      = _MACRO.fear_greed_index,
        fed_rate        = _MACRO.fed_rate,
    )
    return state.model_dump()


# ── ExpectationEngine ─────────────────────────────────────────────────────────

@app.get("/api/expectations")
async def get_expectations(symbol: Optional[str] = None):
    """Erwartungsmodell: Consensus vs. tatsächlicher Outcome + Surprise-Score."""
    if symbol:
        sym    = symbol.upper()
        prices = list(_state.history.get(sym, deque()))
        if len(prices) < 5:
            raise HTTPException(404, f"Zu wenig Daten für {sym}")
        model = _expect_eng.assess(
            sym, prices, _FUND_SCORES.get(sym, {}).get("fundamental", 70)
        )
        return model.model_dump()

    # Portfolio-weite Erwartungen
    price_histories = {
        sym: list(_state.history.get(sym, deque()))
        for sym in TRACKED_SYMBOLS
        if len(_state.history.get(sym, deque())) >= 5
    }
    fund_scores = {sym: _FUND_SCORES.get(sym, {}).get("fundamental", 70)
                   for sym in price_histories}
    portfolio = _expect_eng.assess_portfolio(price_histories, fund_scores)
    return {sym: m.model_dump() for sym, m in portfolio.items()}


# ── HypothesisEngine ──────────────────────────────────────────────────────────

@app.get("/api/hypothesis/{symbol}")
async def get_hypothesis(symbol: str):
    """Basishypothese + Gegenhypothese + Phasenwechsel-Trigger für ein Symbol."""
    sym    = symbol.upper()
    prices = list(_state.history.get(sym, deque()))
    fund   = _FUND_SCORES.get(sym, {})
    asset  = _normalizer.symbol_to_asset(sym)

    if len(prices) < 5:
        raise HTTPException(404, f"Zu wenig Preisdaten für {sym}")

    sent   = max(15, min(90, int(90 - (_MACRO.fear_greed_index or 50) * 0.7)))
    signal = _signal_gen.generate_from_prices(sym, asset.name, prices, fund, sentiment_score=sent)
    if not signal:
        raise HTTPException(404, f"Kein Signal für {sym} generierbar")

    hypothesis = _hypothesis_eng.generate(signal, _current_regime, prices)
    return hypothesis.model_dump()


# ── Backtesting ───────────────────────────────────────────────────────────────

_backtest_engine  = BacktestEngine()
_backtest_results: Dict[str, BacktestResult] = {}  # in-memory store

# ── Portfolio Service ─────────────────────────────────────────────────────────
_portfolio_service  = PortfolioService(usd_chf=settings.usd_chf_rate)
_watchlist_service  = WatchlistService()
_alert_service      = AlertService()
_news_feed          = NewsFeed()


@app.post("/api/backtest/run")
async def run_backtest(config: BacktestConfig):
    """
    Startet einen Backtest und gibt sofort das vollständige Ergebnis zurück.
    Das Ergebnis wird für spätere Abfragen gespeichert.
    """
    if config.end_date <= config.start_date:
        raise HTTPException(400, "end_date muss nach start_date liegen")
    if (config.end_date - config.start_date).days < 30:
        raise HTTPException(400, "Mindestzeitraum: 30 Tage")

    try:
        result = _backtest_engine.run_backtest(config)
    except Exception as exc:
        raise HTTPException(500, f"Backtest-Fehler: {exc}") from exc

    _backtest_results[result.backtest_id] = result

    # Zusammenfassung ohne Equity-Kurve zurückgeben (für schnelle Anzeige)
    return {
        "backtest_id": result.backtest_id,
        "symbol":      config.symbol,
        "metrics":     result.metrics.model_dump(),
        "num_trades":  len(result.trades),
        "duration_ms": result.duration_ms,
        "generated_at": result.generated_at.isoformat(),
    }


@app.get("/api/backtest/results/{backtest_id}")
async def get_backtest_result(backtest_id: str):
    """Vollständiges Backtest-Ergebnis inkl. Equity-Kurve."""
    result = _backtest_results.get(backtest_id)
    if not result:
        raise HTTPException(404, f"Kein Backtest mit ID {backtest_id}")
    return result.model_dump()


@app.get("/api/backtest/trades/{backtest_id}")
async def get_backtest_trades(backtest_id: str):
    """Alle Trades eines Backtest-Laufs als Liste."""
    result = _backtest_results.get(backtest_id)
    if not result:
        raise HTTPException(404, f"Kein Backtest mit ID {backtest_id}")
    return {
        "backtest_id": backtest_id,
        "symbol":      result.config.symbol,
        "trades":      [t.model_dump() for t in result.trades],
    }


@app.get("/api/backtest/equity/{backtest_id}")
async def get_backtest_equity(backtest_id: str):
    """Equity-Kurve eines Backtest-Laufs (optimiert für Chart-Rendering)."""
    result = _backtest_results.get(backtest_id)
    if not result:
        raise HTTPException(404, f"Kein Backtest mit ID {backtest_id}")

    # Downsampling: max 252 Punkte für die Darstellung
    curve = result.equity_curve
    if len(curve) > 252:
        step  = len(curve) / 252
        curve = [curve[int(i * step)] for i in range(252)]
        curve.append(result.equity_curve[-1])  # letzter Punkt immer

    return {
        "backtest_id":   backtest_id,
        "equity_curve":  [p.model_dump() for p in curve],
        "initial_capital": result.config.initial_capital,
        "final_equity":  result.metrics.final_equity,
    }


# ── Portfolio-Verwaltung ──────────────────────────────────────────────────────

@app.get("/api/portfolio/summary")
async def get_portfolio_summary():
    """Gesamtübersicht: Werte, PnL, offene Positionen, alle Trades."""
    def price_fn(sym: str) -> float:
        return _state.price(sym)

    def today_pnl_fn(sym: str) -> float:
        info = _state.cache.get(sym, {})
        price = _state.price(sym)
        # Finde Menge aus service
        positions = _portfolio_service.get_positions(price_fn)
        qty = next((p.quantity for p in positions if p.symbol == sym), 0.0)
        fx = settings.usd_chf_rate if info.get("currency") == "USD" else 1.0
        chg_pct = info.get("change_percent", 0.0)
        return price * qty * fx * chg_pct / 100

    summary = _portfolio_service.get_summary(price_fn=price_fn, today_pnl_fn=today_pnl_fn)
    return summary.model_dump()


@app.get("/api/portfolio/positions")
async def get_portfolio_positions():
    """Alle offenen Positionen mit aktuellem PnL."""
    positions = _portfolio_service.get_positions(price_fn=_state.price)
    # Datenquelle pro Symbol hinzufügen
    for p in positions:
        info = _state.cache.get(p.symbol, {})
        p.data_source = info.get("source", "mock")
    return [p.model_dump() for p in positions]


@app.get("/api/portfolio/trades")
async def get_portfolio_trades():
    """Alle erfassten Trades (neueste zuerst)."""
    return [t.model_dump() for t in _portfolio_service.get_trades()]


@app.post("/api/portfolio/trades", status_code=201)
async def create_portfolio_trade(data: PortfolioTradeCreate):
    """Neuen Trade erfassen (Kauf oder Verkauf)."""
    sym = data.symbol.upper()
    if sym not in ({p["symbol"] for p in _MY_POSITIONS} | set(TRACKED_SYMBOLS)):
        # Symbol trotzdem erlauben — nur warnen
        print(f"[Portfolio] Unbekanntes Symbol: {sym}")

    # Prüfen ob genug Cash für Kauf vorhanden
    if data.action.value == "buy":
        summary = _portfolio_service.get_summary(price_fn=_state.price)
        fx = settings.usd_chf_rate if data.currency.upper() == "USD" else 1.0
        cost = data.quantity * data.price * fx + data.fees
        if summary.cash_chf < cost:
            raise HTTPException(400, f"Nicht genug Cash: {summary.cash_chf:.0f} CHF verfügbar, "
                                     f"{cost:.0f} CHF benötigt")

    trade = await _portfolio_service.add_trade(data)
    return trade.model_dump()


@app.delete("/api/portfolio/trades/{trade_id}")
async def delete_portfolio_trade(trade_id: str):
    """Trade löschen."""
    deleted = await _portfolio_service.delete_trade(trade_id)
    if not deleted:
        raise HTTPException(404, f"Trade {trade_id} nicht gefunden")
    return {"deleted": True, "trade_id": trade_id}


# ── Watchlist ─────────────────────────────────────────────────────────────────

@app.get("/api/watchlist")
async def get_watchlist():
    items = _watchlist_service.get_all()
    result = []
    for item in items:
        sym  = item.symbol
        info = _state.cache.get(sym, {})
        # Signal-Score aus Geschichte
        hist = list(_state.history.get(sym, []))
        score = None
        sig_type = None
        try:
            if len(hist) >= 20:
                sig = _signal_gen.generate_from_prices(sym, hist, {})
                if sig:
                    score    = sig.score.total
                    sig_type = sig.signal_type
        except Exception:
            pass
        d = item.model_dump()
        d.update({
            "current_price": info.get("price", 0),
            "change_pct":    info.get("change_percent", 0),
            "signal_score":  score,
            "signal_type":   sig_type,
            "data_source":   info.get("source", "mock"),
        })
        result.append(d)
    return result


@app.post("/api/watchlist", status_code=201)
async def add_to_watchlist(data: WatchlistAdd):
    item = await _watchlist_service.add(data)
    return item.model_dump()


@app.delete("/api/watchlist/{symbol}")
async def remove_from_watchlist(symbol: str):
    removed = await _watchlist_service.remove(symbol)
    if not removed:
        raise HTTPException(404, f"{symbol} nicht in der Watchlist")
    return {"removed": True, "symbol": symbol.upper()}


# ── News ──────────────────────────────────────────────────────────────────────

@app.get("/api/news")
async def get_all_news(limit_per: int = 3):
    syms = list({p["symbol"] for p in _MY_POSITIONS} | set(TRACKED_SYMBOLS)
                | {s.symbol for s in _watchlist_service.get_all()})
    items = await _news_feed.get_all_news(syms, limit_per=limit_per)
    return [i.model_dump() for i in items]


@app.get("/api/news/{symbol}")
async def get_news_for_symbol(symbol: str, limit: int = 8):
    items = await _news_feed.get_news(symbol.upper(), limit=limit)
    return [i.model_dump() for i in items]


# ── Alerts ────────────────────────────────────────────────────────────────────

@app.get("/api/alerts")
async def get_alerts():
    return [a.model_dump() for a in _alert_service.get_alerts()]


@app.get("/api/alerts/triggered")
async def get_triggered_alerts():
    return [e.model_dump() for e in _alert_service.get_history()]


@app.post("/api/alerts", status_code=201)
async def create_alert(data: AlertCreate):
    alert = await _alert_service.create_alert(data)
    return alert.model_dump()


@app.delete("/api/alerts/{alert_id}")
async def delete_alert(alert_id: str):
    deleted = await _alert_service.delete_alert(alert_id)
    if not deleted:
        raise HTTPException(404, f"Alert {alert_id} nicht gefunden")
    return {"deleted": True, "alert_id": alert_id}


# ── Risiko-Dashboard ──────────────────────────────────────────────────────────

@app.get("/api/risk")
async def get_risk():
    import math
    positions = _portfolio_service.get_positions(price_fn=_state.price)
    summary   = _portfolio_service.get_summary(price_fn=_state.price)

    total_val = summary.positions_value_chf or 1.0
    concentration: List[Dict] = []

    # Pro-Symbol: Volatilität aus Preishistorie
    weighted_var_sum = 0.0
    for pos in positions:
        sym   = pos.symbol
        hist  = list(_state.history.get(sym, []))
        fx    = settings.usd_chf_rate if pos.currency == "USD" else 1.0
        daily_vol = 0.018  # Default
        if len(hist) >= 10:
            rets = [(hist[i] - hist[i-1]) / hist[i-1] for i in range(1, len(hist)) if hist[i-1] != 0]
            if rets:
                mean = sum(rets) / len(rets)
                daily_vol = math.sqrt(sum((r - mean) ** 2 for r in rets) / len(rets))

        weight    = pos.value_chf / total_val
        var_1d    = pos.value_chf * 1.645 * daily_vol  # 95% VaR 1-Tag
        weighted_var_sum += var_1d * weight

        concentration.append({
            "symbol":    sym,
            "value_chf": pos.value_chf,
            "weight_pct": pos.weight_pct,
            "daily_vol_pct": round(daily_vol * 100, 2),
            "var_95_chf": round(var_1d, 2),
        })

    portfolio_var = round(weighted_var_sum, 2)

    # Szenarien
    scenarios = []
    for name, shock in [("Bull (+15%)", 0.15), ("Base (0%)", 0.0), ("Bear (-20%)", -0.20), ("Crash (-35%)", -0.35)]:
        pnl = round(total_val * shock, 2)
        scenarios.append({"scenario": name, "shock_pct": shock * 100, "pnl_chf": pnl,
                          "new_value": round(total_val + pnl, 2)})

    # Max Drawdown aus Portfolio-Preishistorie (approximiert)
    all_hist = [list(_state.history.get(p.symbol, [])) for p in positions]
    max_hist_len = max((len(h) for h in all_hist), default=0)
    portfolio_values = []
    for i in range(max_hist_len):
        pv = 0.0
        for idx, pos in enumerate(positions):
            h = all_hist[idx]
            if i < len(h):
                fx = settings.usd_chf_rate if pos.currency == "USD" else 1.0
                pv += h[i] * pos.quantity * fx
        portfolio_values.append(pv)

    max_dd = 0.0
    peak = portfolio_values[0] if portfolio_values else 1.0
    for v in portfolio_values:
        if v > peak:
            peak = v
        dd = (peak - v) / peak if peak else 0
        if dd > max_dd:
            max_dd = dd

    return {
        "portfolio_value_chf": round(total_val, 2),
        "var_95_1d_chf":       portfolio_var,
        "var_95_1d_pct":       round(portfolio_var / total_val * 100, 2) if total_val else 0,
        "max_drawdown_pct":    round(max_dd * 100, 2),
        "concentration":       sorted(concentration, key=lambda x: x["weight_pct"], reverse=True),
        "scenarios":           scenarios,
        "num_positions":       len(positions),
    }


# ── Dominance Engine ──────────────────────────────────────────────────────────

from app.layers.interpretation.dominance_engine import DominanceEngine as _DominanceEngineClass

_dominance_engine = _DominanceEngineClass()


@app.get("/api/dominance")
async def get_dominance():
    """Erkennt die aktuell dominante Marktebene (6 Ebenen) mit Stärke und Trend."""
    try:
        # ── RSI / Momentum / Volume aus gecachter Preishistorie berechnen ──
        rsi_values:    list[float] = []
        momentum_values: list[float] = []
        volume_ratios:  list[float] = []

        for sym in TRACKED_SYMBOLS:
            try:
                hist    = list(_state.history.get(sym, []))
                volumes = list(_state.volumes.get(sym, []))
            except Exception as exc:
                logger.warning("dominance: Fehler beim Lesen von History für %s: %s", sym, exc)
                continue

            if len(hist) < 15:
                logger.debug("dominance: %s hat nur %d Preispunkte — übersprungen", sym, len(hist))
                continue

            # RSI-Proxy (14 Perioden)
            gains  = [max(0.0, hist[i] - hist[i - 1]) for i in range(len(hist) - 14, len(hist))]
            losses = [max(0.0, hist[i - 1] - hist[i]) for i in range(len(hist) - 14, len(hist))]
            avg_g  = sum(gains)  / 14 if gains  else 0.0
            avg_l  = max(sum(losses) / 14, 0.001) if losses else 0.001  # nie 0 — sonst ZeroDivisionError
            rsi    = 100 - 100 / (1 + (avg_g / avg_l if avg_l != 0 else 0.0))
            rsi_values.append(rsi)
            logger.debug("dominance: %s RSI=%.1f", sym, rsi)

            # 5-Tage Momentum
            if len(hist) >= 5:
                base = hist[-5] if hist[-5] != 0 else 0.001
                m5 = (hist[-1] - hist[-5]) / base * 100
                momentum_values.append(m5)

            # Volume-Ratio (aktuell / 20T-Durchschnitt)
            if len(volumes) >= 20:
                avg_vol  = sum(volumes[-20:]) / 20
                curr_vol = volumes[-1] if volumes else avg_vol
                volume_ratios.append(curr_vol / avg_vol if avg_vol > 0 else 1.0)

        rsi_avg      = sum(rsi_values)       / len(rsi_values)       if rsi_values      else 50.0
        momentum_5d  = sum(momentum_values)  / len(momentum_values)  if momentum_values else 0.0
        volume_ratio = sum(volume_ratios)    / len(volume_ratios)    if volume_ratios   else 1.0

        # ── Fund-Score Durchschnitt ──
        fund_avg = (
            sum(v.get("fundamental", 70) for v in _FUND_SCORES.values())
            / max(len(_FUND_SCORES), 1)
        )

        # ── Regime — sicher lesen ──
        try:
            regime_type = _current_regime.regime_type
        except AttributeError:
            logger.warning("dominance: _current_regime nicht initialisiert — verwende 'sideways'")
            regime_type = "sideways"

        # ── Makro-Daten — sicher lesen ──
        try:
            vix        = float(_MACRO.vix or 20.0)
            fear_greed = float(_MACRO.fear_greed_index or 50.0)
            yield_curve = float(_MACRO.yield_curve_10y_2y or 0.0)
            fed_rate   = float(_MACRO.fed_rate or 3.5)
        except AttributeError as exc:
            logger.warning("dominance: Makro-Daten unvollständig (%s) — verwende Defaults", exc)
            vix, fear_greed, yield_curve, fed_rate = 20.0, 50.0, 0.0, 3.5

        logger.debug(
            "dominance: assess() vix=%.1f fg=%.0f yc=%.2f rate=%.2f rsi=%.1f mom=%.2f vol=%.2f fund=%.1f regime=%s",
            vix, fear_greed, yield_curve, fed_rate, rsi_avg, momentum_5d, volume_ratio, fund_avg, regime_type,
        )

        state = _dominance_engine.assess(
            vix                 = vix,
            fear_greed          = fear_greed,
            yield_curve         = yield_curve,
            fed_rate            = fed_rate,
            rsi_avg             = rsi_avg,
            volume_ratio        = volume_ratio,
            momentum_5d         = momentum_5d,
            fund_score_avg      = fund_avg,
            narrative_intensity = 0.4,
            regime_type         = regime_type,
        )

        result = {**state.model_dump(), "assessed_at": datetime.utcnow().isoformat(), "error": None}
        logger.info(
            "dominance: dominant=%s stärke=%.0f%% gaining=%s losing=%s",
            state.dominant_layer, state.dominance_strength * 100,
            state.gaining_layers, state.losing_layers,
        )
        return result

    except Exception as exc:
        logger.error("dominance: Unerwarteter Fehler — gebe Fallback zurück: %s", exc, exc_info=True)
        return {
            "dominant_layer":        "unknown",
            "dominant_label":        "Unbekannt",
            "dominance_strength":    0.0,
            "layer_scores":          {k: 0.0 for k in ("fundamental", "geopolitical", "liquidity", "psychology", "microstructure", "narrative")},
            "gaining_layers":        [],
            "losing_layers":         [],
            "narrative_explanation": f"Dominanz-Analyse vorübergehend nicht verfügbar: {exc}",
            "assessed_at":           datetime.utcnow().isoformat(),
            "error":                 str(exc),
        }


# ── Portfolio-Analyse ─────────────────────────────────────────────────────────

from app.services.portfolio_analyzer import PortfolioAnalyzer as _PortfolioAnalyzerClass

_portfolio_analyzer = _PortfolioAnalyzerClass()


@app.get("/api/portfolio/analysis")
async def get_portfolio_analysis():
    """Vollständige Portfolio-Analyse: Klumpenrisiken, Regionen, Sektoren,
    Währungen und Schritt-für-Schritt-Empfehlung je Position."""
    price_cache = {sym: _state.price(sym) for sym in TRACKED_SYMBOLS}
    price_histories = {
        sym: list(_state.history.get(sym, []))
        for sym in TRACKED_SYMBOLS
    }
    result = _portfolio_analyzer.analyze(
        positions       = _MY_POSITIONS,
        price_cache     = price_cache,
        price_histories = price_histories,
        fund_scores     = _FUND_SCORES,
        regime_type     = _current_regime.regime_type,
        vix             = _MACRO.vix or 20.0,
        fear_greed      = _MACRO.fear_greed_index or 50.0,
        fed_rate        = _MACRO.fed_rate or 3.5,
        usd_chf         = settings.usd_chf_rate,
    )
    return result.model_dump()


# ── Learning: Evaluationen & Prompt-Vorschläge ────────────────────────────────

from app.layers.learning.feedback_engine import FeedbackEngine as _FeedbackEngineClass
from app.layers.learning.prompt_optimizer import PromptOptimizer as _PromptOptimizerClass

_feedback_engine   = _FeedbackEngineClass()
_prompt_optimizer  = _PromptOptimizerClass(_feedback_engine)


@app.get("/api/learning/evaluations")
async def get_evaluations():
    """Vergangene Empfehlungs-Evaluationen mit Fehlerklassifikation."""
    evals = _feedback_engine.get_all()
    stats = _feedback_engine.get_stats()
    return {
        "evaluations": [e.model_dump() for e in evals],
        "stats":       stats,
    }


@app.get("/api/learning/prompt-suggestions")
async def get_prompt_suggestions():
    """Optimierungsvorschläge als direkt nutzbare Prompts — basierend auf Fehleranalyse."""
    suggestions = _prompt_optimizer.generate_suggestions()
    return [s.model_dump() for s in suggestions]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
