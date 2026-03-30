/**
 * TradeApp — API Service
 * Alle Endpunkte des FastAPI Backends auf Port 8000.
 */

// Re-export fetch* functions used by hooks/useApi.ts
export {
  fetchHealth,
  fetchRegime,
  fetchSignals,
  fetchSignalForSymbol,
  fetchRecommendations,
  fetchRecommendationForSymbol,
  fetchPortfolio,
  fetchMacro,
  fetchQuote,
  fetchJournalStats,
  fetchBiasAnalysis,
  fetchCycle,
  fetchLiquidity,
  fetchExpectations,
  fetchHypothesis,
  runBacktest,
  fetchBacktestResult,
  fetchBacktestTrades,
  fetchBacktestEquity,
  fetchPortfolioSummary,
  createPortfolioTrade,
  deletePortfolioTrade,
  fetchWatchlist,
  addToWatchlist,
  removeFromWatchlist,
  fetchAllNews,
  fetchNewsForSymbol,
  fetchAlerts,
  fetchTriggeredAlerts,
  createAlert,
  deleteAlert,
  fetchRisk,
  fetchDominance,
  fetchPortfolioAnalysis,
  fetchEvaluations,
  fetchPromptSuggestions,
} from './api/index'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// ── Hilfsfunktionen ───────────────────────────────────────────────────────────

async function fetchAPI<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`)
  if (!res.ok) throw new Error(`API ${res.status}: ${path}`)
  return res.json()
}

async function postAPI<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`API ${res.status}: ${path}`)
  return res.json()
}

// ── Reality Layer ─────────────────────────────────────────────────────────────

export const getHealth    = ()         => fetchAPI<Health>('/health')
export const getQuote     = (sym: string) => fetchAPI<Quote>(`/api/quotes/${sym}`)
export const getMacro     = ()         => fetchAPI<MacroData>('/api/macro')

// ── Interpretation Layer ──────────────────────────────────────────────────────

export const getRegime    = ()                    => fetchAPI<Regime>('/api/regime')
export const getSignals   = (minScore = 70)       => fetchAPI<Signal[]>(`/api/signals?min_score=${minScore}`)
export const getSignal    = (sym: string)         => fetchAPI<Signal>(`/api/signals/${sym}`)

// ── Decision Engine ───────────────────────────────────────────────────────────

export const getRecommendations = (minScore = 65) =>
  fetchAPI<Recommendation[]>(`/api/recommendations?min_score=${minScore}`)
export const getRecommendation  = (sym: string)   =>
  fetchAPI<Recommendation>(`/api/recommendations/${sym}`)

// ── Portfolio ─────────────────────────────────────────────────────────────────

export const getPortfolio = () => fetchAPI<Portfolio>('/api/portfolio')

// ── Orders ────────────────────────────────────────────────────────────────────

export const validateOrder = (order: OrderRequest) =>
  postAPI<OrderValidation>('/api/orders/validate', order)

export const executeOrder  = (order: OrderRequest) =>
  postAPI<OrderResult>('/api/orders/execute', order)

// ── Behavioral Layer ──────────────────────────────────────────────────────────

export const getJournalStats  = ()           => fetchAPI<JournalStats>('/api/journal/stats')
export const getBiasAnalysis  = (sym: string) =>
  fetchAPI<BiasAnalysis>(`/api/journal/bias-analysis/${sym}`)

// ── KI-Analyse ────────────────────────────────────────────────────────────────

export const analyzeWithAI = (subject: string, question?: string) =>
  postAPI<AIAnalysis>('/api/ai/analyze', { subject, question })

// ── Tax ───────────────────────────────────────────────────────────────────────

export const calculateTax = (year = 2024) =>
  postAPI<TaxResult>('/api/tax/calculate', {}, )

// ── Typen ─────────────────────────────────────────────────────────────────────

export interface Health {
  status: string
  ibkr_connected: boolean
  mock_feed: boolean
  redis: boolean
  database: boolean
  regime: string
  cached_symbols: string[]
  timestamp: number
}

export interface Quote {
  symbol: string
  name: string
  price: number
  change: number
  change_percent: number
  volume: number
  currency: string
  exchange: string
  source: string
  timestamp: number
}

export interface MacroData {
  fed_rate: number
  snb_rate: number
  ecb_rate: number
  boj_rate: number
  cpi_us: number
  nfp_latest: number
  nfp_expected: number
  unemployment: number
  oil_wti: number
  gold_xau_usd: number
  silver_xag_usd: number
  eur_chf: number
  usd_chf: number
  vix: number
  fear_greed_index: number
  yield_curve_10y_2y: number
  last_updated: number
}

export interface Regime {
  regime_type: string
  sub_regime: string | null
  label: string
  confidence: number
  strength: number
  is_risk_off: boolean
  vix_category: string
  characteristics: string[]
  active_risks: string[]
  max_position_size_pct: number
  recommended_cash_buffer_pct: number
  detected_at: string
}

export interface ScoreBreakdown {
  total: number
  fundamental: number
  technical: number
  management: number
  sentiment: number
  geopolitical: number
  macro: number
  verdict: string
  confidence: string
}

export interface Signal {
  id: string
  symbol: string
  name: string
  verdict: string
  strength: string
  price: number
  stop_loss: number
  target: number
  crv: number
  score: ScoreBreakdown
  reasons: string[]
  timestamp: number
}

export interface PositionSizing {
  suggested_pct: number
  suggested_chf: number | null
  suggested_shares: number | null
  max_pct_by_regime: number
  kelly_fraction: number | null
  risk_per_trade_chf: number | null
  risk_pct_of_portfolio: number | null
}

export interface Recommendation {
  id: string
  symbol: string
  name: string
  action: string
  priority: string
  rationale: string
  entry_price: number | null
  stop_loss: number | null
  target_price: number | null
  crv: number | null
  composite_score: number | null
  regime_summary: string | null
  has_bias_warning: boolean
  bias_score: number
  detected_biases: string[]
  key_risks: string[]
  sizing: PositionSizing | null
  created_at: string
}

export interface Position {
  id: string
  symbol: string
  name: string
  quantity: number
  avg_price: number
  current_price: number
  currency: string
  exchange: string
  value_chf: number
  cost_basis_chf: number
  pnl_chf: number
  pnl_percent: number
  weight_percent: number
  score?: number
  sector?: string
  source?: string
}

export interface Portfolio {
  total_value_chf: number
  total_pnl_chf: number
  total_pnl_percent: number
  today_pnl_chf: number
  today_pnl_percent: number
  cash_chf: number
  score: number
  positions: Position[]
  last_updated: number
}

export interface OrderRequest {
  symbol: string
  direction: string
  amount_chf?: number
  quantity?: number
  order_type?: string
  stop_loss?: number
  take_profit?: number
}

export interface OrderValidation {
  valid: boolean
  errors: string[]
  warnings: string[]
  estimated_shares: number | null
  estimated_cost_chf: number
  stamp_tax_chf: number
  crv: number | null
  entry_price: number
}

export interface OrderResult {
  status: string
  order_id: string
  symbol: string
  direction: string
  message: string
}

export interface JournalStats {
  total_trades: number
  win_rate: number
  avg_win_chf: number
  avg_loss_chf: number
  avg_crv: number
  profit_factor: number
  potential_alpha_chf: number
  bias_stats: Record<string, { count: number; cost_chf: number }>
}

export interface BiasAnalysis {
  overall_score: number
  detected_biases: string[]
  warnings: string[]
  recommendation_adjusted: boolean
  quality_score: number
}

export interface AIAnalysis {
  analysis: string
  subject: string
  generated_at: string
}

export interface TaxResult {
  year: number
  realized_gains_chf: number
  stamp_tax_paid_chf: number
  verrechnungssteuer_chf: number
  vermoegenssteuerwert_chf: number
  note: string
}
