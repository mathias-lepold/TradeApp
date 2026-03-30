// ─────────────────────────────────────────────────────────────────────────────
// Domain Types — spiegeln die Pydantic-Modelle des Backends 1:1 wider
// ─────────────────────────────────────────────────────────────────────────────

export type SignalType = 'buy' | 'sell' | 'hold' | 'avoid' | 'reduce' | 'add'
export type SignalStrength = 'strong' | 'moderate' | 'weak'
export type SignalConfidence = 'high' | 'medium' | 'low'
export type RecommendationAction = 'buy' | 'sell' | 'hold' | 'add' | 'reduce' | 'exit' | 'avoid' | 'rebalance' | 'wait'
export type RecommendationPriority = 'urgent' | 'high' | 'normal' | 'low'
export type RegimeType = 'bull_market' | 'bear_market' | 'sideways' | 'volatile' | 'crisis' | 'recovery'

// ── Regime ────────────────────────────────────────────────────────────────────

export interface MacroSnapshot {
  fed_rate?: number
  snb_rate?: number
  vix?: number
  yield_curve_10y_2y?: number
  usd_chf?: number
  eur_chf?: number
  gold_xau_usd?: number
  oil_wti?: number
  fear_greed_index?: number
  cpi_us?: number
  unemployment_us?: number
}

export interface RegimeState {
  id: string
  regime_type: RegimeType
  sub_regime?: string
  confidence: number
  strength: number
  macro: MacroSnapshot
  characteristics: string[]
  active_risks: string[]
  max_position_size_pct: number
  recommended_cash_buffer_pct: number
  sector_preferences: Record<string, number>
  detected_at: string
  is_risk_off: boolean
  vix_category: string
  label: string
}

// ── Signals ───────────────────────────────────────────────────────────────────

export interface ScoreBreakdown {
  fundamental: number
  technical: number
  management: number
  sentiment: number
  geopolitical: number
  macro: number
  total: number
  verdict: SignalType
  confidence: SignalConfidence
}

export interface TechnicalLevels {
  support_1?: number
  support_2?: number
  resistance_1?: number
  resistance_2?: number
  moving_avg_50?: number
  moving_avg_200?: number
  rsi_14?: number
  atr_14?: number
}

export interface Signal {
  id: string
  asset_symbol: string
  asset_name: string
  signal_type: SignalType
  strength: SignalStrength
  score: ScoreBreakdown
  price_at_signal: number
  stop_loss?: number
  target_price?: number
  technical_levels?: TechnicalLevels
  reasons: string[]
  risks: string[]
  catalyst?: string
  regime_context?: string
  layer_source: string
  generated_at: string
  valid_until?: string
  crv?: number
  is_expired: boolean
}

// ── Recommendations ───────────────────────────────────────────────────────────

export interface BiasRisk {
  overall_score: number
  detected_biases: string[]
  warnings: string[]
  recommendation_adjusted: boolean
}

export interface PositionSizing {
  suggested_pct: number
  suggested_chf?: number
  suggested_shares?: number
  max_pct_by_regime: number
  kelly_fraction?: number
  risk_per_trade_chf?: number
  risk_pct_of_portfolio?: number
}

export interface Recommendation {
  id: string
  asset_symbol: string
  asset_name: string
  action: RecommendationAction
  priority: RecommendationPriority
  rationale: string
  signal_id?: string
  regime_state_id?: string
  entry_price?: number
  stop_loss?: number
  target_price?: number
  sizing?: PositionSizing
  bias_risk?: BiasRisk
  regime_summary?: string
  key_risks: string[]
  conditions_to_invalidate: string[]
  decision_engine_version: string
  composite_score?: number
  crv?: number
  created_at: string
  valid_until?: string
  is_expired: boolean
  has_bias_warning: boolean
  no_trade_flag?: boolean
  base_hypothesis?: string
  counter_hypothesis?: string
  scenario_analysis?: Record<string, number>
  uncertainty_level?: string
}

// ── Portfolio ─────────────────────────────────────────────────────────────────

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
}

export interface Portfolio {
  total_value_chf: number
  total_pnl_chf: number
  total_pnl_percent: number
  cash_chf: number
  positions: Position[]
  last_updated: number
}

// ── Market Data ───────────────────────────────────────────────────────────────

export interface Quote {
  symbol: string
  name: string
  price: number
  change: number
  change_percent: number
  volume: number
  currency: string
  exchange: string
  source?: string
  timestamp: number
  from_cache: boolean
}

// ── Portfolio Management ──────────────────────────────────────────────────────

export type TradeAction = 'buy' | 'sell'

export interface PortfolioPosition {
  symbol:             string
  name:               string
  quantity:           number
  avg_entry_price:    number
  current_price:      number
  currency:           string
  unrealized_pnl:     number
  unrealized_pnl_pct: number
  realized_pnl:       number
  value_chf:          number
  cost_basis_chf:     number
  weight_pct:         number
  opened_at:          string | null
  data_source:        string
}

export interface PortfolioTrade {
  id:         string
  symbol:     string
  action:     TradeAction
  quantity:   number
  price:      number
  fees:       number
  currency:   string
  timestamp:  string
  notes:      string
  value_chf:  number
  total_chf:  number
}

export interface PortfolioSummary {
  starting_capital_chf: number
  total_value_chf:      number
  invested_chf:         number
  cash_chf:             number
  positions_value_chf:  number
  total_pnl_chf:        number
  total_pnl_pct:        number
  unrealized_pnl_chf:   number
  realized_pnl_chf:     number
  today_pnl_chf:        number
  positions:            PortfolioPosition[]
  trades:               PortfolioTrade[]
  num_trades:           number
  num_open_pos:         number
  last_updated:         string
}

export interface PortfolioTradeCreate {
  symbol:    string
  action:    TradeAction
  quantity:  number
  price:     number
  fees:      number
  currency:  string
  notes:     string
  timestamp?: string
}

// ── Watchlist ─────────────────────────────────────────────────────────────────

export interface WatchlistItem {
  id:           string
  symbol:       string
  name:         string
  target_price: number | null
  alert_price:  number | null
  notes:        string
  added_at:     string
  current_price: number
  change_pct:   number
  signal_score: number | null
  signal_type:  string | null
  data_source:  string
}

export interface WatchlistAdd {
  symbol:       string
  name?:        string
  target_price?: number
  notes?:       string
}

// ── News ──────────────────────────────────────────────────────────────────────

export type NewsSentiment = 'bullish' | 'bearish' | 'neutral'

export interface NewsItem {
  id:           string
  title:        string
  summary:      string
  symbol:       string
  source:       string
  url:          string
  published_at: string
  sentiment:    NewsSentiment
  is_mock:      boolean
}

// ── Alerts ────────────────────────────────────────────────────────────────────

export type AlertCondition =
  | 'price_above' | 'price_below'
  | 'signal_score_above' | 'signal_score_below'
  | 'regime_change'

export interface AlertConfig {
  id:              string
  symbol:          string
  condition:       AlertCondition
  threshold:       number
  active:          boolean
  triggered:       boolean
  triggered_at:    string | null
  triggered_value: number | null
  notes:           string
  created_at:      string
}

export interface AlertCreate {
  symbol:    string
  condition: AlertCondition
  threshold: number
  notes:     string
}

export interface AlertEvent {
  alert_id:        string
  symbol:          string
  condition:       AlertCondition
  threshold:       number
  triggered_value: number
  triggered_at:    string
  message:         string
}

// ── Risk ──────────────────────────────────────────────────────────────────────

export interface RiskConcentration {
  symbol:       string
  value_chf:    number
  weight_pct:   number
  daily_vol_pct: number
  var_95_chf:   number
}

export interface RiskScenario {
  scenario:  string
  shock_pct: number
  pnl_chf:   number
  new_value: number
}

export interface RiskMetrics {
  portfolio_value_chf: number
  var_95_1d_chf:       number
  var_95_1d_pct:       number
  max_drawdown_pct:    number
  concentration:       RiskConcentration[]
  scenarios:           RiskScenario[]
  num_positions:       number
}

// ── Health ────────────────────────────────────────────────────────────────────

export interface Health {
  status: string
  ibkr_connected: boolean
  redis: boolean
  database: boolean
  feed_mode?: 'yahoo' | 'mock'
  last_data_fetch?: string | null
  timestamp: number
}

// ── Journal ───────────────────────────────────────────────────────────────────

export interface BiasAnalysis extends BiasRisk {
  quality_score: number
}

export interface JournalStats {
  total_analyzed: number
  bias_counts: Record<string, number>
  avg_bias_score: number
  avg_quality_score: number
  most_common_bias: string | null
  bias_adjusted_decisions: number
}

// ── Market Cycle ──────────────────────────────────────────────────────────────

export type CyclePhase =
  | 'fundamental'
  | 'external_shock'
  | 'first_reaction'
  | 'psychological_overshoot'
  | 'stabilization'
  | 'return_to_fundamentals'

export interface PhaseIntensity {
  phase: CyclePhase
  intensity: number
  description: string
}

export interface MarketCycleState {
  active_phases: PhaseIntensity[]
  dominant_phase: CyclePhase
  transition_speed: number
  overall_instability: number
  signals: string[]
  detected_at: string
  regime?: string
}

// ── Liquidity ─────────────────────────────────────────────────────────────────

export type FundingCondition = 'ample' | 'normal' | 'tightening' | 'tight' | 'stressed'

export interface LiquidityState {
  liquidity_stress: number
  funding_conditions: FundingCondition
  forced_selling_risk: number
  bid_ask_spread_proxy: number
  market_depth_score: number
  vix_proxy: number
  signals: string[]
  assessed_at: string
}

// ── Expectations ──────────────────────────────────────────────────────────────

export interface ExpectationModel {
  asset_symbol: string
  consensus_expectation: number
  actual_outcome: number
  surprise_score: number
  expectation_gap: number
  revision_trend: 'up' | 'down' | 'neutral'
  implied_volatility_proxy: number
  confidence: number
  assessed_at: string
}

// ── Hypothesis ────────────────────────────────────────────────────────────────

export interface HypothesisScenario {
  title: string
  description: string
  confidence: number
  triggers: string[]
  invalidators: string[]
  price_target_pct?: number
  time_horizon_days?: number
}

export interface HypothesisSet {
  asset_symbol: string
  base_hypothesis: HypothesisScenario
  counter_hypothesis: HypothesisScenario
  alternative_scenarios: HypothesisScenario[]
  overall_conviction: number
  phase_transition_triggers: string[]
  generated_at: string
}

// ── Backtesting ───────────────────────────────────────────────────────────────

export interface BacktestConfig {
  symbol: string
  start_date: string   // ISO date "YYYY-MM-DD"
  end_date: string     // ISO date "YYYY-MM-DD"
  initial_capital: number
  seed: number
  min_score: number
}

export interface BacktestMetrics {
  initial_capital: number
  final_equity: number
  total_return_pct: number
  annualized_return_pct: number
  sharpe_ratio: number
  calmar_ratio: number
  max_drawdown_pct: number
  win_rate: number
  profit_factor: number
  num_trades: number
  num_wins: number
  num_losses: number
  avg_trade_duration_days: number
  best_trade_pct: number
  worst_trade_pct: number
  avg_win_pct: number
  avg_loss_pct: number
  max_consecutive_wins: number
  max_consecutive_losses: number
}

export interface TradeRecord {
  trade_id: string
  symbol: string
  entry_date: string
  exit_date: string
  entry_price: number
  exit_price: number
  quantity: number
  stop_loss: number
  take_profit: number
  pnl_chf: number
  pnl_pct: number
  duration_days: number
  exit_reason: string
  signal_score?: number
  is_win: boolean
}

export interface EquityCurvePoint {
  date: string
  equity: number
  drawdown_pct: number
}

export interface BacktestResult {
  backtest_id: string
  config: BacktestConfig
  metrics: BacktestMetrics
  equity_curve: EquityCurvePoint[]
  trades: TradeRecord[]
  generated_at: string
  duration_ms: number
}

export interface BacktestRunResponse {
  backtest_id: string
  symbol: string
  metrics: BacktestMetrics
  num_trades: number
  duration_ms: number
  generated_at: string
}

// ── Order ─────────────────────────────────────────────────────────────────────

export interface OrderRequest {
  symbol: string
  direction: 'buy' | 'sell'
  quantity?: number
  amount_chf?: number
  limit_price?: number
  stop_loss?: number
  take_profit?: number
}

export interface OrderValidation {
  valid: boolean
  errors: string[]
  warnings: string[]
  crv?: number
  stamp_tax_chf: number
  estimated_cost_chf: number
  entry_price: number
}

// ── Dominance Engine ──────────────────────────────────────────────────────────

export interface DominanceState {
  dominant_layer:       string
  dominant_label:       string
  dominance_strength:   number          // 0–1
  layer_scores:         Record<string, number>
  gaining_layers:       string[]
  losing_layers:        string[]
  narrative_explanation: string
  assessed_at?:         string
  error?:               string | null   // gesetzt wenn Backend-Fallback aktiv
}

// ── Portfolio Analysis ────────────────────────────────────────────────────────

export interface DerivationStep {
  step:    number
  label:   string
  finding: string
  signal:  'bullish' | 'bearish' | 'neutral'
}

export interface PositionAnalysis {
  symbol:       string
  name:         string
  action:       'buy' | 'accumulate' | 'hold' | 'reduce' | 'sell' | 'watch'
  conviction:   'high' | 'medium' | 'low'
  score:        number
  derivation:   DerivationStep[]
  summary:      string
  key_risk:     string
  price_target?: number
  stop_loss?:   number
}

export interface ClusterRisk {
  type:       'sector' | 'region' | 'currency'
  label:      string
  weight_pct: number
  symbols:    string[]
  risk_level: 'low' | 'medium' | 'high'
  comment:    string
}

export interface PortfolioAnalysisResult {
  overall_score:          number
  diversification_score:  number
  region_weights:         Record<string, number>
  sector_weights:         Record<string, number>
  currency_weights:       Record<string, number>
  cluster_risks:          ClusterRisk[]
  position_analyses:      PositionAnalysis[]
  portfolio_comment:      string
}

// ── Learning: Evaluations ─────────────────────────────────────────────────────

export type EvaluationErrorType =
  | 'wrong_regime' | 'wrong_dominance' | 'wrong_psychology'
  | 'wrong_liquidity' | 'wrong_timing' | 'correct' | 'unknown'

export interface Evaluation {
  id:                       string
  recommendation_id:        string
  symbol:                   string
  predicted_action:         string
  actual_outcome:           string
  price_at_recommendation:  number
  price_after_1d?:          number
  price_after_5d?:          number
  price_after_20d?:         number
  return_1d_pct?:           number
  return_5d_pct?:           number
  return_20d_pct?:          number
  accuracy_score:           number
  correct:                  boolean
  error_type?:              EvaluationErrorType
  lesson_learned?:          string
  evaluated_at?:            string
  horizon_days:             number
}

export interface EvaluationErrorStats {
  count:        number
  correct:      number
  avg_accuracy: number
  win_rate:     number
}

export interface EvaluationStats {
  total:        number
  correct:      number
  win_rate:     number
  avg_accuracy: number
  by_error_type: Record<string, EvaluationErrorStats>
}

export interface EvaluationResponse {
  evaluations: Evaluation[]
  stats:       EvaluationStats
}

// ── Learning: Prompt Suggestions ─────────────────────────────────────────────

export interface PromptSuggestion {
  id:                string
  category:          string
  category_label:    string
  problem:           string
  suggestion_prompt: string
  priority:          'high' | 'medium' | 'low'
  based_on_errors:   number
  example_case:      string
}
