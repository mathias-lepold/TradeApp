import { useRegime, useSignals, useRecommendations, usePortfolio, useCycle, useLiquidity, useHypothesis } from '../hooks/useApi'
import { DominanzKarteConnected } from '../components/shared/DominanzKarte'
import { RegimeBanner, RegimeSkeleton } from '../components/shared/RegimeBanner'
import { SignalRow } from '../components/shared/SignalCard'
import { RecommendationRow } from '../components/shared/RecommendationCard'
import { Card, CardHeader, StatTile } from '../components/ui/Card'
import { LoadingSpinner, ErrorState } from '../components/ui/LoadingSpinner'
import { useNavigate } from 'react-router-dom'
import type { MarketCycleState, LiquidityState, HypothesisSet, FundingCondition, CyclePhase } from '../api/types'

function fmt(n: number, decimals = 2) {
  return n.toLocaleString('de-CH', { minimumFractionDigits: decimals, maximumFractionDigits: decimals })
}

// ── Phase Meta ────────────────────────────────────────────────────────────────

const PHASE_META: Record<CyclePhase, { label: string; color: string; icon: string }> = {
  fundamental:             { label: 'Fundamental',         color: 'var(--accent)',  icon: '◆' },
  external_shock:          { label: 'Externer Schock',     color: 'var(--red)',     icon: '⚡' },
  first_reaction:          { label: 'Erstreaktion',        color: 'var(--amber)',   icon: '→' },
  psychological_overshoot: { label: 'Psych. Überschuss',   color: 'var(--red)',     icon: '↕' },
  stabilization:           { label: 'Stabilisierung',      color: 'var(--green)',   icon: '≈' },
  return_to_fundamentals:  { label: 'Rückkehr Fundament.', color: 'var(--green)',   icon: '↩' },
}

const FUNDING_META: Record<FundingCondition, { label: string; color: string }> = {
  ample:      { label: 'Reichlich',    color: 'var(--green)' },
  normal:     { label: 'Normal',       color: 'var(--accent)' },
  tightening: { label: 'Verschärfend', color: 'var(--amber)' },
  tight:      { label: 'Eng',          color: 'var(--amber)' },
  stressed:   { label: 'Gestresst',    color: 'var(--red)' },
}

// ── No-Trade Banner ───────────────────────────────────────────────────────────

function NoTradeBanner() {
  return (
    <div className="no-trade-banner anim-fade">
      <div style={{
        width: 44, height: 44, borderRadius: 10,
        background: 'rgba(239,68,68,0.15)',
        border: '1px solid rgba(239,68,68,0.3)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 20, flexShrink: 0,
      }}>
        🚫
      </div>
      <div>
        <div style={{ fontWeight: 800, fontSize: 14, color: '#dc2626', letterSpacing: '.04em', textTransform: 'uppercase' }}>
          No-Trade-Flag aktiv
        </div>
        <div style={{ fontSize: 13, color: 'var(--text-3)', marginTop: 4, lineHeight: 1.5 }}>
          Regime-Fragility zu hoch — Decision Engine empfiehlt keinen Neueinstieg bis zur Stabilisierung.
        </div>
      </div>
      <div style={{
        marginLeft: 'auto', padding: '6px 14px', borderRadius: 8,
        background: 'rgba(239,68,68,0.15)', border: '1px solid rgba(239,68,68,0.3)',
        fontSize: 12, fontWeight: 700, color: '#dc2626',
        flexShrink: 0,
      }}>
        Abwarten
      </div>
    </div>
  )
}

// ── Stat Icons ────────────────────────────────────────────────────────────────

const IconPortfolio = () => (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2"/>
  </svg>
)
const IconTrend = () => (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/>
  </svg>
)
const IconSignal = () => (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
  </svg>
)
const IconShield = () => (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
  </svg>
)

// ── Marktzyklus Karte ─────────────────────────────────────────────────────────

function MarktzyklusKarte({ cycle }: { cycle: MarketCycleState }) {
  const dominant = PHASE_META[cycle.dominant_phase] ?? PHASE_META.fundamental
  const sorted   = [...cycle.active_phases].sort((a, b) => b.intensity - a.intensity)

  return (
    <Card>
      <CardHeader
        title="Marktzyklus"
        subtitle={`Instabilität ${Math.round(cycle.overall_instability * 100)}%`}
      />

      {/* Dominante Phase */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 14,
        padding: '12px 14px', borderRadius: 10, marginBottom: 16,
        background: `${dominant.color}12`,
        border: `1px solid ${dominant.color}25`,
      }}>
        <div style={{
          width: 40, height: 40, borderRadius: 9,
          background: `${dominant.color}20`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 18, color: dominant.color, flexShrink: 0,
        }}>
          {dominant.icon}
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '.1em', textTransform: 'uppercase', color: dominant.color, opacity: 0.7 }}>
            Dominante Phase
          </div>
          <div style={{ fontWeight: 700, fontSize: 14, color: dominant.color, marginTop: 2 }}>
            {dominant.label}
          </div>
          <div style={{ fontSize: 11, color: 'var(--text-4)', marginTop: 2 }}>
            Transition Speed {Math.round(cycle.transition_speed * 100)}%
          </div>
        </div>
        <div className="font-num" style={{ fontSize: 24, fontWeight: 800, color: dominant.color }}>
          {Math.round((sorted[0]?.intensity ?? 0) * 100)}%
        </div>
      </div>

      {/* Alle aktiven Phasen */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {sorted.map((p) => {
          const meta = PHASE_META[p.phase as CyclePhase] ?? PHASE_META.fundamental
          return (
            <div key={p.phase}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                <span style={{ fontSize: 12, color: meta.color, fontWeight: 600 }}>
                  {meta.icon} {meta.label}
                </span>
                <span className="font-num" style={{ fontSize: 11, color: 'var(--text-4)' }}>
                  {Math.round(p.intensity * 100)}%
                </span>
              </div>
              <div className="progress-track">
                <div className="progress-fill" style={{ width: `${p.intensity * 100}%`, background: meta.color }} />
              </div>
            </div>
          )
        })}
      </div>

      {/* Signale */}
      {(cycle.signals?.length ?? 0) > 0 && (
        <div style={{ marginTop: 14, display: 'flex', flexDirection: 'column', gap: 4 }}>
          {cycle.signals.slice(0, 3).map((s, i) => (
            <div key={i} style={{
              fontSize: 11, color: 'var(--text-3)', padding: '4px 10px',
              borderLeft: '2px solid var(--border-bold)',
              lineHeight: 1.4,
            }}>
              {s}
            </div>
          ))}
        </div>
      )}
    </Card>
  )
}

// ── Liquiditäts Karte ─────────────────────────────────────────────────────────

function StressGauge({ value, label }: { value: number; label: string }) {
  const color = value > 0.65 ? 'var(--red)' : value > 0.40 ? 'var(--amber)' : 'var(--green)'
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 5 }}>
        <span className="label-caps">{label}</span>
        <span className="font-num" style={{ fontSize: 12, fontWeight: 700, color }}>
          {Math.round(value * 100)}%
        </span>
      </div>
      <div className="progress-track" style={{ height: 6 }}>
        <div className="progress-fill" style={{ width: `${value * 100}%`, background: color }} />
      </div>
    </div>
  )
}

function LiquiditätsKarte({ liq }: { liq: LiquidityState }) {
  const funding = FUNDING_META[liq.funding_conditions] ?? FUNDING_META.normal

  return (
    <Card>
      <CardHeader
        title="Liquidität"
        subtitle={`VIX-Proxy ${liq.vix_proxy.toFixed(1)} · Spread ${(liq.bid_ask_spread_proxy * 100).toFixed(2)} bp`}
      />

      {/* Funding Badge */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '10px 14px', borderRadius: 10, marginBottom: 16,
        background: `${funding.color}10`,
        border: `1px solid ${funding.color}25`,
      }}>
        <span style={{ fontSize: 13, color: 'var(--text-2)', fontWeight: 500 }}>Funding-Bedingungen</span>
        <span style={{ fontSize: 14, fontWeight: 700, color: funding.color }}>{funding.label}</span>
      </div>

      {/* Gauges */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        <StressGauge value={liq.liquidity_stress}    label="Liquiditätsstress" />
        <StressGauge value={liq.forced_selling_risk} label="Zwangsverkaufsrisiko" />
      </div>

      <div className="divider" />

      {/* Metriken Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
        <Metric label="Spread-Proxy" value={`${(liq.bid_ask_spread_proxy * 100).toFixed(2)} bp`}
          color={liq.bid_ask_spread_proxy > 0.003 ? 'var(--red)' : 'var(--green)'} />
        <Metric label="Markttiefe" value={`${Math.round(liq.market_depth_score * 100)}%`}
          color={liq.market_depth_score > 0.6 ? 'var(--green)' : 'var(--amber)'} />
      </div>

      {/* Signale */}
      {(liq.signals?.length ?? 0) > 0 && (
        <div style={{ marginTop: 14, display: 'flex', flexDirection: 'column', gap: 4 }}>
          {liq.signals.slice(0, 2).map((s, i) => (
            <div key={i} style={{
              fontSize: 11, color: 'var(--amber)', padding: '4px 10px',
              borderLeft: '2px solid rgba(245,158,11,0.5)',
              lineHeight: 1.4,
            }}>
              {s}
            </div>
          ))}
        </div>
      )}
    </Card>
  )
}

function Metric({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div>
      <div className="label-caps" style={{ marginBottom: 4 }}>{label}</div>
      <div className="font-num" style={{ fontSize: 14, fontWeight: 700, color: color ?? 'var(--text-1)' }}>
        {value}
      </div>
    </div>
  )
}

// ── Hypothesen Karte ──────────────────────────────────────────────────────────

function HypothesenKarte({ hyp }: { hyp: HypothesisSet }) {
  const conviction = hyp.overall_conviction
  const convColor = conviction > 0.65 ? 'var(--green)' : conviction > 0.40 ? 'var(--amber)' : 'var(--red)'

  return (
    <Card>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 18 }}>
        <div>
          <div className="label-caps" style={{ marginBottom: 4 }}>Hypothesen · {hyp.asset_symbol}</div>
          <div style={{ color: 'var(--text-3)', fontSize: 13 }}>Basis vs. Gegenhypothese</div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div className="label-caps" style={{ marginBottom: 4 }}>Überzeugung</div>
          <div className="font-num" style={{ fontSize: 22, fontWeight: 700, color: convColor }}>
            {Math.round(conviction * 100)}%
          </div>
        </div>
      </div>

      {/* Überzeugungsbalken */}
      <div style={{ marginBottom: 18 }}>
        <div className="progress-track" style={{ height: 6 }}>
          <div className="progress-fill" style={{ width: `${conviction * 100}%`, background: convColor }} />
        </div>
      </div>

      {/* Basis vs Gegen — nebeneinander */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 14 }}>
        {/* Basishypothese */}
        <div style={{
          padding: '14px', borderRadius: 10,
          background: 'rgba(34,197,94,0.07)',
          border: '1px solid rgba(34,197,94,0.2)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
            <span style={{ fontSize: 10, fontWeight: 800, letterSpacing: '.1em', textTransform: 'uppercase', color: 'var(--green)' }}>
              ↑ Basis
            </span>
            <span className="font-num" style={{ fontSize: 12, fontWeight: 700, color: 'var(--green)' }}>
              {Math.round(hyp.base_hypothesis.confidence * 100)}%
            </span>
          </div>
          <div style={{ fontWeight: 600, fontSize: 13, color: 'var(--text-1)', marginBottom: 6, lineHeight: 1.3 }}>
            {hyp.base_hypothesis.title}
          </div>
          <div style={{ fontSize: 12, color: 'var(--text-3)', lineHeight: 1.5 }}>
            {hyp.base_hypothesis.description}
          </div>
          {hyp.base_hypothesis.price_target_pct != null && (
            <div className="font-num" style={{
              marginTop: 8, fontSize: 12, fontWeight: 700, color: 'var(--green)',
              padding: '4px 8px', background: 'rgba(34,197,94,0.1)', borderRadius: 6, display: 'inline-block',
            }}>
              {hyp.base_hypothesis.price_target_pct > 0 ? '+' : ''}{hyp.base_hypothesis.price_target_pct.toFixed(1)}%
              {hyp.base_hypothesis.time_horizon_days && <span style={{ color: 'var(--text-4)', fontWeight: 400 }}> · {hyp.base_hypothesis.time_horizon_days}T</span>}
            </div>
          )}
        </div>

        {/* Gegenhypothese */}
        <div style={{
          padding: '14px', borderRadius: 10,
          background: 'rgba(239,68,68,0.06)',
          border: '1px solid rgba(239,68,68,0.18)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
            <span style={{ fontSize: 10, fontWeight: 800, letterSpacing: '.1em', textTransform: 'uppercase', color: 'var(--red)' }}>
              ↓ Gegen
            </span>
            <span className="font-num" style={{ fontSize: 12, fontWeight: 700, color: 'var(--red)' }}>
              {Math.round(hyp.counter_hypothesis.confidence * 100)}%
            </span>
          </div>
          <div style={{ fontWeight: 600, fontSize: 13, color: 'var(--text-1)', marginBottom: 6, lineHeight: 1.3 }}>
            {hyp.counter_hypothesis.title}
          </div>
          <div style={{ fontSize: 12, color: 'var(--text-3)', lineHeight: 1.5 }}>
            {hyp.counter_hypothesis.description}
          </div>
        </div>
      </div>

      {/* Phasenwechsel-Trigger */}
      {(hyp.phase_transition_triggers?.length ?? 0) > 0 && (
        <div>
          <div className="label-caps" style={{ marginBottom: 8 }}>Trigger-Bedingungen</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {hyp.phase_transition_triggers.slice(0, 3).map((t, i) => (
              <div key={i} style={{
                fontSize: 12, color: 'var(--text-3)', padding: '4px 10px',
                borderLeft: '2px solid rgba(245,158,11,0.5)',
                lineHeight: 1.4,
              }}>
                {t}
              </div>
            ))}
          </div>
        </div>
      )}
    </Card>
  )
}

// ── Regime Detail Karte ───────────────────────────────────────────────────────

function RegimeDetailsKarte({ title, items, bullet }: { title: string; items: string[]; bullet: string }) {
  return (
    <Card>
      <CardHeader title={title} />
      {items.length > 0 ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {items.map((item, i) => (
            <div key={i} style={{
              display: 'flex', gap: 10, alignItems: 'flex-start',
              fontSize: 13, color: 'var(--text-2)', lineHeight: 1.5,
            }}>
              <span style={{ color: bullet === 'risk' ? 'var(--red)' : 'var(--accent)', flexShrink: 0, marginTop: 2 }}>
                {bullet === 'risk' ? '▲' : '●'}
              </span>
              {item}
            </div>
          ))}
        </div>
      ) : (
        <div style={{ color: 'var(--text-4)', fontSize: 13 }}>Keine Einträge verfügbar</div>
      )}
    </Card>
  )
}

// ── Dashboard ─────────────────────────────────────────────────────────────────

export default function Dashboard() {
  const navigate = useNavigate()
  const { data: regime, isLoading: regimeLoading, isError: regimeError, refetch: refetchRegime } = useRegime()
  const { data: signals        = [] } = useSignals(65)
  const { data: recommendations = [] } = useRecommendations()
  const { data: portfolio }   = usePortfolio()
  const { data: cycle }       = useCycle()
  const { data: liquidity }   = useLiquidity()
  const { data: hypothesis }  = useHypothesis('NVDA')

  const topSignals  = signals.slice(0, 5)
  const topRecs     = recommendations.filter((r) => !r?.is_expired).slice(0, 4)
  const buyRecs     = recommendations.filter((r) => r.action === 'buy' || r.action === 'add')
  const noTradeRecs = recommendations.filter((r) => r.no_trade_flag === true)
  const showNoTrade = noTradeRecs.length > 0

  const totalPnl       = portfolio?.total_pnl_chf ?? 0
  const totalPnlPct    = portfolio?.total_pnl_percent ?? 0
  const portfolioValue = portfolio?.total_value_chf ?? 0

  return (
    <div className="stagger" style={{ display: 'flex', flexDirection: 'column', gap: 22 }}>

      {/* ── No-Trade Banner ── */}
      {showNoTrade && <NoTradeBanner />}

      {/* ── Regime Banner ── */}
      {regimeLoading && <RegimeSkeleton />}
      {regimeError   && <ErrorState message="Regime-Daten nicht verfügbar" onRetry={refetchRegime} />}
      {regime        && <RegimeBanner regime={regime} />}

      {/* ── 4 Stat Tiles ── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 14 }}>
        <StatTile
          label="Portfolio CHF"
          value={portfolioValue > 0 ? `CHF ${fmt(portfolioValue, 0)}` : '—'}
          mono
          icon={<IconPortfolio />}
        />
        <StatTile
          label="Gesamt P&L"
          value={totalPnl !== 0 ? `${totalPnl > 0 ? '+' : ''}CHF ${fmt(totalPnl, 0)}` : '—'}
          sub={totalPnlPct !== 0 ? `${totalPnlPct > 0 ? '+' : ''}${fmt(totalPnlPct)}%` : undefined}
          positive={totalPnl > 0}
          negative={totalPnl < 0}
          mono
          icon={<IconTrend />}
        />
        <StatTile
          label="Aktive Signale"
          value={signals.length}
          sub={`${buyRecs.length} Kauf-Empfehlungen`}
          icon={<IconSignal />}
          accentColor="var(--accent)"
        />
        <StatTile
          label="Max. Position"
          value={regime ? `${regime.max_position_size_pct}%` : '—'}
          sub={regime?.label ?? 'Regime lädt…'}
          icon={<IconShield />}
        />
      </div>

      {/* ── Marktzyklus + Liquidität + Dominanz ── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16 }}>
        {cycle
          ? <MarktzyklusKarte cycle={cycle} />
          : <Card><LoadingSpinner message="Lade Marktzyklus…" /></Card>}
        {liquidity
          ? <LiquiditätsKarte liq={liquidity} />
          : <Card><LoadingSpinner message="Lade Liquiditätsdaten…" /></Card>}
        <DominanzKarteConnected />
      </div>

      {/* ── Top Signale + Empfehlungen ── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <Card style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ padding: '20px 20px 0' }}>
            <CardHeader
              title="Top Signale"
              subtitle={`${signals.length} aktive Signale`}
              action={
                <button className="btn-ghost" style={{ fontSize: 12 }} onClick={() => navigate('/signals')}>
                  Alle ansehen →
                </button>
              }
            />
          </div>
          {topSignals.length === 0
            ? <div style={{ padding: 20 }}><LoadingSpinner message="Lade Signale…" /></div>
            : topSignals.map((s) => <SignalRow key={s.id} signal={s} />)
          }
        </Card>

        <Card style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ padding: '20px 20px 0' }}>
            <CardHeader
              title="Decision Engine"
              subtitle={`${topRecs.length} Empfehlungen`}
              action={
                <button className="btn-ghost" style={{ fontSize: 12 }} onClick={() => navigate('/recommendations')}>
                  Alle ansehen →
                </button>
              }
            />
          </div>
          {topRecs.length === 0
            ? <div style={{ padding: 20 }}><LoadingSpinner message="Lade Empfehlungen…" /></div>
            : topRecs.map((r) => <RecommendationRow key={r.id} rec={r} />)
          }
        </Card>
      </div>

      {/* ── Hypothesen (volle Breite) ── */}
      {hypothesis && <HypothesenKarte hyp={hypothesis} />}

      {/* ── Regime Details ── */}
      {regime && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <RegimeDetailsKarte
            title="Regime-Merkmale"
            items={regime.characteristics ?? []}
            bullet="char"
          />
          <RegimeDetailsKarte
            title="Aktive Risiken"
            items={regime.active_risks ?? []}
            bullet="risk"
          />
        </div>
      )}

    </div>
  )
}
