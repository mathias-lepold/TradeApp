import { useState } from 'react'
import { useRecommendations } from '../hooks/useApi'
import { RecommendationCard } from '../components/shared/RecommendationCard'
import { Badge } from '../components/ui/Badge'
import { LoadingSpinner, ErrorState, EmptyState } from '../components/ui/LoadingSpinner'
import type { RecommendationAction, RecommendationPriority } from '../api/types'

const ACTIONS: { value: RecommendationAction | 'all'; label: string }[] = [
  { value: 'all',    label: 'Alle' },
  { value: 'buy',    label: 'Kaufen' },
  { value: 'add',    label: 'Aufstocken' },
  { value: 'sell',   label: 'Verkaufen' },
  { value: 'reduce', label: 'Reduzieren' },
  { value: 'hold',   label: 'Halten' },
  { value: 'wait',   label: 'Abwarten' },
  { value: 'avoid',  label: 'Meiden' },
]

const PRIORITIES: { value: RecommendationPriority | 'all'; label: string }[] = [
  { value: 'all',    label: 'Alle' },
  { value: 'urgent', label: 'Dringend' },
  { value: 'high',   label: 'Hoch' },
  { value: 'normal', label: 'Normal' },
  { value: 'low',    label: 'Niedrig' },
]

export default function RecommendationsPage() {
  const [actionFilter, setAction]     = useState<RecommendationAction | 'all'>('all')
  const [priorityFilter, setPriority] = useState<RecommendationPriority | 'all'>('all')
  const [showExpired, setShowExpired] = useState(false)

  const { data: recs = [], isLoading, isError, refetch } = useRecommendations()

  const filtered = recs
    .filter((r) => showExpired || !r?.is_expired)
    .filter((r) => actionFilter === 'all'   || r.action === actionFilter)
    .filter((r) => priorityFilter === 'all' || r.priority === priorityFilter)
    .sort((a, b) => {
      const order = { urgent: 0, high: 1, normal: 2, low: 3 }
      return order[a.priority] - order[b.priority]
    })

  const buyCount  = recs.filter((r) => !r?.is_expired && (r.action === 'buy' || r.action === 'add')).length
  const biasCount = recs.filter((r) => r.has_bias_warning).length

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

      {/* ── Summary Strip ── */}
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
        <SummaryTile label="Empfehlungen gesamt" value={recs.length} />
        <SummaryTile label="Kaufen / Aufstocken" value={buyCount} color="var(--green)" />
        <SummaryTile
          label="Bias-Warnungen"
          value={biasCount}
          color={biasCount > 0 ? 'var(--amber)' : undefined}
        />
      </div>

      {/* ── Filter Bar ── */}
      <div className="filter-bar" style={{ flexWrap: 'wrap', gap: 10 }}>
        {/* Action */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
          <span className="label-caps">Aktion</span>
          {ACTIONS.map(({ value, label }) => (
            <button
              key={value}
              className={`filter-chip${actionFilter === value ? ' active' : ''}`}
              onClick={() => setAction(value)}
            >
              {label}
            </button>
          ))}
        </div>

        <div style={{ width: 1, height: 24, background: 'var(--border-std)', flexShrink: 0 }} />

        {/* Priority */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span className="label-caps">Priorität</span>
          {PRIORITIES.map(({ value, label }) => (
            <button
              key={value}
              className={`filter-chip${priorityFilter === value ? ' active' : ''}`}
              onClick={() => setPriority(value)}
            >
              {label}
            </button>
          ))}
        </div>

        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 12 }}>
          <label style={{
            display: 'flex', alignItems: 'center', gap: 7,
            cursor: 'pointer', fontSize: 13, color: 'var(--text-3)',
          }}>
            <input
              type="checkbox"
              checked={showExpired}
              onChange={(e) => setShowExpired(e.target.checked)}
              style={{ accentColor: 'var(--accent)', width: 14, height: 14 }}
            />
            Abgelaufene
          </label>
          <Badge variant="dim" size="md">{filtered.length} Ergebnisse</Badge>
        </div>
      </div>

      {/* ── Content ── */}
      {isLoading && <LoadingSpinner fullPage message="Decision Engine läuft…" />}
      {isError   && <ErrorState message="Empfehlungen nicht verfügbar" onRetry={refetch} />}

      {!isLoading && !isError && filtered.length === 0 && (
        <EmptyState message="Keine Empfehlungen für diese Filterkriterien" />
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(400px, 1fr))', gap: 16 }}>
        {filtered.map((rec) => (
          <RecommendationCard key={rec.id} rec={rec} />
        ))}
      </div>

    </div>
  )
}

function SummaryTile({ label, value, color }: { label: string; value: number; color?: string }) {
  return (
    <div style={{
      padding: '12px 18px',
      borderRadius: 10,
      background: 'var(--bg-surface)',
      border: '1px solid var(--border-dim)',
      display: 'flex', flexDirection: 'column', gap: 5,
      minWidth: 140,
      boxShadow: 'var(--shadow-card)',
    }}>
      <span className="label-caps">{label}</span>
      <span className="font-num" style={{ fontSize: 28, fontWeight: 700, color: color ?? 'var(--text-1)', lineHeight: 1 }}>
        {value}
      </span>
    </div>
  )
}
