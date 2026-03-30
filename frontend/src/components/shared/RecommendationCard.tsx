import type { Recommendation } from '../../api/types'
import { ActionBadge, PriorityDot, Badge } from '../ui/Badge'
import { Card } from '../ui/Card'

interface Props {
  rec: Recommendation
  compact?: boolean
}

function BiasBar({ score }: { score: number }) {
  const color = score > 60 ? 'var(--red)' : score > 40 ? 'var(--amber)' : 'var(--green)'
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
      <div style={{ flex: 1, height: 4, background: 'var(--border-dim)', borderRadius: 99 }}>
        <div style={{ width: `${score}%`, height: '100%', background: color, borderRadius: 99, transition: 'width 0.6s ease' }} />
      </div>
      <span className="font-num" style={{ fontSize: 11, color, minWidth: 28, textAlign: 'right', fontWeight: 700 }}>
        {score}
      </span>
    </div>
  )
}

function SizingBlock({ sizing }: {
  sizing: NonNullable<Recommendation['sizing']>
}) {
  return (
    <div style={{
      background: 'var(--bg-elevated)',
      borderRadius: 10,
      padding: '12px 14px',
      display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10,
      border: '1px solid var(--border-dim)',
    }}>
      <div>
        <div className="label-caps" style={{ marginBottom: 4 }}>Grösse</div>
        <div className="font-num" style={{ fontSize: 16, fontWeight: 700, color: 'var(--accent)' }}>
          {sizing.suggested_pct.toFixed(1)}%
        </div>
      </div>
      {sizing.suggested_chf && (
        <div>
          <div className="label-caps" style={{ marginBottom: 4 }}>Betrag CHF</div>
          <div className="font-num" style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-1)' }}>
            {sizing.suggested_chf.toLocaleString('de-CH', { maximumFractionDigits: 0 })}
          </div>
        </div>
      )}
      {sizing.suggested_shares && (
        <div>
          <div className="label-caps" style={{ marginBottom: 4 }}>Anteile</div>
          <div className="font-num" style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-1)' }}>
            {sizing.suggested_shares.toFixed(2)}
          </div>
        </div>
      )}
      {sizing.risk_per_trade_chf && (
        <div>
          <div className="label-caps" style={{ marginBottom: 4 }}>Risiko CHF</div>
          <div className="font-num" style={{ fontSize: 14, color: 'var(--red)' }}>
            {sizing.risk_per_trade_chf.toLocaleString('de-CH', { maximumFractionDigits: 0 })}
          </div>
        </div>
      )}
    </div>
  )
}

export function RecommendationCard({ rec, compact }: Props) {
  const hasLevels = rec.entry_price || rec.stop_loss || rec.target_price

  return (
    <Card className="anim-fade">
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 14 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <PriorityDot priority={rec.priority} size="lg" />
          <div>
            <div style={{ fontWeight: 700, fontSize: 18, letterSpacing: '-0.01em', color: 'var(--text-1)' }}>
              {rec.asset_symbol}
            </div>
            <div style={{ color: 'var(--text-4)', fontSize: 12, marginTop: 2 }}>{rec.asset_name}</div>
          </div>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 6 }}>
          <ActionBadge action={rec.action} />
          {rec.composite_score && (
            <span className="font-num" style={{ fontSize: 11, color: 'var(--text-4)' }}>
              Score {rec.composite_score}
            </span>
          )}
        </div>
      </div>

      {/* Rationale */}
      <p style={{ fontSize: 13, color: 'var(--text-3)', lineHeight: 1.6, marginBottom: 14 }}>
        {rec.rationale}
      </p>

      {/* Preislevel */}
      {hasLevels && (
        <div style={{
          display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)',
          gap: 1, marginBottom: 14,
          background: 'var(--border-dim)', borderRadius: 10, overflow: 'hidden',
        }}>
          {rec.entry_price && (
            <PriceCell label="Einstieg" value={rec.entry_price.toFixed(2)} />
          )}
          {rec.stop_loss && (
            <PriceCell label="Stop" value={rec.stop_loss.toFixed(2)} color="var(--red)" />
          )}
          {rec.target_price && (
            <PriceCell label="Ziel" value={rec.target_price.toFixed(2)} color="var(--green)" />
          )}
        </div>
      )}

      {/* CRV */}
      {rec.crv && (
        <div style={{
          display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14,
          padding: '7px 12px', borderRadius: 8,
          background: 'var(--bg-elevated)', border: '1px solid var(--border-dim)',
        }}>
          <span className="label-caps">CRV</span>
          <span className="font-num" style={{
            fontSize: 14, fontWeight: 700,
            color: rec.crv >= 2 ? 'var(--green)' : rec.crv >= 1.5 ? 'var(--amber)' : 'var(--red)',
          }}>
            1 : {rec.crv}
          </span>
          {rec.regime_summary && (
            <span style={{ color: 'var(--text-4)', fontSize: 12, marginLeft: 'auto', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {rec.regime_summary}
            </span>
          )}
        </div>
      )}

      {/* Positionsgrösse */}
      {!compact && rec.sizing && (
        <div style={{ marginBottom: 14 }}>
          <div className="label-caps" style={{ marginBottom: 8 }}>Positionsgrösse</div>
          <SizingBlock sizing={rec.sizing} />
        </div>
      )}

      {/* Bias Warning */}
      {rec.has_bias_warning && rec.bias_risk && (
        <div style={{
          padding: '10px 14px', borderRadius: 10, marginBottom: 14,
          background: 'rgba(245,158,11,0.08)',
          border: '1px solid rgba(245,158,11,0.25)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="var(--amber)" strokeWidth="2.5">
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
              <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
            </svg>
            <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--amber)', letterSpacing: '.02em' }}>
              Bias-Risiko erkannt
            </span>
          </div>
          <BiasBar score={rec.bias_risk.overall_score} />
          {(rec.bias_risk?.detected_biases?.length ?? 0) > 0 && (
            <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap', marginTop: 8 }}>
              {rec.bias_risk?.detected_biases?.map((b) => (
                <Badge key={b} variant="amber">{b.replace('_', ' ')}</Badge>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Key Risks */}
      {!compact && (rec.key_risks?.length ?? 0) > 0 && (
        <div>
          <div className="label-caps" style={{ marginBottom: 8 }}>Risiken</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
            {rec.key_risks?.slice(0, 3).map((risk, i) => (
              <div key={i} style={{
                display: 'flex', gap: 10, alignItems: 'flex-start',
                fontSize: 12, color: 'var(--text-3)', lineHeight: 1.5,
              }}>
                <span style={{ color: 'var(--red)', flexShrink: 0, marginTop: 1 }}>▲</span>
                {risk}
              </div>
            ))}
          </div>
        </div>
      )}
    </Card>
  )
}

function PriceCell({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div style={{ textAlign: 'center', padding: '10px 8px', background: 'var(--bg-elevated)' }}>
      <div className="label-caps" style={{ marginBottom: 5 }}>{label}</div>
      <div className="font-num" style={{ fontSize: 14, fontWeight: 700, color: color ?? 'var(--text-1)' }}>
        {value}
      </div>
    </div>
  )
}

// Kompakte Zeile für Dashboard-Preview
export function RecommendationRow({ rec }: { rec: Recommendation }) {
  return (
    <div className="list-row" style={{ display: 'flex', alignItems: 'center', gap: 14, padding: '11px 20px' }}>
      <PriorityDot priority={rec.priority} size="lg" />
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontWeight: 600, fontSize: 14, color: 'var(--text-1)' }}>{rec.asset_symbol}</div>
        <div style={{
          fontSize: 12, color: 'var(--text-4)', marginTop: 2,
          overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
        }}>
          {rec.rationale?.slice(0, 55) ?? ''}…
        </div>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 5 }}>
        <ActionBadge action={rec.action} />
        {rec.crv && (
          <span className="font-num" style={{ fontSize: 11, color: 'var(--text-4)' }}>
            CRV 1:{rec.crv}
          </span>
        )}
      </div>
    </div>
  )
}
