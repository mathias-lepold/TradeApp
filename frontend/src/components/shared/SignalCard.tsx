import type { Signal } from '../../api/types'
import { SignalTypeBadge, Badge } from '../ui/Badge'
import { ScoreBreakdownBars, TotalScore } from '../ui/ScoreBar'
import { Card } from '../ui/Card'

const STRENGTH_COLOR: Record<string, string> = {
  strong: 'var(--green)', moderate: 'var(--accent)', weak: 'var(--text-4)',
}
const STRENGTH_LABEL: Record<string, string> = {
  strong: 'Stark', moderate: 'Moderat', weak: 'Schwach',
}

interface Props {
  signal: Signal
  compact?: boolean
}

export function SignalCard({ signal, compact }: Props) {
  const crv = signal.crv
  const hasPrice = signal.stop_loss || signal.target_price

  return (
    <Card className="anim-fade">
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <TotalScore score={signal.score.total} size="md" />
          <div>
            <div style={{ fontWeight: 700, fontSize: 17, letterSpacing: '-0.01em', color: 'var(--text-1)' }}>
              {signal.asset_symbol}
            </div>
            <div style={{ color: 'var(--text-4)', fontSize: 12, marginTop: 3, fontWeight: 400 }}>
              {signal.asset_name}
            </div>
          </div>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 7 }}>
          <SignalTypeBadge type={signal.signal_type} />
          <span style={{ fontSize: 11, color: STRENGTH_COLOR[signal.strength], fontWeight: 600 }}>
            ● {STRENGTH_LABEL[signal.strength]}
          </span>
        </div>
      </div>

      {/* Preislevel */}
      {hasPrice && (
        <div style={{
          display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)',
          gap: 1, marginBottom: 16,
          background: 'var(--border-dim)',
          borderRadius: 10, overflow: 'hidden',
        }}>
          <PriceCell label="Einstieg" value={signal.price_at_signal?.toFixed(2) ?? '—'} />
          {signal.stop_loss && (
            <PriceCell label="Stop-Loss" value={signal.stop_loss.toFixed(2)} color="var(--red)" />
          )}
          {signal.target_price && (
            <PriceCell label="Kursziel" value={signal.target_price.toFixed(2)} color="var(--green)" />
          )}
        </div>
      )}

      {/* CRV */}
      {crv && (
        <div style={{
          display: 'flex', alignItems: 'center', gap: 12, marginBottom: 14,
          padding: '7px 12px', borderRadius: 8,
          background: 'var(--bg-elevated)', border: '1px solid var(--border-dim)',
        }}>
          <span className="label-caps">CRV</span>
          <span className="font-num" style={{
            fontSize: 14, fontWeight: 700,
            color: crv >= 2 ? 'var(--green)' : crv >= 1.5 ? 'var(--amber)' : 'var(--red)',
          }}>
            1 : {crv}
          </span>
          {signal.catalyst && (
            <span style={{ color: 'var(--text-4)', fontSize: 12, marginLeft: 'auto', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {signal.catalyst}
            </span>
          )}
        </div>
      )}

      {/* Score Bars */}
      {!compact && (
        <>
          <div className="divider" />
          <div style={{ marginTop: 4 }}>
            <div className="label-caps" style={{ marginBottom: 10 }}>Score Breakdown</div>
            <ScoreBreakdownBars score={signal.score} compact />
          </div>
        </>
      )}

      {/* Gründe */}
      {!compact && (signal.reasons?.length ?? 0) > 0 && (
        <div style={{ marginTop: 14 }}>
          <div className="label-caps" style={{ marginBottom: 8 }}>Argumente</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
            {signal.reasons?.map((r, i) => (
              <Badge key={i} variant="dim">{r}</Badge>
            ))}
          </div>
        </div>
      )}

      {/* Regime Context */}
      {signal.regime_context && (
        <div style={{
          marginTop: 12, padding: '6px 10px', borderRadius: 6,
          background: 'var(--bg-elevated)', fontSize: 11, color: 'var(--text-4)',
        }}>
          Regime: {signal.regime_context}
        </div>
      )}
    </Card>
  )
}

function PriceCell({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div style={{
      textAlign: 'center', padding: '10px 8px',
      background: 'var(--bg-elevated)',
    }}>
      <div className="label-caps" style={{ marginBottom: 5 }}>{label}</div>
      <div className="font-num" style={{ fontSize: 13, fontWeight: 700, color: color ?? 'var(--text-1)' }}>
        {value}
      </div>
    </div>
  )
}

// Kompakte Version für Dashboard-Preview
export function SignalRow({ signal }: { signal: Signal }) {
  return (
    <div className="list-row" style={{ display: 'flex', alignItems: 'center', gap: 14, padding: '11px 20px' }}>
      <TotalScore score={signal.score.total} size="sm" />
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontWeight: 600, fontSize: 14, color: 'var(--text-1)' }}>{signal.asset_symbol}</div>
        <div style={{ fontSize: 12, color: 'var(--text-4)', marginTop: 2 }}>{signal.asset_name}</div>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 5 }}>
        <SignalTypeBadge type={signal.signal_type} />
        {signal.crv && (
          <span className="font-num" style={{ fontSize: 11, color: 'var(--text-4)' }}>
            CRV 1:{signal.crv}
          </span>
        )}
      </div>
    </div>
  )
}
