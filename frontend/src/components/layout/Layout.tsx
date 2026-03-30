import { Outlet, useLocation } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { useRegime } from '../../hooks/useApi'

const PAGE_META: Record<string, { title: string; subtitle?: string }> = {
  '/dashboard':       { title: 'Dashboard',       subtitle: 'Marktübersicht' },
  '/portfolio':       { title: 'Portfolio',        subtitle: 'Positionen & PnL' },
  '/signals':         { title: 'Signale',          subtitle: 'RSI · MACD · Bollinger' },
  '/recommendations': { title: 'Empfehlungen',     subtitle: 'Decision Engine' },
  '/journal':         { title: 'Journal',          subtitle: 'Bias-Analyse' },
  '/backtest':        { title: 'Backtest',         subtitle: 'Historische Simulation' },
  '/watchlist':       { title: 'Watchlist',        subtitle: 'Beobachtungsliste' },
  '/news':            { title: 'News',             subtitle: 'Sentiment-Analyse' },
  '/alerts':          { title: 'Alerts',           subtitle: 'Kursalarme' },
  '/risk':            { title: 'Risiko',           subtitle: 'VaR & Konzentration' },
  '/learning':        { title: 'Lernsystem',       subtitle: 'Fehleranalyse & Optimierung' },
}

export default function Layout() {
  const location = useLocation()
  const meta = PAGE_META[location.pathname] ?? { title: 'TradeApp' }
  const { dataUpdatedAt } = useRegime()

  const lastUpdate = dataUpdatedAt
    ? new Date(dataUpdatedAt).toLocaleTimeString('de-CH', {
        hour: '2-digit', minute: '2-digit', second: '2-digit',
      })
    : null

  return (
    <div className="app-shell">
      <Sidebar />

      <div className="main-area">
        <header className="topbar">
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 10 }}>
            <div className="topbar-title">{meta.title}</div>
            {meta.subtitle && (
              <div className="topbar-meta">{meta.subtitle}</div>
            )}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            {lastUpdate && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                <span style={{
                  width: 6, height: 6, borderRadius: '50%',
                  background: 'var(--green)',
                  display: 'inline-block',
                  animation: 'pulse 2s infinite',
                }} />
                <span style={{ fontSize: 11, color: 'var(--text-4)' }}>{lastUpdate}</span>
              </div>
            )}
            <div style={{
              width: 32, height: 32, borderRadius: 8,
              background: 'var(--bg-elevated)',
              border: '1px solid var(--border-std)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: 'var(--text-3)', cursor: 'pointer',
              transition: 'all var(--trans)',
            }}
              onMouseEnter={e => { e.currentTarget.style.background = 'var(--border-std)' }}
              onMouseLeave={e => { e.currentTarget.style.background = 'var(--bg-elevated)' }}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="8" r="4"/>
                <path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/>
              </svg>
            </div>
          </div>
        </header>

        <main className="page-content">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
