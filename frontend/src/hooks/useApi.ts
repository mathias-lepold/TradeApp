import { useQuery, useMutation } from '@tanstack/react-query'
import {
  fetchHealth, fetchRegime, fetchSignals, fetchSignalForSymbol,
  fetchRecommendations, fetchRecommendationForSymbol, fetchPortfolio,
  fetchMacro, fetchQuote, fetchJournalStats, fetchBiasAnalysis,
  validateOrder, executeOrder,
  fetchCycle, fetchLiquidity, fetchExpectations, fetchHypothesis,
  runBacktest, fetchBacktestResult, fetchBacktestTrades, fetchBacktestEquity,
  fetchPortfolioSummary, createPortfolioTrade, deletePortfolioTrade,
  fetchWatchlist, addToWatchlist, removeFromWatchlist,
  fetchAllNews, fetchNewsForSymbol,
  fetchAlerts, fetchTriggeredAlerts, createAlert, deleteAlert,
  fetchRisk,
  fetchDominance, fetchPortfolioAnalysis, fetchEvaluations, fetchPromptSuggestions,
} from '../api'
import type {
  OrderRequest, BacktestConfig, PortfolioTradeCreate,
  WatchlistAdd, AlertCreate,
} from '../api/types'

const STALE = 25_000    // 25s stale time → refetch wenn > 25s alt
const INTERVAL = 30_000 // Auto-Refetch alle 30s

// ── Health ────────────────────────────────────────────────────────────────────
export const useHealth = () =>
  useQuery({
    queryKey: ['health'],
    queryFn: fetchHealth,
    refetchInterval: INTERVAL,
    staleTime: STALE,
  })

// ── Macro ─────────────────────────────────────────────────────────────────────
export const useMacro = () =>
  useQuery({
    queryKey: ['macro'],
    queryFn: fetchMacro,
    refetchInterval: 60_000,
    staleTime: 55_000,
  })

// ── Quote ─────────────────────────────────────────────────────────────────────
export const useQuote = (symbol: string) =>
  useQuery({
    queryKey: ['quote', symbol],
    queryFn: () => fetchQuote(symbol),
    refetchInterval: INTERVAL,
    staleTime: STALE,
    enabled: !!symbol,
  })

// ── Regime ────────────────────────────────────────────────────────────────────
export const useRegime = () =>
  useQuery({
    queryKey: ['regime'],
    queryFn: fetchRegime,
    refetchInterval: 60_000,
    staleTime: 55_000,
  })

// ── Signals ───────────────────────────────────────────────────────────────────
export const useSignals = (minScore = 65) =>
  useQuery({
    queryKey: ['signals', minScore],
    queryFn: () => fetchSignals(minScore),
    refetchInterval: INTERVAL,
    staleTime: STALE,
  })

export const useSignal = (symbol: string) =>
  useQuery({
    queryKey: ['signal', symbol],
    queryFn: () => fetchSignalForSymbol(symbol),
    refetchInterval: INTERVAL,
    staleTime: STALE,
    enabled: !!symbol,
    retry: false,
  })

// ── Recommendations ───────────────────────────────────────────────────────────
export const useRecommendations = () =>
  useQuery({
    queryKey: ['recommendations'],
    queryFn: fetchRecommendations,
    refetchInterval: INTERVAL,
    staleTime: STALE,
  })

export const useRecommendation = (symbol: string) =>
  useQuery({
    queryKey: ['recommendation', symbol],
    queryFn: () => fetchRecommendationForSymbol(symbol),
    refetchInterval: INTERVAL,
    staleTime: STALE,
    enabled: !!symbol,
    retry: false,
  })

// ── Portfolio (legacy — Dashboard) ───────────────────────────────────────────
export const usePortfolio = () =>
  useQuery({
    queryKey: ['portfolio'],
    queryFn: fetchPortfolio,
    refetchInterval: 60_000,
    staleTime: 55_000,
  })

// ── Portfolio Management ──────────────────────────────────────────────────────
export const usePortfolioSummary = () =>
  useQuery({
    queryKey: ['portfolio', 'summary'],
    queryFn: fetchPortfolioSummary,
    refetchInterval: 30_000,
    staleTime: 25_000,
  })

export const useCreateTrade = () =>
  useMutation({
    mutationFn: (data: PortfolioTradeCreate) => createPortfolioTrade(data),
  })

export const useDeleteTrade = () =>
  useMutation({
    mutationFn: (id: string) => deletePortfolioTrade(id),
  })

// ── Journal ───────────────────────────────────────────────────────────────────
export const useJournalStats = () =>
  useQuery({
    queryKey: ['journal', 'stats'],
    queryFn: fetchJournalStats,
    staleTime: 5 * 60_000,
  })

export const useBiasAnalysis = (symbol: string) =>
  useQuery({
    queryKey: ['bias', symbol],
    queryFn: () => fetchBiasAnalysis(symbol),
    enabled: !!symbol,
    retry: false,
  })

// ── Orders ────────────────────────────────────────────────────────────────────
export const useValidateOrder = () =>
  useMutation({ mutationFn: validateOrder })

export const useExecuteOrder = () =>
  useMutation({ mutationFn: executeOrder })

// ── Market Cycle ──────────────────────────────────────────────────────────────
export const useCycle = () =>
  useQuery({
    queryKey: ['cycle'],
    queryFn: fetchCycle,
    refetchInterval: INTERVAL,
    staleTime: STALE,
  })

// ── Liquidity ─────────────────────────────────────────────────────────────────
export const useLiquidity = () =>
  useQuery({
    queryKey: ['liquidity'],
    queryFn: fetchLiquidity,
    refetchInterval: INTERVAL,
    staleTime: STALE,
  })

// ── Expectations ──────────────────────────────────────────────────────────────
export const useExpectations = (symbol?: string) =>
  useQuery({
    queryKey: ['expectations', symbol ?? 'portfolio'],
    queryFn: () => fetchExpectations(symbol),
    refetchInterval: INTERVAL,
    staleTime: STALE,
  })

// ── Hypothesis ────────────────────────────────────────────────────────────────
export const useHypothesis = (symbol: string) =>
  useQuery({
    queryKey: ['hypothesis', symbol],
    queryFn: () => fetchHypothesis(symbol),
    refetchInterval: INTERVAL,
    staleTime: STALE,
    enabled: !!symbol,
    retry: false,
  })

// ── Backtesting ───────────────────────────────────────────────────────────────
export const useRunBacktest = () =>
  useMutation({ mutationFn: (config: BacktestConfig) => runBacktest(config) })

export const useBacktestResult = (id: string | null) =>
  useQuery({
    queryKey: ['backtest', 'result', id],
    queryFn: () => fetchBacktestResult(id!),
    enabled: !!id,
    staleTime: Infinity,
    retry: false,
  })

export const useBacktestTrades = (id: string | null) =>
  useQuery({
    queryKey: ['backtest', 'trades', id],
    queryFn: () => fetchBacktestTrades(id!),
    enabled: !!id,
    staleTime: Infinity,
    retry: false,
  })

export const useBacktestEquity = (id: string | null) =>
  useQuery({
    queryKey: ['backtest', 'equity', id],
    queryFn: () => fetchBacktestEquity(id!),
    enabled: !!id,
    staleTime: Infinity,
    retry: false,
  })

// ── Watchlist ─────────────────────────────────────────────────────────────────
export const useWatchlist = () =>
  useQuery({ queryKey: ['watchlist'], queryFn: fetchWatchlist, refetchInterval: INTERVAL, staleTime: STALE })

export const useAddToWatchlist = () =>
  useMutation({ mutationFn: (data: WatchlistAdd) => addToWatchlist(data) })

export const useRemoveFromWatchlist = () =>
  useMutation({ mutationFn: (symbol: string) => removeFromWatchlist(symbol) })

// ── News ──────────────────────────────────────────────────────────────────────
export const useAllNews = (limitPer = 3) =>
  useQuery({
    queryKey: ['news', 'all', limitPer],
    queryFn: () => fetchAllNews(limitPer),
    refetchInterval: 5 * 60_000,
    staleTime: 4 * 60_000,
  })

export const useNewsForSymbol = (symbol: string) =>
  useQuery({
    queryKey: ['news', symbol],
    queryFn: () => fetchNewsForSymbol(symbol),
    enabled: !!symbol,
    refetchInterval: 5 * 60_000,
    staleTime: 4 * 60_000,
  })

// ── Alerts ────────────────────────────────────────────────────────────────────
export const useAlerts = () =>
  useQuery({ queryKey: ['alerts'], queryFn: fetchAlerts, refetchInterval: 30_000, staleTime: 25_000 })

export const useTriggeredAlerts = () =>
  useQuery({ queryKey: ['alerts', 'triggered'], queryFn: fetchTriggeredAlerts, refetchInterval: 30_000, staleTime: 25_000 })

export const useCreateAlert = () =>
  useMutation({ mutationFn: (data: AlertCreate) => createAlert(data) })

export const useDeleteAlert = () =>
  useMutation({ mutationFn: (id: string) => deleteAlert(id) })

// ── Risk ──────────────────────────────────────────────────────────────────────
export const useRisk = () =>
  useQuery({ queryKey: ['risk'], queryFn: fetchRisk, refetchInterval: 60_000, staleTime: 55_000 })

// ── Dominance Engine ──────────────────────────────────────────────────────────
export const useDominance = () =>
  useQuery({ queryKey: ['dominance'], queryFn: fetchDominance, refetchInterval: INTERVAL, staleTime: STALE, retry: 1, retryDelay: 2_000 })

// ── Portfolio Analysis ────────────────────────────────────────────────────────
export const usePortfolioAnalysis = () =>
  useQuery({ queryKey: ['portfolio', 'analysis'], queryFn: fetchPortfolioAnalysis, refetchInterval: 60_000, staleTime: 55_000 })

// ── Learning ──────────────────────────────────────────────────────────────────
export const useEvaluations = () =>
  useQuery({ queryKey: ['learning', 'evaluations'], queryFn: fetchEvaluations, staleTime: 5 * 60_000 })

export const usePromptSuggestions = () =>
  useQuery({ queryKey: ['learning', 'prompts'], queryFn: fetchPromptSuggestions, staleTime: 5 * 60_000 })
