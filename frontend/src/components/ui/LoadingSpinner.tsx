interface Props {
  size?: number
  message?: string
  fullPage?: boolean
}

export function LoadingSpinner({ size = 28, message, fullPage }: Props) {
  const spinner = (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 14 }}>
      <svg
        width={size} height={size}
        viewBox="0 0 24 24" fill="none"
        style={{ animation: 'spin 0.75s linear infinite' }}
      >
        <circle cx="12" cy="12" r="10" stroke="var(--border-std)" strokeWidth="2" />
        <path d="M12 2a10 10 0 0 1 10 10" stroke="var(--accent)" strokeWidth="2.5" strokeLinecap="round" />
      </svg>
      {message && (
        <div style={{ color: 'var(--text-4)', fontSize: 13, fontWeight: 500, letterSpacing: '0.01em' }}>
          {message}
        </div>
      )}
    </div>
  )

  if (fullPage) {
    return (
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        height: '60vh',
        background: 'transparent',
      }}>
        {spinner}
      </div>
    )
  }

  return (
    <div style={{
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      padding: '32px 20px',
    }}>
      {spinner}
    </div>
  )
}

export function ErrorState({ message, onRetry }: { message?: string; onRetry?: () => void }) {
  return (
    <div style={{
      display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 14,
      padding: '40px 32px', textAlign: 'center',
    }}>
      <div style={{
        width: 48, height: 48, borderRadius: 12,
        background: 'rgba(239,68,68,0.1)',
        border: '1px solid rgba(239,68,68,0.25)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="var(--red)" strokeWidth="2">
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="8" x2="12" y2="12" />
          <line x1="12" y1="16" x2="12.01" y2="16" />
        </svg>
      </div>
      <div style={{ color: 'var(--text-3)', fontSize: 14, fontWeight: 500 }}>
        {message ?? 'Backend nicht erreichbar'}
      </div>
      {onRetry && (
        <button className="btn-secondary" onClick={onRetry}>
          Erneut versuchen
        </button>
      )}
    </div>
  )
}

export function EmptyState({ message = 'Keine Daten verfügbar' }: { message?: string }) {
  return (
    <div style={{
      display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12,
      padding: '60px 32px',
      color: 'var(--text-4)',
    }}>
      <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
        <line x1="11" y1="8" x2="11" y2="14"/><line x1="8" y1="11" x2="14" y2="11"/>
      </svg>
      <div style={{ fontSize: 14, fontWeight: 500 }}>{message}</div>
    </div>
  )
}
