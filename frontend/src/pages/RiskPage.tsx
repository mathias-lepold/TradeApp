import { useRef } from 'react'
import { Doughnut } from 'react-chartjs-2'
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js'
import { useRisk } from '../hooks/useApi'
import type { RiskScenario, RiskConcentration } from '../api/types'
import { LoadingSpinner } from '../components/ui/LoadingSpinner'
import { StatTile } from '../components/ui/Card'

ChartJS.register(ArcElement, Tooltip, Legend)

const fmt = (n: number, d = 0) => n.toLocaleString('de-CH', { minimumFractionDigits: d, maximumFractionDigits: d })
const pnlColor = (v: number) => v > 0 ? 'var(--green)' : v < 0 ? 'var(--red)' : 'var(--text-3)'

const COLORS = ['#3b82f6', '#22c55e', '#f59e0b', '#a78bfa', '#f87171', '#34d399']

// ── Donut Chart ───────────────────────────────────────────────────────────────

function ConcentrationChart({ items }: { items: RiskConcentration[] }) {
  const chartRef = useRef(null)

  const data = {
    labels: items.map(i => i.symbol),
    datasets: [{
      data: items.map(i => i.weight_pct),
      backgroundColor: COLORS.slice(0, items.length),
      borderColor: '#f8fafc',
      borderWidth: 3,
      hoverOffset: 6,
    }],
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    cutout: '68%',
    plugins: {
      legend: {
        position: 'right' as const,
        labels: {
          color: '#94a3b8',
          padding: 16,
          font: { size: 12, family: 'Inter' },
          usePointStyle: true,
          pointStyleWidth: 8,
        },
      },
      tooltip: {
        backgroundColor: '#ffffff',
        borderColor: '#e2e8f0',
        borderWidth: 1,
        titleColor: '#0f172a',
        bodyColor: '#64748b',
        padding: 12,
        callbacks: {
          label: (ctx: { label: string; parsed: number }) =>
            ` ${ctx.label}: ${ctx.parsed.toFixed(1)}%`,
        },
      },
    },
  }

  return (
    <div style={{ position: 'relative', height: 220 }}>
      <Doughnut ref={chartRef} data={data} options={options} />
    </div>
  )
}

// ── Scenarios ─────────────────────────────────────────────────────────────────

function ScenarioBar({ scenario }: { scenario: RiskScenario }) {
  const pct  = scenario.shock_pct
  const fill = Math.min(Math.abs(pct) / 40 * 100, 100)
  const color = pct >= 0 ? 'var(--green)' : 'var(--red)'

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 16, padding: '12px 0', borderBottom: '1px solid var(--border-dim)' }}>
      <div style={{ minWidth: 120, fontSize: 13, color: 'var(--text-2)', fontWeight: 500 }}>{scenario.scenario}</div>
      <div style={{ flex: 1, height: 6, background: 'var(--bg-elevated)', borderRadius: 3, overflow: 'hidden' }}>
        <div style={{
          height: '100%', width: `${fill}%`,
          background: color, borderRadius: 3,
          transition: 'width 0.5s ease',
        }} />
      </div>
      <div style={{ minWidth: 110, textAlign: 'right' }}>
        <span className="font-num" style={{ fontWeight: 700, color, fontSize: 14 }}>
          {pct >= 0 ? '+' : ''}{fmt(scenario.pnl_chf)} CHF
        </span>
      </div>
      <div style={{ minWidth: 90, textAlign: 'right' }}>
        <span className="font-num" style={{ fontSize: 12, color: 'var(--text-4)' }}>
          = {fmt(scenario.new_value)} CHF
        </span>
      </div>
    </div>
  )
}

// ── Concentration Table ────────────────────────────────────────────────────────

function ConcentrationTable({ items }: { items: RiskConcentration[] }) {
  return (
    <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: 16 }}>
      <thead>
        <tr style={{ borderBottom: '1px solid var(--border-std)' }}>
          {['Symbol', 'Wert CHF', 'Gewicht', 'Tages-Vol.', 'VaR 95% (1T)'].map(h => (
            <th key={h} style={{
              padding: '8px 12px', textAlign: 'right', fontSize: 11,
              fontWeight: 600, color: 'var(--text-4)', letterSpacing: '0.06em', textTransform: 'uppercase',
            }}>{h}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {items.map((item, i) => (
          <tr key={item.symbol} style={{ borderBottom: '1px solid var(--border-dim)' }}>
            <td style={{ padding: '11px 12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <div style={{ width: 10, height: 10, borderRadius: '50%', background: COLORS[i] ?? '#64748b', flexShrink: 0 }} />
                <span style={{ fontWeight: 700, color: 'var(--text-1)' }}>{item.symbol}</span>
              </div>
            </td>
            <td style={{ padding: '11px 12px', textAlign: 'right' }} className="font-num">
              {fmt(item.value_chf)} CHF
            </td>
            <td style={{ padding: '11px 12px', textAlign: 'right' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, justifyContent: 'flex-end' }}>
                <div style={{ width: 60, height: 4, background: 'var(--bg-elevated)', borderRadius: 2, overflow: 'hidden' }}>
                  <div style={{ height: '100%', width: `${item.weight_pct}%`, background: COLORS[i] ?? '#64748b', borderRadius: 2 }} />
                </div>
                <span className="font-num" style={{ fontSize: 13, fontWeight: 600 }}>{item.weight_pct.toFixed(1)}%</span>
              </div>
            </td>
            <td style={{ padding: '11px 12px', textAlign: 'right' }} className="font-num">
              <span style={{ color: item.daily_vol_pct > 2.5 ? 'var(--gold)' : 'var(--text-3)' }}>
                {item.daily_vol_pct.toFixed(2)}%
              </span>
            </td>
            <td style={{ padding: '11px 12px', textAlign: 'right' }}>
              <span className="font-num" style={{ color: 'var(--red)', fontWeight: 600 }}>
                −{fmt(item.var_95_chf)} CHF
              </span>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function RiskPage() {
  const { data: risk, isLoading, isError } = useRisk()

  if (isLoading) return <LoadingSpinner message="Berechne Risikokennzahlen…" fullPage />
  if (isError || !risk) return (
    <div style={{ textAlign: 'center', padding: 40, color: 'var(--red)' }}>
      Fehler beim Laden der Risikodaten
    </div>
  )

  const varPct = risk.var_95_1d_pct

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

      {/* ── Stat Tiles ── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
        <StatTile
          label="Portfolio-Wert"
          value={`${fmt(risk.portfolio_value_chf)} CHF`}
          sub={`${risk.num_positions} Positionen`}
          mono
        />
        <StatTile
          label="VaR 95% (1 Tag)"
          value={`−${fmt(risk.var_95_1d_chf)} CHF`}
          sub={`${varPct.toFixed(2)}% des Portfolios`}
          negative
          mono
        />
        <StatTile
          label="Max. Drawdown"
          value={`−${risk.max_drawdown_pct.toFixed(2)}%`}
          sub="Aus Preishistorie"
          negative={risk.max_drawdown_pct > 5}
          mono
        />
        <StatTile
          label="Risiko-Level"
          value={varPct < 1.5 ? 'Niedrig' : varPct < 2.5 ? 'Moderat' : 'Erhöht'}
          sub={`VaR < ${varPct < 1.5 ? '1.5' : varPct < 2.5 ? '2.5' : '>2.5'}%`}
          accentColor={varPct < 1.5 ? 'var(--green)' : varPct < 2.5 ? 'var(--gold)' : 'var(--red)'}
        />
      </div>

      {/* ── VaR Explanation ── */}
      <div style={{
        padding: '12px 18px', borderRadius: 10,
        background: 'rgba(59,130,246,0.06)', border: '1px solid rgba(59,130,246,0.15)',
        fontSize: 13, color: 'var(--text-3)', lineHeight: 1.6,
      }}>
        <strong style={{ color: 'var(--accent)' }}>Value at Risk (VaR 95%, 1 Tag):</strong>{' '}
        Mit 95%-iger Wahrscheinlichkeit verliert das Portfolio innerhalb eines Handelstages
        nicht mehr als <strong style={{ color: 'var(--text-1)' }} className="font-num">{fmt(risk.var_95_1d_chf)} CHF</strong>{' '}
        ({varPct.toFixed(2)}%). Berechnet via parametrischem Modell aus der Preisvolatilität der letzten {Math.round(risk.num_positions * 20)} Ticks.
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>

        {/* ── Konzentration Donut ── */}
        <div className="card">
          <div className="label-caps" style={{ marginBottom: 16 }}>Portfolio-Konzentration</div>
          {risk.concentration.length > 0 ? (
            <>
              <ConcentrationChart items={risk.concentration} />
              <ConcentrationTable items={risk.concentration} />
            </>
          ) : (
            <div style={{ textAlign: 'center', padding: 32, color: 'var(--text-4)' }}>Keine Positionen</div>
          )}
        </div>

        {/* ── Szenarien ── */}
        <div className="card">
          <div className="label-caps" style={{ marginBottom: 16 }}>Verlust-Szenarien</div>
          <div style={{ fontSize: 12, color: 'var(--text-4)', marginBottom: 16 }}>
            Erwarteter Portfolio-Wert bei gegebenen Marktschocks
          </div>
          {risk.scenarios.map(s => <ScenarioBar key={s.scenario} scenario={s} />)}

          <div style={{ marginTop: 20, padding: '14px 16px', borderRadius: 8, background: 'var(--bg-elevated)', border: '1px solid var(--border-std)' }}>
            <div className="label-caps" style={{ marginBottom: 10 }}>Risiko-Checkliste</div>
            {[
              { ok: risk.concentration[0]?.weight_pct < 40, label: 'Keine Einzelposition > 40%' },
              { ok: risk.var_95_1d_pct < 3, label: 'VaR unter 3% (1-Tages-Limit)' },
              { ok: risk.max_drawdown_pct < 20, label: 'Max. Drawdown unter 20%' },
              { ok: risk.num_positions >= 3, label: 'Mindestens 3 Positionen (Diversifikation)' },
            ].map(({ ok, label }) => (
              <div key={label} style={{ display: 'flex', gap: 10, alignItems: 'center', padding: '6px 0', borderBottom: '1px solid var(--border-dim)' }}>
                <span style={{ color: ok ? 'var(--green)' : 'var(--red)', fontSize: 14 }}>{ok ? '✓' : '✗'}</span>
                <span style={{ fontSize: 13, color: ok ? 'var(--text-2)' : 'var(--text-4)' }}>{label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

    </div>
  )
}
