import type { RegimeState, RegimeType } from '../../api/types'

const REGIME_META: Record<RegimeType, {
  icon: string
  color: string
  bg: string
  border: string
  label: string
}> = {
  bull_market: {
    icon: '↗', color: '#16a34a', bg: 'rgba(22,163,74,0.07)',
    border: 'rgba(22,163,74,0.20)', label: 'bull_market',
  },
  bear_market: {
    icon: '↘', color: '#dc2626', bg: 'rgba(220,38,38,0.07)',
    border: 'rgba(220,38,38,0.20)', label: 'bear_market',
  },
  sideways: {
    icon: '→', color: '#64748b', bg: 'rgba(100,116,139,0.06)',
    border: 'rgba(100,116,139,0.18)', label: 'sideways',
  },
  volatile: {
    icon: '↕', color: '#d97706', bg: 'rgba(217,119,6,0.07)',
    border: 'rgba(217,119,6,0.22)', label: 'volatile',
  },
  crisis: {
    icon: '⚠', color: '#dc2626', bg: 'rgba(220,38,38,0.09)',
    border: 'rgba(220,38,38,0.30)', label: 'crisis',
  },
  recovery: {
    icon: '↑', color: '#2563eb', bg: 'rgba(37,99,235,0.07)',
    border: 'rgba(37,99,235,0.20)', label: 'recovery',
  },
}

export function RegimeBanner({ regime }: { regime: RegimeState | undefined | null }) {
  if (!regime) return <RegimeSkeleton />

  const meta = REGIME_META[regime.regime_type] ?? REGIME_META.sideways
  const vix  = regime.macro?.vix
  const fg   = regime.macro?.fear_greed_index

  return (
    <div
      className="regime-banner anim-fade"
      style={{
        background: meta.bg,
        border: `1px solid ${meta.border}`,
        boxShadow: 'var(--shadow-card)',
      }}
    >
      {/* Regime Typ */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
        <div style={{
          width: 48, height: 48,
          borderRadius: 12,
          background: `${meta.color}20`,
          border: `1px solid ${meta.color}35`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 22, color: meta.color,
          flexShrink: 0,
        }}>
          {meta.icon}
        </div>
        <div>
          <div style={{
            fontSize: 10, fontWeight: 700, letterSpacing: '.12em',
            textTransform: 'uppercase', color: meta.color, opacity: 0.7, marginBottom: 3,
          }}>
            Marktregime
          </div>
          <div style={{ fontSize: 18, fontWeight: 700, color: meta.color, lineHeight: 1.1 }}>
            {regime.label}
          </div>
        </div>
      </div>

      {/* Separator */}
      <div className="seg-divider" style={{ height: 40 }} />

      {/* Konfidenz */}
      <div>
        <div className="label-caps" style={{ marginBottom: 5 }}>Konfidenz</div>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 4 }}>
          <span className="font-num" style={{ fontSize: 22, fontWeight: 700, color: meta.color }}>
            {Math.round(regime.confidence * 100)}
          </span>
          <span style={{ fontSize: 13, color: 'var(--text-4)' }}>%</span>
        </div>
      </div>

      {/* VIX */}
      {vix !== undefined && (
        <>
          <div className="seg-divider" style={{ height: 40 }} />
          <div>
            <div className="label-caps" style={{ marginBottom: 5 }}>VIX</div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 4 }}>
              <span className="font-num" style={{
                fontSize: 22, fontWeight: 700,
                color: vix > 30 ? 'var(--red)' : vix > 20 ? 'var(--amber)' : 'var(--green)',
              }}>
                {vix.toFixed(1)}
              </span>
              <span style={{ fontSize: 11, color: 'var(--text-4)' }}>
                {vix > 30 ? 'Hoch' : vix > 20 ? 'Erhöht' : 'Normal'}
              </span>
            </div>
          </div>
        </>
      )}

      {/* Fear & Greed */}
      {fg !== undefined && (
        <>
          <div className="seg-divider" style={{ height: 40 }} />
          <div>
            <div className="label-caps" style={{ marginBottom: 5 }}>Fear &amp; Greed</div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 4 }}>
              <span className="font-num" style={{
                fontSize: 22, fontWeight: 700,
                color: fg < 30 ? 'var(--red)' : fg > 70 ? 'var(--green)' : 'var(--amber)',
              }}>
                {fg}
              </span>
              <span style={{ fontSize: 11, color: 'var(--text-4)' }}>
                {fg < 20 ? 'Extreme Angst' : fg < 40 ? 'Angst' : fg > 80 ? 'Extreme Gier' : fg > 60 ? 'Gier' : 'Neutral'}
              </span>
            </div>
          </div>
        </>
      )}

      {/* Risk-Off Warning */}
      {regime.is_risk_off && (
        <>
          <div className="seg-divider" style={{ height: 40 }} />
          <div style={{
            display: 'flex', alignItems: 'center', gap: 8,
            padding: '8px 14px', borderRadius: 8,
            background: 'rgba(220,38,38,0.08)',
            border: '1px solid rgba(220,38,38,0.22)',
          }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#dc2626" strokeWidth="2.5">
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
              <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
            </svg>
            <span style={{ fontSize: 12, fontWeight: 700, color: '#dc2626', letterSpacing: '.04em' }}>
              RISK-OFF
            </span>
          </div>
        </>
      )}

      {/* Max Position + Cash Buffer */}
      <div style={{ marginLeft: 'auto', textAlign: 'right' }}>
        <div className="label-caps" style={{ marginBottom: 5 }}>Max. Position</div>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 4, justifyContent: 'flex-end' }}>
          <span className="font-num" style={{ fontSize: 22, fontWeight: 700, color: 'var(--text-1)' }}>
            {regime.max_position_size_pct}
          </span>
          <span style={{ fontSize: 13, color: 'var(--text-4)' }}>%</span>
        </div>
        <div style={{ fontSize: 11, color: 'var(--text-4)', marginTop: 3 }}>
          Cash-Buffer: {regime.recommended_cash_buffer_pct}%
        </div>
      </div>
    </div>
  )
}

export function RegimeSkeleton() {
  return (
    <div className="regime-banner" style={{
      background: 'var(--bg-surface)',
      border: '1px solid var(--border-dim)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
        <div className="skeleton" style={{ width: 48, height: 48, borderRadius: 12 }} />
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <div className="skeleton" style={{ width: 80, height: 11 }} />
          <div className="skeleton" style={{ width: 140, height: 22 }} />
        </div>
      </div>
      <div className="skeleton" style={{ width: 80, height: 30 }} />
      <div className="skeleton" style={{ width: 60, height: 30 }} />
      <div style={{ marginLeft: 'auto' }}>
        <div className="skeleton" style={{ width: 100, height: 30 }} />
      </div>
    </div>
  )
}
