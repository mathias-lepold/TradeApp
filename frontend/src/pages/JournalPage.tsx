import { useState } from 'react'
import { useBiasAnalysis, useSignal } from '../hooks/useApi'
import { Card, CardHeader } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { LoadingSpinner, ErrorState } from '../components/ui/LoadingSpinner'
import { ScoreBreakdownBars, TotalScore } from '../components/ui/ScoreBar'

const SYMBOLS = ['NVDA', 'MSFT', 'NOVN', 'ZGLD', 'AAPL', 'AMZN']

const BIAS_META: Record<string, { icon: string; color: string; label: string; description: string }> = {
  fomo:            { icon: '🔥', color: '#dc2626', label: 'FOMO',            description: 'Kauf bei extremer Gier / Allzeithochs' },
  loss_aversion:   { icon: '🔒', color: '#d97706', label: 'Loss Aversion',   description: 'Verlustpositionen zu lange halten' },
  overconfidence:  { icon: '⚡', color: '#d97706', label: 'Overconfidence',  description: 'Zu grosse Positionen nach Gewinnserie' },
  revenge_trading: { icon: '💢', color: '#dc2626', label: 'Revenge Trading', description: 'Schneller Wiedereinstieg nach Verlust' },
  recency_bias:    { icon: '📈', color: '#94a3b8', label: 'Recency Bias',    description: 'Übergewichtung der letzten Kursbewegungen' },
  anchoring:       { icon: '⚓', color: '#94a3b8', label: 'Anchoring',       description: 'Festhalten an historischen Einstiegspreisen' },
}

function QualityGauge({ score }: { score: number }) {
  const color = score >= 80 ? 'var(--green)' : score >= 60 ? 'var(--accent)' : score >= 40 ? 'var(--amber)' : 'var(--red)'
  const label = score >= 80 ? 'Diszipliniert' : score >= 60 ? 'Gut' : score >= 40 ? 'Entwicklungspotential' : 'Hohes Bias-Risiko'

  return (
    <div style={{
      display: 'flex', flexDirection: 'column', alignItems: 'center',
      gap: 12, padding: '20px 0',
    }}>
      <TotalScore score={score} size="lg" />
      <div style={{ fontSize: 14, fontWeight: 700, color }}>{label}</div>
      <div style={{ fontSize: 12, color: 'var(--text-4)' }}>Behavioral Quality Score</div>
    </div>
  )
}

export default function JournalPage() {
  const [symbol, setSymbol] = useState('NVDA')
  const [customSymbol, setCustomSymbol] = useState('')

  const activeSymbol = customSymbol.toUpperCase() || symbol
  const { data: bias, isLoading, isError, refetch } = useBiasAnalysis(activeSymbol)
  const { data: signal } = useSignal(activeSymbol)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

      {/* ── Symbol Selector ── */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap',
        padding: '14px 18px',
        background: 'var(--bg-surface)',
        border: '1px solid var(--border-dim)',
        borderRadius: 12,
        boxShadow: 'var(--shadow-card)',
      }}>
        <span className="label-caps" style={{ marginRight: 4 }}>Symbol</span>
        {SYMBOLS.map((s) => (
          <button
            key={s}
            className={`filter-chip${symbol === s && !customSymbol ? ' active' : ''}`}
            onClick={() => { setSymbol(s); setCustomSymbol('') }}
          >
            {s}
          </button>
        ))}
        <div style={{ width: 1, height: 22, background: 'var(--border-std)' }} />
        <input
          type="text"
          placeholder="Eigenes Symbol…"
          value={customSymbol}
          onChange={(e) => setCustomSymbol(e.target.value.toUpperCase())}
          style={{ width: 140 }}
        />
        <span style={{ marginLeft: 'auto', fontSize: 13, color: 'var(--text-4)' }}>
          Analyse für:{' '}
          <span style={{ color: 'var(--accent)', fontWeight: 700 }}>{activeSymbol}</span>
        </span>
      </div>

      {/* ── Content ── */}
      {isLoading && <LoadingSpinner fullPage message="Behavioral Layer analysiert…" />}
      {isError   && <ErrorState message={`Keine Bias-Analyse für ${activeSymbol} verfügbar`} onRetry={refetch} />}

      {bias && (
        <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: 16 }}>

          {/* ── Linke Spalte ── */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {/* Quality Score */}
            <Card>
              <CardHeader title="Trader-Qualität" />
              <QualityGauge score={bias.quality_score} />

              {/* Bias Score Bar */}
              <div style={{
                padding: '12px 14px',
                background: 'var(--bg-elevated)',
                borderRadius: 10,
                border: '1px solid var(--border-dim)',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                  <span style={{ fontSize: 13, color: 'var(--text-3)' }}>Bias-Score</span>
                  <span className="font-num" style={{
                    fontSize: 15, fontWeight: 800,
                    color: bias.overall_score > 60 ? 'var(--red)' : bias.overall_score > 40 ? 'var(--amber)' : 'var(--green)',
                  }}>
                    {bias.overall_score} / 100
                  </span>
                </div>
                <div style={{ height: 5, background: 'var(--border-dim)', borderRadius: 99 }}>
                  <div style={{
                    height: '100%', borderRadius: 99,
                    width: `${bias.overall_score}%`,
                    background: bias.overall_score > 60 ? 'var(--red)' : bias.overall_score > 40 ? 'var(--amber)' : 'var(--green)',
                    transition: 'width 0.7s cubic-bezier(.4,0,.2,1)',
                  }} />
                </div>
              </div>

              {bias.recommendation_adjusted && (
                <div style={{
                  marginTop: 12, padding: '10px 12px', borderRadius: 8,
                  background: 'rgba(245,158,11,0.08)',
                  border: '1px solid rgba(245,158,11,0.25)',
                  display: 'flex', gap: 8, alignItems: 'center',
                  fontSize: 12, color: 'var(--amber)',
                }}>
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                    <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
                  </svg>
                  Empfehlung wurde wegen Bias angepasst
                </div>
              )}
            </Card>

            {/* Signal Basis */}
            {signal && (
              <Card>
                <CardHeader title="Signal-Basis" subtitle={signal.asset_name} />
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 14 }}>
                  <TotalScore score={signal.score.total} size="sm" />
                  <div>
                    <div style={{ fontWeight: 700, fontSize: 15, color: 'var(--text-1)' }}>
                      {signal.asset_symbol}
                    </div>
                    <div style={{ fontSize: 12, color: 'var(--text-4)', marginTop: 2 }}>
                      {signal.signal_type?.toUpperCase()} · {signal.strength}
                    </div>
                  </div>
                </div>
                <ScoreBreakdownBars score={signal.score} compact />
              </Card>
            )}
          </div>

          {/* ── Rechte Spalte ── */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

            {/* Erkannte Biases */}
            <Card>
              <CardHeader
                title="Erkannte Biases"
                subtitle={(bias.detected_biases?.length ?? 0) === 0
                  ? 'Keine Biases erkannt'
                  : `${bias.detected_biases?.length} Bias(es) aktiv`}
              />
              {(bias.detected_biases?.length ?? 0) === 0 ? (
                <div style={{
                  display: 'flex', alignItems: 'center', gap: 12,
                  padding: '16px 14px', borderRadius: 10,
                  background: 'rgba(34,197,94,0.08)',
                  border: '1px solid rgba(34,197,94,0.2)',
                }}>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--green)" strokeWidth="2.5">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                  <span style={{ color: 'var(--green)', fontSize: 13, fontWeight: 500 }}>
                    Keine kognitiven Verzerrungen erkannt — rationale Entscheidungsgrundlage
                  </span>
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {(bias.detected_biases ?? []).map((b) => {
                    const meta = BIAS_META[b] ?? { icon: '●', color: 'var(--text-3)', label: b, description: '' }
                    return (
                      <div key={b} style={{
                        display: 'flex', alignItems: 'flex-start', gap: 14,
                        padding: '12px 14px', borderRadius: 10,
                        background: `${meta.color}0d`,
                        border: `1px solid ${meta.color}25`,
                      }}>
                        <span style={{ fontSize: 20, flexShrink: 0, lineHeight: 1 }}>{meta.icon}</span>
                        <div style={{ flex: 1 }}>
                          <div style={{ fontWeight: 700, fontSize: 14, color: meta.color }}>{meta.label}</div>
                          <div style={{ fontSize: 12, color: 'var(--text-3)', marginTop: 4, lineHeight: 1.5 }}>
                            {meta.description}
                          </div>
                        </div>
                        <Badge
                          variant={meta.color === '#dc2626' ? 'red' : 'amber'}
                          size="sm"
                        >
                          Aktiv
                        </Badge>
                      </div>
                    )
                  })}
                </div>
              )}
            </Card>

            {/* Warnhinweise */}
            {(bias.warnings?.length ?? 0) > 0 && (
              <Card>
                <CardHeader title="Warnhinweise" subtitle="Vom Behavioral Layer erkannt" />
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {(bias.warnings ?? []).map((w, i) => (
                    <div key={i} style={{
                      fontSize: 13, color: 'var(--text-2)',
                      padding: '10px 14px',
                      background: 'rgba(245,158,11,0.06)',
                      borderRadius: 8,
                      borderLeft: '3px solid rgba(245,158,11,0.6)',
                      lineHeight: 1.5,
                    }}>
                      {w}
                    </div>
                  ))}
                </div>
              </Card>
            )}

            {/* Bias-Bibliothek */}
            <Card>
              <CardHeader title="Bias-Bibliothek" subtitle="Alle überwachten Verzerrungen" />
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                {Object.entries(BIAS_META).map(([key, meta]) => {
                  const active = (bias.detected_biases ?? []).includes(key)
                  return (
                    <div key={key} style={{
                      display: 'flex', alignItems: 'center', gap: 10,
                      padding: '10px 12px', borderRadius: 9,
                      background: active ? `${meta.color}0d` : 'var(--bg-elevated)',
                      border: `1px solid ${active ? meta.color + '30' : 'var(--border-dim)'}`,
                      opacity: active ? 1 : 0.45,
                      transition: 'all var(--trans)',
                    }}>
                      <span style={{ fontSize: 18, flexShrink: 0 }}>{meta.icon}</span>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{
                          fontSize: 12, fontWeight: 600,
                          color: active ? meta.color : 'var(--text-4)',
                          overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                        }}>
                          {meta.label}
                        </div>
                      </div>
                      {active && (
                        <span style={{
                          width: 7, height: 7, borderRadius: '50%',
                          background: meta.color, flexShrink: 0,
                          boxShadow: `0 0 6px ${meta.color}`,
                        }} />
                      )}
                    </div>
                  )
                })}
              </div>
            </Card>
          </div>
        </div>
      )}

    </div>
  )
}
