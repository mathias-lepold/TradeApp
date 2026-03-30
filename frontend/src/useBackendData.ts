/**
 * TradeApp — React Hooks für alle Backend-Daten
 * Jeder Hook kapselt Laden, Fehler und Auto-Refresh.
 */

import { useState, useEffect, useCallback } from 'react'
import {
  getPortfolio, getSignals, getMacro, getHealth, getRegime,
  getRecommendations, getJournalStats,
  type Portfolio, type Signal, type MacroData,
  type Health, type Regime, type Recommendation, type JournalStats,
} from './api'

// ── Generischer Lade-Hook ─────────────────────────────────────────────────────

function useAutoRefresh<T>(
  fetcher: () => Promise<T>,
  intervalMs: number,
  deps: unknown[] = [],
): { data: T | null; loading: boolean; error: string | null; refresh: () => void } {
  const [data,    setData]    = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState<string | null>(null)

  const load = useCallback(async () => {
    try {
      setLoading(true)
      setData(await fetcher())
      setError(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Fehler beim Laden')
    } finally {
      setLoading(false)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  useEffect(() => {
    load()
    if (intervalMs > 0) {
      const id = setInterval(load, intervalMs)
      return () => clearInterval(id)
    }
  }, [load, intervalMs])

  return { data, loading, error, refresh: load }
}

// ── Portfolio (alle 60s) ──────────────────────────────────────────────────────

export function usePortfolio() {
  const { data: portfolio, loading, error, refresh } =
    useAutoRefresh(getPortfolio, 60_000)
  return { portfolio, loading, error, refresh }
}

// ── Signale (alle 30s) ────────────────────────────────────────────────────────

export function useSignals(minScore = 70) {
  const [signals,  setSignals]  = useState<Signal[]>([])
  const [loading,  setLoading]  = useState(true)
  const [error,    setError]    = useState<string | null>(null)

  const load = useCallback(async () => {
    try {
      setLoading(true)
      setSignals(await getSignals(minScore))
      setError(null)
    } catch (e) {
      setError('Signale nicht verfügbar')
    } finally {
      setLoading(false)
    }
  }, [minScore])

  useEffect(() => {
    load()
    const id = setInterval(load, 30_000)
    return () => clearInterval(id)
  }, [load])

  return { signals, loading, error, refresh: load }
}

// ── Recommendations (alle 60s) ────────────────────────────────────────────────

export function useRecommendations(minScore = 65) {
  const { data, loading, error, refresh } =
    useAutoRefresh(() => getRecommendations(minScore), 60_000, [minScore])
  return { recommendations: data ?? [], loading, error, refresh }
}

// ── Macro (alle 5min) ─────────────────────────────────────────────────────────

export function useMacro() {
  const { data: macro, loading, error } =
    useAutoRefresh(getMacro, 5 * 60_000)
  return { macro, loading, error }
}

// ── Regime (alle 5min) ────────────────────────────────────────────────────────

export function useRegime() {
  const { data: regime, loading, error } =
    useAutoRefresh(getRegime, 5 * 60_000)
  return { regime, loading, error }
}

// ── Journal Stats (einmalig) ──────────────────────────────────────────────────

export function useJournalStats() {
  const { data: stats, loading, error } =
    useAutoRefresh(getJournalStats, 0)  // kein Auto-Refresh
  return { stats, loading, error }
}

// ── Backend + IBKR Status (alle 30s) ─────────────────────────────────────────

export function useBackendStatus() {
  const [status, setStatus] = useState<Health | null>(null)

  useEffect(() => {
    const check = async () => {
      try { setStatus(await getHealth()) }
      catch { setStatus(null) }
    }
    check()
    const id = setInterval(check, 30_000)
    return () => clearInterval(id)
  }, [])

  return {
    connected:     !!status && status.status === 'ok',
    ibkrConnected: status?.ibkr_connected ?? false,
    mockFeed:      status?.mock_feed ?? false,
    regime:        status?.regime ?? null,
    redisOk:       status?.redis ?? false,
    raw:           status,
  }
}

// Re-exports für Abwärtskompatibilität mit App.tsx
export type { Portfolio, Signal, MacroData, Regime, Recommendation, JournalStats }
