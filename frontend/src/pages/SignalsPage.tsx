import { useState } from 'react'
import { useSignals } from '../hooks/useApi'
import { SignalCard } from '../components/shared/SignalCard'
import { Badge } from '../components/ui/Badge'
import { LoadingSpinner, ErrorState, EmptyState } from '../components/ui/LoadingSpinner'
import type { SignalType, SignalStrength } from '../api/types'

const SIGNAL_TYPES: { value: SignalType | 'all'; label: string }[] = [
  { value: 'all',      label: 'Alle' },
  { value: 'buy',      label: 'Kaufen' },
  { value: 'sell',     label: 'Verkaufen' },
  { value: 'hold',     label: 'Halten' },
  { value: 'avoid',    label: 'Meiden' },
]

const STRENGTHS: { value: SignalStrength | 'all'; label: string }[] = [
  { value: 'all',      label: 'Alle Stärken' },
  { value: 'strong',   label: 'Stark' },
  { value: 'moderate', label: 'Moderat' },
  { value: 'weak',     label: 'Schwach' },
]

export default function SignalsPage() {
  const [minScore, setMinScore]       = useState(65)
  const [typeFilter, setTypeFilter]   = useState<SignalType | 'all'>('all')
  const [strengthFilter, setStrength] = useState<SignalStrength | 'all'>('all')

  const { data: signals = [], isLoading, isError, refetch } = useSignals(minScore)

  const filtered = signals
    .filter((s) => typeFilter === 'all'     || s.signal_type === typeFilter)
    .filter((s) => strengthFilter === 'all' || s.strength === strengthFilter)
    .sort((a, b) => b.score.total - a.score.total)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

      {/* ── Filter Bar ── */}
      <div className="filter-bar">
        {/* Score Slider */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span className="label-caps">Min. Score</span>
          <input
            type="range" min={50} max={90} step={5} value={minScore}
            onChange={(e) => setMinScore(Number(e.target.value))}
            style={{ width: 110, accentColor: 'var(--accent)' }}
          />
          <span className="font-num" style={{
            fontSize: 14, fontWeight: 700, color: 'var(--accent)',
            minWidth: 26, background: 'var(--accent-dim)',
            padding: '2px 7px', borderRadius: 6,
          }}>
            {minScore}
          </span>
        </div>

        <div style={{ width: 1, height: 24, background: 'var(--border-std)' }} />

        {/* Signal Type */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span className="label-caps">Typ</span>
          {SIGNAL_TYPES.map(({ value, label }) => (
            <button
              key={value}
              className={`filter-chip${typeFilter === value ? ' active' : ''}`}
              onClick={() => setTypeFilter(value)}
            >
              {label}
            </button>
          ))}
        </div>

        <div style={{ width: 1, height: 24, background: 'var(--border-std)' }} />

        {/* Strength */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span className="label-caps">Stärke</span>
          {STRENGTHS.map(({ value, label }) => (
            <button
              key={value}
              className={`filter-chip${strengthFilter === value ? ' active' : ''}`}
              onClick={() => setStrength(value)}
            >
              {label}
            </button>
          ))}
        </div>

        <div style={{ marginLeft: 'auto' }}>
          <Badge variant="dim" size="md">{filtered.length} Signale</Badge>
        </div>
      </div>

      {/* ── Content ── */}
      {isLoading && <LoadingSpinner fullPage message="Signale werden analysiert…" />}
      {isError   && <ErrorState message="Signale nicht verfügbar" onRetry={refetch} />}

      {!isLoading && !isError && filtered.length === 0 && (
        <EmptyState message="Keine Signale für diese Filterkriterien" />
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))', gap: 16 }}>
        {filtered.map((signal) => (
          <SignalCard key={signal.id} signal={signal} />
        ))}
      </div>

    </div>
  )
}
