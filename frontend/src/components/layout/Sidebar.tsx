import { NavLink } from 'react-router-dom'
import { useHealth } from '../../hooks/useApi'

const NAV = [
  {
    to: '/dashboard',
    label: 'Dashboard',
    icon: (
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>
        <rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>
      </svg>
    ),
  },
  {
    to: '/portfolio',
    label: 'Portfolio',
    icon: (
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="2" y="7" width="20" height="14" rx="2"/>
        <path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2"/>
      </svg>
    ),
  },
  {
    to: '/signals',
    label: 'Signale',
    icon: (
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
      </svg>
    ),
  },
  {
    to: '/recommendations',
    label: 'Empfehlungen',
    icon: (
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
      </svg>
    ),
  },
  {
    to: '/journal',
    label: 'Journal',
    icon: (
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>
        <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
      </svg>
    ),
  },
  {
    to: '/backtest',
    label: 'Backtest',
    icon: (
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>
        <polyline points="17 6 23 6 23 12"/>
      </svg>
    ),
  },
  {
    to: '/watchlist',
    label: 'Watchlist',
    icon: (
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
        <circle cx="12" cy="12" r="3"/>
      </svg>
    ),
  },
  {
    to: '/news',
    label: 'News',
    icon: (
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M4 22h16a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v16a2 2 0 0 1-2 2zm0 0a2 2 0 0 1-2-2v-9c0-1.1.9-2 2-2h2"/>
        <path d="M18 14h-8M15 18h-5M10 6h8v4h-8z"/>
      </svg>
    ),
  },
  {
    to: '/alerts',
    label: 'Alerts',
    icon: (
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
        <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
      </svg>
    ),
  },
  {
    to: '/risk',
    label: 'Risiko',
    icon: (
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
      </svg>
    ),
  },
  {
    to: '/learning',
    label: 'Lernsystem',
    icon: (
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 2L2 7l10 5 10-5-10-5z"/>
        <path d="M2 17l10 5 10-5"/>
        <path d="M2 12l10 5 10-5"/>
      </svg>
    ),
  },
]

export function Sidebar() {
  const { data: health } = useHealth()
  const backendOk = health?.status === 'ok'
  const ibkrOk   = health?.ibkr_connected
  const feedMode  = health?.feed_mode
  const dataLabel = feedMode === 'yahoo' ? 'Yahoo Finance' : feedMode === 'mock' ? 'MockFeed' : undefined

  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">T</div>
        <div>
          <div className="sidebar-logo-name">TradeApp</div>
          <div className="sidebar-logo-sub">Magdalena</div>
        </div>
      </div>

      {/* Navigation */}
      <nav style={{ padding: '8px 0', flex: 1 }}>
        {NAV.map(({ to, icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) => `sidebar-nav-item${isActive ? ' active' : ''}`}
          >
            <span className="sidebar-nav-icon">{icon}</span>
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Status — kompakt */}
      <div className="sidebar-status">
        <StatusRow ok={backendOk} label="Backend" />
        {ibkrOk && <StatusRow ok={true} label="IBKR TWS" />}
        {dataLabel && (
          <div className="status-row">
            <span style={{
              width: 7, height: 7, borderRadius: '50%', flexShrink: 0, display: 'inline-block',
              background: feedMode === 'yahoo' ? 'var(--green)' : 'var(--amber)',
            }} />
            <span style={{ fontSize: 11, color: 'var(--text-4)', flex: 1 }}>{dataLabel}</span>
          </div>
        )}
      </div>
    </aside>
  )
}

function StatusRow({ ok, label }: { ok?: boolean; label: string }) {
  const color  = ok === undefined ? 'var(--text-4)' : ok ? 'var(--green)' : 'var(--red)'
  const status = ok === undefined ? '···' : ok ? 'Online' : 'Offline'
  return (
    <div className="status-row">
      <span className={ok ? 'pulse-anim' : ''} style={{
        display: 'inline-block', width: 7, height: 7,
        borderRadius: '50%', background: color, flexShrink: 0,
      }} />
      <span style={{ fontSize: 11, color: 'var(--text-3)', flex: 1 }}>{label}</span>
      <span style={{ fontSize: 10, fontWeight: 600, color }}>{status}</span>
    </div>
  )
}
