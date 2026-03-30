import type { ScoreBreakdown } from '../../api/types'

const DIMS: { key: keyof ScoreBreakdown; label: string }[] = [
  { key: 'fundamental', label: 'Fundamental' },
  { key: 'technical',   label: 'Technisch' },
  { key: 'management',  label: 'Management' },
  { key: 'sentiment',   label: 'Sentiment' },
  { key: 'geopolitical',label: 'Geopolitik' },
  { key: 'macro',       label: 'Makro' },
]

function scoreColor(v: number) {
  if (v >= 75) return 'var(--green)'
  if (v >= 55) return 'var(--accent)'
  if (v >= 40) return 'var(--amber)'
  return 'var(--red)'
}

interface Props {
  score: ScoreBreakdown
  compact?: boolean
}

export function ScoreBreakdownBars({ score, compact }: Props) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: compact ? 8 : 10 }}>
      {DIMS.map(({ key, label }) => {
        const val = score[key] as number
        const color = scoreColor(val)
        return (
          <div key={key}>
            <div style={{
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              marginBottom: 4,
            }}>
              <span style={{ fontSize: 12, color: 'var(--text-3)', fontWeight: 500 }}>{label}</span>
              <span className="font-num" style={{ fontSize: 11, color, fontWeight: 700 }}>{val}</span>
            </div>
            <div style={{
              height: compact ? 3 : 4,
              background: 'var(--border-dim)',
              borderRadius: 99,
              overflow: 'hidden',
            }}>
              <div style={{
                height: '100%',
                width: `${val}%`,
                background: color,
                borderRadius: 99,
                transition: 'width 0.7s cubic-bezier(.4,0,.2,1)',
              }} />
            </div>
          </div>
        )
      })}
    </div>
  )
}

export function TotalScore({ score, size = 'md' }: { score: number; size?: 'sm' | 'md' | 'lg' }) {
  const fs   = size === 'lg' ? 28 : size === 'md' ? 18 : 14
  const dim  = size === 'lg' ? 72 : size === 'md' ? 52 : 38
  const stroke = size === 'lg' ? 3 : 2.5
  const r    = (dim / 2) - stroke - 1
  const circ = 2 * Math.PI * r
  const offset = circ - (score / 100) * circ
  const color  = scoreColor(score)

  return (
    <div style={{ position: 'relative', width: dim, height: dim, flexShrink: 0 }}>
      <svg width={dim} height={dim} viewBox={`0 0 ${dim} ${dim}`} style={{ transform: 'rotate(-90deg)' }}>
        <circle
          cx={dim/2} cy={dim/2} r={r}
          fill="none"
          stroke="var(--border-dim)"
          strokeWidth={stroke}
        />
        <circle
          cx={dim/2} cy={dim/2} r={r}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circ}
          strokeDashoffset={offset}
          style={{ transition: 'stroke-dashoffset 0.9s cubic-bezier(.4,0,.2,1)' }}
        />
      </svg>
      <div className="font-num" style={{
        position: 'absolute', inset: 0,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: fs, fontWeight: 700, color,
      }}>
        {score}
      </div>
    </div>
  )
}
