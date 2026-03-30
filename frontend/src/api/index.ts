import { apiClient } from './client'
import type {
  Quote, Portfolio, Signal, RegimeState, Recommendation,
  MacroSnapshot, BiasAnalysis, JournalStats, OrderRequest,
  OrderValidation, Health,
  MarketCycleState, LiquidityState, ExpectationModel, HypothesisSet,
  BacktestConfig, BacktestRunResponse, BacktestResult, TradeRecord, EquityCurvePoint,
  PortfolioSummary, PortfolioPosition, PortfolioTrade, PortfolioTradeCreate,
  WatchlistItem, WatchlistAdd, NewsItem, AlertConfig, AlertCreate, AlertEvent, RiskMetrics,
  DominanceState, PortfolioAnalysisResult, EvaluationResponse, PromptSuggestion,
} from './types'

// ── Health ────────────────────────────────────────────────────────────────────
export const fetchHealth = () =>
  apiClient.get<Health>('/health').then((r) => r.data)

// ── Market Data ───────────────────────────────────────────────────────────────
export const fetchQuote = (symbol: string) =>
  apiClient.get<Quote>(`/api/quotes/${symbol}`).then((r) => r.data)

export const fetchMacro = () =>
  apiClient.get<MacroSnapshot>('/api/macro').then((r) => r.data)

// ── Reality → Interpretation Layer ───────────────────────────────────────────
export const fetchRegime = () =>
  apiClient.get<RegimeState>('/api/regime').then((r) => r.data)

export const fetchSignals = (minScore = 65) =>
  apiClient.get<Signal[]>(`/api/signals?min_score=${minScore}`).then((r) => r.data)

export const fetchSignalForSymbol = (symbol: string) =>
  apiClient.get<Signal>(`/api/signals/${symbol}`).then((r) => r.data)

// ── Decision Engine ───────────────────────────────────────────────────────────
export const fetchRecommendations = () =>
  apiClient.get<Recommendation[]>('/api/recommendations').then((r) => r.data)

export const fetchRecommendationForSymbol = (symbol: string) =>
  apiClient.get<Recommendation>(`/api/recommendations/${symbol}`).then((r) => r.data)

// ── Portfolio (legacy) ────────────────────────────────────────────────────────
export const fetchPortfolio = () =>
  apiClient.get<Portfolio>('/api/portfolio').then((r) => r.data)

// ── Portfolio Management ──────────────────────────────────────────────────────
export const fetchPortfolioSummary = () =>
  apiClient.get<PortfolioSummary>('/api/portfolio/summary').then((r) => r.data)

export const fetchPortfolioPositions = () =>
  apiClient.get<PortfolioPosition[]>('/api/portfolio/positions').then((r) => r.data)

export const fetchPortfolioTrades = () =>
  apiClient.get<PortfolioTrade[]>('/api/portfolio/trades').then((r) => r.data)

export const createPortfolioTrade = (data: PortfolioTradeCreate) =>
  apiClient.post<PortfolioTrade>('/api/portfolio/trades', data).then((r) => r.data)

export const deletePortfolioTrade = (id: string) =>
  apiClient.delete<{ deleted: boolean; trade_id: string }>(`/api/portfolio/trades/${id}`).then((r) => r.data)

// ── Behavioral / Journal ──────────────────────────────────────────────────────
export const fetchJournalStats = () =>
  apiClient.get<JournalStats>('/api/journal/stats').then((r) => r.data)

export const fetchBiasAnalysis = (symbol: string) =>
  apiClient.get<BiasAnalysis>(`/api/journal/bias-analysis/${symbol}`).then((r) => r.data)

// ── Orders ────────────────────────────────────────────────────────────────────
export const validateOrder = (order: OrderRequest) =>
  apiClient.post<OrderValidation>('/api/orders/validate', order).then((r) => r.data)

export const executeOrder = (order: OrderRequest) =>
  apiClient.post('/api/orders/execute', order).then((r) => r.data)

// ── Market Cycle ──────────────────────────────────────────────────────────────
export const fetchCycle = () =>
  apiClient.get<MarketCycleState>('/api/cycle').then((r) => r.data)

// ── Liquidity ─────────────────────────────────────────────────────────────────
export const fetchLiquidity = () =>
  apiClient.get<LiquidityState>('/api/liquidity').then((r) => r.data)

// ── Expectations ──────────────────────────────────────────────────────────────
export const fetchExpectations = (symbol?: string) =>
  apiClient
    .get<Record<string, ExpectationModel> | ExpectationModel>(
      symbol ? `/api/expectations?symbol=${symbol}` : '/api/expectations'
    )
    .then((r) => r.data)

// ── Hypothesis ────────────────────────────────────────────────────────────────
export const fetchHypothesis = (symbol: string) =>
  apiClient.get<HypothesisSet>(`/api/hypothesis/${symbol}`).then((r) => r.data)

// ── Backtesting ───────────────────────────────────────────────────────────────
export const runBacktest = (config: BacktestConfig) =>
  apiClient.post<BacktestRunResponse>('/api/backtest/run', config).then((r) => r.data)

export const fetchBacktestResult = (id: string) =>
  apiClient.get<BacktestResult>(`/api/backtest/results/${id}`).then((r) => r.data)

export const fetchBacktestTrades = (id: string) =>
  apiClient.get<{ backtest_id: string; symbol: string; trades: TradeRecord[] }>(
    `/api/backtest/trades/${id}`
  ).then((r) => r.data)

export const fetchBacktestEquity = (id: string) =>
  apiClient.get<{ backtest_id: string; equity_curve: EquityCurvePoint[]; initial_capital: number; final_equity: number }>(
    `/api/backtest/equity/${id}`
  ).then((r) => r.data)

// ── Watchlist ─────────────────────────────────────────────────────────────────
export const fetchWatchlist = () =>
  apiClient.get<WatchlistItem[]>('/api/watchlist').then((r) => r.data)

export const addToWatchlist = (data: WatchlistAdd) =>
  apiClient.post<WatchlistItem>('/api/watchlist', data).then((r) => r.data)

export const removeFromWatchlist = (symbol: string) =>
  apiClient.delete<{ removed: boolean; symbol: string }>(`/api/watchlist/${symbol}`).then((r) => r.data)

// ── News ──────────────────────────────────────────────────────────────────────
export const fetchAllNews = (limitPer = 3) =>
  apiClient.get<NewsItem[]>(`/api/news?limit_per=${limitPer}`).then((r) => r.data)

export const fetchNewsForSymbol = (symbol: string, limit = 8) =>
  apiClient.get<NewsItem[]>(`/api/news/${symbol}?limit=${limit}`).then((r) => r.data)

// ── Alerts ────────────────────────────────────────────────────────────────────
export const fetchAlerts = () =>
  apiClient.get<AlertConfig[]>('/api/alerts').then((r) => r.data)

export const fetchTriggeredAlerts = () =>
  apiClient.get<AlertEvent[]>('/api/alerts/triggered').then((r) => r.data)

export const createAlert = (data: AlertCreate) =>
  apiClient.post<AlertConfig>('/api/alerts', data).then((r) => r.data)

export const deleteAlert = (id: string) =>
  apiClient.delete<{ deleted: boolean; alert_id: string }>(`/api/alerts/${id}`).then((r) => r.data)

// ── Risk ──────────────────────────────────────────────────────────────────────
export const fetchRisk = () =>
  apiClient.get<RiskMetrics>('/api/risk').then((r) => r.data)

// ── Dominance Engine ──────────────────────────────────────────────────────────
export const fetchDominance = () =>
  apiClient.get<DominanceState>('/api/dominance').then((r) => r.data)

// ── Portfolio Analysis ────────────────────────────────────────────────────────
export const fetchPortfolioAnalysis = () =>
  apiClient.get<PortfolioAnalysisResult>('/api/portfolio/analysis').then((r) => r.data)

// ── Learning ──────────────────────────────────────────────────────────────────
export const fetchEvaluations = () =>
  apiClient.get<EvaluationResponse>('/api/learning/evaluations').then((r) => r.data)

export const fetchPromptSuggestions = () =>
  apiClient.get<PromptSuggestion[]>('/api/learning/prompt-suggestions').then((r) => r.data)
