"""
TradeApp Backend — FastAPI
Empfohlene Technologie: Python 3.12 + FastAPI + PostgreSQL + Redis
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum
import asyncio
import json
import os

# ── App Setup ─────────────────────────────────────────
app = FastAPI(
    title="TradeApp API",
    description="Professional Trading Dashboard — CHF Portfolio Management",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://tradeapp.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Schemas ───────────────────────────────────────────

class OrderType(str, Enum):
    market = "market"
    limit = "limit"
    stop = "stop"
    stop_limit = "stop_limit"
    oco = "oco"

class SignalVerdict(str, Enum):
    buy = "buy"
    hold = "hold"
    sell = "sell"
    avoid = "avoid"

class Quote(BaseModel):
    symbol: str
    name: str
    price: float
    change: float
    change_percent: float
    volume: int
    market_cap: Optional[float]
    currency: str
    exchange: str
    timestamp: int

class Position(BaseModel):
    id: str
    symbol: str
    name: str
    quantity: float
    avg_price: float
    current_price: float
    currency: str
    exchange: str
    value_chf: float
    cost_basis_chf: float
    pnl_chf: float
    pnl_percent: float
    weight_percent: float
    score: Optional[int]
    sector: Optional[str]

class Portfolio(BaseModel):
    total_value_chf: float
    total_pnl_chf: float
    total_pnl_percent: float
    today_pnl_chf: float
    today_pnl_percent: float
    cash_chf: float
    score: int
    positions: List[Position]
    last_updated: int

class ScoreBreakdown(BaseModel):
    fundamental: int = Field(ge=0, le=100)
    technical: int = Field(ge=0, le=100)
    management: int = Field(ge=0, le=100)
    sentiment: int = Field(ge=0, le=100)
    geopolitical: int = Field(ge=0, le=100)
    macro: int = Field(ge=0, le=100)
    total: int = Field(ge=0, le=100)
    verdict: SignalVerdict
    confidence: str

class Signal(BaseModel):
    id: str
    symbol: str
    name: str
    verdict: SignalVerdict
    strength: str
    price: float
    stop_loss: float
    target: float
    crv: float
    score: ScoreBreakdown
    reasons: List[str]
    timestamp: int

class OrderRequest(BaseModel):
    symbol: str
    direction: str  # "buy" | "sell"
    quantity: Optional[float]
    amount_chf: Optional[float]
    order_type: OrderType
    limit_price: Optional[float]
    stop_price: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]
    oco_enabled: bool = False

class OrderValidation(BaseModel):
    valid: bool
    errors: List[str]
    warnings: List[str]
    estimated_shares: Optional[float]
    estimated_cost_chf: float
    stamp_tax_chf: float
    crv: Optional[float]
    risk_chf: Optional[float]
    risk_percent: Optional[float]

class TradeEntry(BaseModel):
    id: str
    symbol: str
    name: str
    direction: str
    quantity: float
    entry_price: float
    exit_price: Optional[float]
    stop_loss: float
    target: float
    currency: str
    status: str
    opened_at: int
    closed_at: Optional[int]
    pnl_chf: Optional[float]
    pnl_percent: Optional[float]
    holding_days: Optional[int]
    score_at_entry: Optional[int]
    crv_achieved: Optional[float]
    bias: Optional[List[str]]
    notes: Optional[str]

class MacroData(BaseModel):
    fed_rate: float
    snb_rate: float
    ecb_rate: float
    boj_rate: float
    cpi_us: float
    nfp_latest: float
    nfp_expected: float
    unemployment: float
    oil_wti: float
    gold_xau_usd: float
    silver_xag_usd: float
    eur_chf: float
    usd_chf: float
    vix: float
    fear_greed_index: int
    yield_curve_10y_2y: float
    last_updated: int

class AIAnalysisRequest(BaseModel):
    subject: str  # "MSFT", "macro", "portfolio", etc.
    context: Optional[str]
    portfolio_value: Optional[float]
    question: Optional[str]

# ── Mock Data (replace with real DB queries in production) ──

MOCK_MACRO = MacroData(
    fed_rate=3.75, snb_rate=0.50, ecb_rate=2.40, boj_rate=0.50,
    cpi_us=2.4, nfp_latest=-92000, nfp_expected=60000, unemployment=4.4,
    oil_wti=99.40, gold_xau_usd=4850.0, silver_xag_usd=70.10,
    eur_chf=0.9372, usd_chf=0.889, vix=24.5, fear_greed_index=32,
    yield_curve_10y_2y=0.27, last_updated=int(datetime.now().timestamp())
)

MOCK_SIGNALS = [
    Signal(id="s1", symbol="NVDA", name="NVIDIA Corporation", verdict=SignalVerdict.buy,
           strength="strong", price=879.50, stop_loss=798.0, target=1050.0, crv=3.1,
           score=ScoreBreakdown(fundamental=88, technical=82, management=86, sentiment=79,
                                 geopolitical=72, macro=76, total=85, verdict=SignalVerdict.buy, confidence="high"),
           reasons=["Datacenter +122% YoY", "RSI 58 nicht überkauft", "AI-Infrastruktur Megatrend", "CRV 1:3.1"],
           timestamp=int(datetime.now().timestamp())),
    Signal(id="s2", symbol="MSFT", name="Microsoft Corporation", verdict=SignalVerdict.buy,
           strength="strong", price=371.04, stop_loss=344.0, target=445.0, crv=2.8,
           score=ScoreBreakdown(fundamental=84, technical=62, management=91, sentiment=58,
                                 geopolitical=55, macro=68, total=80, verdict=SignalVerdict.buy, confidence="high"),
           reasons=["Azure +29% YoY", "−33% vom ATH Übertreibung", "P/E 22.3x Mehrjahrestief", "CEO Score 91"],
           timestamp=int(datetime.now().timestamp())),
]

# ── Routes ────────────────────────────────────────────

@app.get("/")
async def root():
    return {"status": "TradeApp API v1.0.0", "docs": "/api/docs"}

# Market Data
@app.get("/api/quotes/{symbol}", response_model=Quote)
async def get_quote(symbol: str):
    """Echtzeit-Kurs für ein Symbol. Prod: IBKR TWS API oder Alpha Vantage."""
    mock = {
        "MSFT": Quote(symbol="MSFT", name="Microsoft", price=371.04, change=-1.70, change_percent=-0.46,
                      volume=24_500_000, market_cap=2.76e12, currency="USD", exchange="NASDAQ",
                      timestamp=int(datetime.now().timestamp())),
        "NVDA": Quote(symbol="NVDA", name="NVIDIA", price=879.50, change=20.88, change_percent=2.43,
                      volume=48_200_000, market_cap=2.16e12, currency="USD", exchange="NASDAQ",
                      timestamp=int(datetime.now().timestamp())),
    }
    if symbol.upper() not in mock:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} nicht gefunden")
    return mock[symbol.upper()]

@app.get("/api/macro", response_model=MacroData)
async def get_macro():
    """Makroökonomische Indikatoren. Prod: Fed API, ECB API, Alpha Vantage."""
    return MOCK_MACRO

@app.get("/api/signals", response_model=List[Signal])
async def get_signals(min_score: int = 70, max_results: int = 10):
    """Aktuelle Handelssignale basierend auf Scoring-Modell."""
    filtered = [s for s in MOCK_SIGNALS if s.score.total >= min_score]
    return filtered[:max_results]

@app.get("/api/portfolio", response_model=Portfolio)
async def get_portfolio():
    """Portfolio-Daten. Prod: IBKR Client Portal API."""
    return Portfolio(
        total_value_chf=284620, total_pnl_chf=11820, total_pnl_percent=4.33,
        today_pnl_chf=1240, today_pnl_percent=0.44, cash_chf=113080, score=74,
        last_updated=int(datetime.now().timestamp()),
        positions=[
            Position(id="p1", symbol="NVDA", name="NVIDIA", quantity=59, avg_price=748.20,
                     current_price=879.50, currency="USD", exchange="NASDAQ",
                     value_chf=52100, cost_basis_chf=44144, pnl_chf=7956, pnl_percent=18.02,
                     weight_percent=18.3, score=85, sector="Technology"),
            Position(id="p2", symbol="MSFT", name="Microsoft", quantity=130, avg_price=405.10,
                     current_price=371.04, currency="USD", exchange="NASDAQ",
                     value_chf=48240, cost_basis_chf=52663, pnl_chf=-4423, pnl_percent=-8.40,
                     weight_percent=17.0, score=80, sector="Technology"),
        ]
    )

# Order Management
@app.post("/api/orders/validate", response_model=OrderValidation)
async def validate_order(order: OrderRequest):
    """
    Validiert eine Order vor Ausführung.
    Prüft: 1%-Regel, CRV, Stop-Loss, Positionsgrösse, Stempelsteuer.
    """
    portfolio_value = 284620.0
    price = 371.04  # Prod: Echtzeit-Kurs abrufen

    # Berechnung
    if order.amount_chf:
        shares = order.amount_chf / price
        cost = order.amount_chf
    elif order.quantity:
        shares = order.quantity
        cost = shares * price
    else:
        raise HTTPException(status_code=400, detail="Menge oder Betrag erforderlich")

    stamp_tax = cost * 0.00075  # CH Stempelsteuer 0.075%
    errors = []
    warnings = []

    # 1%-Regel
    if order.stop_loss:
        risk_per_share = abs(price - order.stop_loss)
        risk_chf = risk_per_share * shares
        risk_percent = (risk_chf / portfolio_value) * 100
        if risk_percent > 2.0:
            errors.append(f"Risiko {risk_percent:.1f}% überschreitet 2%-Limit")
        elif risk_percent > 1.0:
            warnings.append(f"Risiko {risk_percent:.1f}% — empfohlen: max 1%")
    else:
        warnings.append("Kein Stop-Loss gesetzt — Pflichtfeld in der App")
        risk_chf = None
        risk_percent = None

    # CRV-Check
    crv = None
    if order.stop_loss and order.take_profit:
        risk_ps  = abs(price - order.stop_loss)
        reward_ps = abs(order.take_profit - price)
        crv = round(reward_ps / risk_ps, 2) if risk_ps > 0 else None
        if crv and crv < 2.0:
            errors.append(f"CRV {crv} unter Mindest-CRV 1:2 — Trade nicht empfohlen")

    # Positionsgrösse
    if cost / portfolio_value > 0.10:
        errors.append(f"Position {cost/portfolio_value*100:.1f}% überschreitet 10%-Limit")
    elif cost / portfolio_value > 0.05:
        warnings.append(f"Position {cost/portfolio_value*100:.1f}% — empfohlen: max 5%")

    return OrderValidation(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        estimated_shares=round(shares, 2),
        estimated_cost_chf=round(cost, 2),
        stamp_tax_chf=round(stamp_tax, 2),
        crv=crv,
        risk_chf=round(risk_chf, 2) if risk_chf else None,
        risk_percent=round(risk_percent, 2) if risk_percent else None,
    )

@app.post("/api/orders/execute")
async def execute_order(order: OrderRequest):
    """
    Führt Order via IBKR TWS API aus.
    Prod: ib_insync Library oder IBKR Client Portal REST API.
    """
    # In Produktion:
    # from ib_insync import IB, Stock, MarketOrder, LimitOrder
    # ib = IB()
    # ib.connect('127.0.0.1', 7497, clientId=1)
    # contract = Stock(order.symbol, 'SMART', 'USD')
    # ib_order = MarketOrder(order.direction.upper(), order.quantity)
    # trade = ib.placeOrder(contract, ib_order)
    return {
        "status": "executed",
        "order_id": f"ORD-{int(datetime.now().timestamp())}",
        "symbol": order.symbol,
        "direction": order.direction,
        "message": f"Order für {order.symbol} erfolgreich platziert (Demo-Modus)"
    }

# AI Analysis
@app.post("/api/ai/analyze")
async def ai_analyze(request: AIAnalysisRequest):
    """
    KI-Analyse via Claude API.
    Prod: anthropic.Anthropic().messages.create(...)
    """
    # In Produktion:
    # import anthropic
    # client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    # message = client.messages.create(
    #     model="claude-opus-4-6",
    #     max_tokens=2000,
    #     messages=[{"role": "user", "content": f"Analysiere {request.subject}..."}]
    # )
    # return {"analysis": message.content[0].text}
    return {
        "analysis": f"Demo: Vollständige KI-Analyse für '{request.subject}' — In der Prod-App via Claude API.",
        "subject": request.subject,
        "generated_at": datetime.now().isoformat()
    }

# Journal
@app.get("/api/journal/stats")
async def get_journal_stats():
    """Journal-Statistiken und Bias-Analyse."""
    return {
        "total_trades": 34,
        "win_rate": 0.62,
        "avg_win_chf": 3840,
        "avg_loss_chf": -2960,
        "avg_crv": 1.29,
        "profit_factor": 1.81,
        "potential_alpha_chf": 8240,
        "bias_stats": {
            "fomo": {"count": 8, "cost_chf": 4120},
            "loss_aversion": {"count": 6, "cost_chf": 2880},
            "revenge_trade": {"count": 4, "cost_chf": 980},
            "anchoring": {"count": 5, "cost_chf": 620},
            "overconfidence": {"count": 3, "cost_chf": 840},
            "rational": {"count": 20, "cost_chf": 0},
        }
    }

# WebSocket for live quotes
class ConnectionManager:
    def __init__(self):
        self.active: List[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        self.active.remove(ws)

    async def broadcast(self, data: dict):
        for ws in self.active:
            try:
                await ws.send_json(data)
            except Exception:
                pass

manager = ConnectionManager()

@app.websocket("/ws/quotes")
async def websocket_quotes(websocket: WebSocket):
    """
    WebSocket für Live-Kurse.
    Prod: IBKR TWS API Streaming + Redis Pub/Sub.
    """
    await manager.connect(websocket)
    try:
        while True:
            # Simuliere Live-Kurse (Prod: echte IBKR/Alpha Vantage Daten)
            import random
            await websocket.send_json({
                "type": "quote",
                "symbol": "MSFT",
                "price": round(371.04 + random.uniform(-0.5, 0.5), 2),
                "timestamp": int(datetime.now().timestamp())
            })
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Swiss Tax Helper
@app.post("/api/tax/calculate")
async def calculate_swiss_tax(year: int = 2026):
    """
    Schweizer Steuer-Assistent:
    - Stempelsteuer (0.075% / 0.15%)
    - Verrechnungssteuer
    - Vermögenssteuerwert per 31.12.
    """
    return {
        "year": year,
        "realized_gains_chf": 4792,
        "stamp_tax_paid_chf": 89.40,
        "withholding_tax_chf": 840,
        "withholding_reclaimable_chf": 840,
        "wealth_tax_value_chf": 284620,
        "notes": "Basierend auf ESTV-Kurse per 31.12. / Alle Angaben ohne Gewähr"
    }

# ── Main ──────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
