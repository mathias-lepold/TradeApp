import { useState, useRef } from 'react'
import { Line } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  CategoryScale, LinearScale, PointElement, LineElement,
  Title, Tooltip, Legend, Filler,
} from 'chart.js'
import { useRunBacktest, useBacktestResult, useBacktestEquity } from '../hooks/useApi'
import type { BacktestConfig, TradeRecord, BacktestMetrics } from '../api/types'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler)

// ── Konstanten ────────────────────────────────────────────────────────────────

const SYMBOLS = ['NVDA', 'MSFT', 'AAPL', 'NOVN', 'ZGLD', 'AMZN', 'GOOGL', 'META', 'SPY', 'TSM']

function todayStr() {
  return new Date().toISOString().slice(0, 10)
}
function oneYearAgoStr() {
  const d = new Date()
  d.setFullYear(d.getFullYear() - 1)
  return d.toISOString().slice(0, 10)
}

// ── Hilfsfunktionen ───────────────────────────────────────────────────────────

function fmtChf(n: number) {
  return n.toLocaleString('de-CH', { maximumFractionDigits: 0 })
}

function fmtPct(n: number, digits = 2) {
  const s = n.toFixed(digits)
  return `${n >= 0 ? '+' : ''}${s}%`
}

function metricColor(value: number, goodIfPositive = true) {
  if (value === 0) return 'var(--text-3)'
  const isGood = goodIfPositive ? value > 0 : value < 0
  return isGood ? 'var(--green)' : 'var(--red)'
}

// ── Kennzahlen-Karte ──────────────────────────────────────────────────────────

function MetricGrid({ metrics }: { metrics: BacktestMetrics }) {
  const items = [
    { label: 'Endkapital CHF',       value: `CHF ${fmtChf(metrics.final_equity)}`, color: 'var(--text-1)', mono: true },
    { label: 'Total Return',         value: fmtPct(metrics.total_return_pct),      color: metricColor(metrics.total_return_pct), mono: true },
    { label: 'Annualisiert',         value: fmtPct(metrics.annualized_return_pct), color: metricColor(metrics.annualized_return_pct), mono: true },
    { label: 'Max. Drawdown',        value: `-${metrics.max_drawdown_pct.toFixed(2)}%`, color: metrics.max_drawdown_pct > 20 ? 'var(--red)' : metrics.max_drawdown_pct > 10 ? 'var(--amber)' : 'var(--green)', mono: true },
    { label: 'Sharpe Ratio',         value: metrics.sharpe_ratio.toFixed(3),       color: metrics.sharpe_ratio >= 1 ? 'var(--green)' : metrics.sharpe_ratio >= 0.5 ? 'var(--amber)' : 'var(--red)', mono: true },
    { label: 'Calmar Ratio',         value: metrics.calmar_ratio.toFixed(3),       color: metrics.calmar_ratio >= 1 ? 'var(--green)' : 'var(--amber)', mono: true },
    { label: 'Win Rate',             value: `${(metrics.win_rate * 100).toFixed(1)}%`, color: metrics.win_rate >= 0.5 ? 'var(--green)' : 'var(--amber)', mono: true },
    { label: 'Profit Factor',        value: metrics.profit_factor === Infinity ? '∞' : metrics.profit_factor.toFixed(2), color: metrics.profit_factor >= 1.5 ? 'var(--green)' : metrics.profit_factor >= 1 ? 'var(--amber)' : 'var(--red)', mono: true },
    { label: 'Anzahl Trades',        value: String(metrics.num_trades),            color: 'var(--text-1)' },
    { label: 'Gewinner / Verlierer', value: `${metrics.num_wins} / ${metrics.num_losses}`, color: 'var(--text-1)' },
    { label: 'Ø Trade-Dauer',        value: `${metrics.avg_trade_duration_days.toFixed(1)} T`, color: 'var(--text-3)' },
    { label: 'Bester Trade',         value: fmtPct(metrics.best_trade_pct),       color: 'var(--green)', mono: true },
    { label: 'Schlechtester Trade',  value: fmtPct(metrics.worst_trade_pct),      color: 'var(--red)', mono: true },
    { label: 'Ø Gewinn-Trade',       value: fmtPct(metrics.avg_win_pct),          color: 'var(--green)', mono: true },
    { label: 'Ø Verlust-Trade',      value: fmtPct(metrics.avg_loss_pct),         color: 'var(--red)', mono: true },
    { label: 'Max. Gewinnserie',     value: String(metrics.max_consecutive_wins),  color: 'var(--green)' },
  ]

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 12 }}>
      {items.map(({ label, value, color, mono }) => (
        <div key={label} style={{
          background: 'var(--bg-elevated)',
          border: '1px solid var(--border-dim)',
          borderRadius: 10, padding: '14px 16px',
        }}>
          <div className="label-caps" style={{ marginBottom: 6 }}>{label}</div>
          <div className={mono ? 'font-num' : ''} style={{
            fontSize: 18, fontWeight: 700, color, lineHeight: 1,
          }}>
            {value}
          </div>
        </div>
      ))}
    </div>
  )
}

// ── Equity Chart ──────────────────────────────────────────────────────────────

function EquityChart({ data, initialCapital }: {
  data: { date: string; equity: number; drawdown_pct: number }[]
  initialCapital: number
}) {
  const labels  = data.map((p) => p.date.slice(5)) // MM-DD
  const equities = data.map((p) => p.equity)
  const drawdowns = data.map((p) => -p.drawdown_pct)

  const chartData = {
    labels,
    datasets: [
      {
        label: 'Equity CHF',
        data: equities,
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59,130,246,0.06)',
        borderWidth: 2,
        pointRadius: 0,
        fill: true,
        tension: 0.3,
        yAxisID: 'y',
      },
      {
        label: 'Drawdown %',
        data: drawdowns,
        borderColor: 'rgba(239,68,68,0.6)',
        backgroundColor: 'rgba(239,68,68,0.06)',
        borderWidth: 1.5,
        borderDash: [4, 3],
        pointRadius: 0,
        fill: true,
        tension: 0.3,
        yAxisID: 'y2',
      },
    ],
  }

  // Reference line at initial capital
  const refLine = {
    id: 'refLine',
    beforeDraw(chart: ChartJS) {
      const { ctx, chartArea, scales } = chart as any
      if (!chartArea) return
      const y = scales.y.getPixelForValue(initialCapital)
      ctx.save()
      ctx.beginPath()
      ctx.moveTo(chartArea.left, y)
      ctx.lineTo(chartArea.right, y)
      ctx.strokeStyle = 'rgba(148,163,184,0.2)'
      ctx.lineWidth = 1
      ctx.setLineDash([4, 4])
      ctx.stroke()
      ctx.restore()
    },
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: 'index' as const, intersect: false },
    plugins: {
      legend: {
        labels: {
          color: '#64748b',
          font: { size: 12 },
          padding: 20,
        },
      },
      tooltip: {
        backgroundColor: '#ffffff',
        borderColor: '#e2e8f0',
        borderWidth: 1,
        titleColor: '#0f172a',
        bodyColor: '#64748b',
        padding: 10,
        callbacks: {
          label: (ctx: any) => {
            if (ctx.datasetIndex === 0) return `  Equity: CHF ${fmtChf(ctx.raw)}`
            return `  Drawdown: ${Math.abs(ctx.raw as number).toFixed(2)}%`
          },
        },
      },
    },
    scales: {
      x: {
        ticks: { color: '#64748b', maxTicksLimit: 12, font: { size: 11 } },
        grid: { color: 'rgba(45,49,72,0.5)' },
      },
      y: {
        position: 'left' as const,
        ticks: { color: '#64748b', font: { size: 11 }, callback: (v: any) => `CHF ${fmtChf(v)}` },
        grid: { color: 'rgba(45,49,72,0.5)' },
      },
      y2: {
        position: 'right' as const,
        ticks: { color: '#dc2626', font: { size: 11 }, callback: (v: any) => `${Math.abs(v).toFixed(1)}%` },
        grid: { display: false },
      },
    },
  }

  return (
    <div style={{ height: 340 }}>
      <Line data={chartData} options={options} plugins={[refLine]} />
    </div>
  )
}

// ── Trade-Liste ───────────────────────────────────────────────────────────────

const EXIT_LABELS: Record<string, string> = {
  stop_loss:     'Stop-Loss',
  take_profit:   'Take-Profit',
  signal_exit:   'Signal',
  end_of_period: 'Periodenende',
}

function TradeTable({ trades }: { trades: TradeRecord[] }) {
  const [page, setPage] = useState(0)
  const pageSize = 15
  const pages    = Math.max(1, Math.ceil(trades.length / pageSize))
  const visible  = trades.slice(page * pageSize, (page + 1) * pageSize)

  return (
    <div>
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border-std)' }}>
              {['#', 'Einstieg', 'Ausstieg', 'Kauf', 'Verkauf', 'Anzahl', 'Stop', 'Ziel', 'P&L CHF', 'P&L %', 'Dauer', 'Ausstiegsgrund', 'Score'].map((h) => (
                <th key={h} style={{
                  padding: '10px 12px', textAlign: 'left',
                  fontSize: 10, fontWeight: 700, letterSpacing: '.06em',
                  textTransform: 'uppercase', color: 'var(--text-4)',
                  whiteSpace: 'nowrap',
                }}>
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {visible.map((t, i) => {
              const rowN = page * pageSize + i + 1
              return (
                <tr key={t.trade_id} style={{
                  borderBottom: '1px solid var(--border-dim)',
                  background: t.is_win ? 'rgba(34,197,94,0.02)' : 'rgba(239,68,68,0.02)',
                  transition: 'background var(--trans)',
                }}
                  onMouseEnter={e => (e.currentTarget.style.background = 'var(--bg-hover)')}
                  onMouseLeave={e => (e.currentTarget.style.background = t.is_win ? 'rgba(34,197,94,0.02)' : 'rgba(239,68,68,0.02)')}
                >
                  <td style={{ padding: '9px 12px', color: 'var(--text-4)', fontWeight: 600 }}>{rowN}</td>
                  <td style={{ padding: '9px 12px', color: 'var(--text-2)' }}>{t.entry_date}</td>
                  <td style={{ padding: '9px 12px', color: 'var(--text-2)' }}>{t.exit_date}</td>
                  <td className="font-num" style={{ padding: '9px 12px', color: 'var(--text-1)' }}>
                    {t.entry_price.toFixed(2)}
                  </td>
                  <td className="font-num" style={{ padding: '9px 12px', color: t.is_win ? 'var(--green)' : 'var(--red)' }}>
                    {t.exit_price.toFixed(2)}
                  </td>
                  <td className="font-num" style={{ padding: '9px 12px', color: 'var(--text-3)' }}>
                    {t.quantity.toFixed(2)}
                  </td>
                  <td className="font-num" style={{ padding: '9px 12px', color: 'var(--red)', fontSize: 12 }}>
                    {t.stop_loss.toFixed(2)}
                  </td>
                  <td className="font-num" style={{ padding: '9px 12px', color: 'var(--green)', fontSize: 12 }}>
                    {t.take_profit.toFixed(2)}
                  </td>
                  <td className="font-num" style={{
                    padding: '9px 12px', fontWeight: 700,
                    color: t.is_win ? 'var(--green)' : 'var(--red)',
                  }}>
                    {t.pnl_chf >= 0 ? '+' : ''}{fmtChf(t.pnl_chf)}
                  </td>
                  <td className="font-num" style={{
                    padding: '9px 12px', fontSize: 12,
                    color: t.is_win ? 'var(--green)' : 'var(--red)',
                  }}>
                    {fmtPct(t.pnl_pct)}
                  </td>
                  <td style={{ padding: '9px 12px', color: 'var(--text-4)', fontSize: 12 }}>
                    {t.duration_days}T
                  </td>
                  <td style={{ padding: '9px 12px' }}>
                    <span style={{
                      fontSize: 10, fontWeight: 700, letterSpacing: '.04em',
                      textTransform: 'uppercase', padding: '2px 7px', borderRadius: 99,
                      background: t.exit_reason === 'take_profit' ? 'rgba(34,197,94,0.12)'
                        : t.exit_reason === 'stop_loss' ? 'rgba(239,68,68,0.12)'
                        : 'rgba(148,163,184,0.08)',
                      color: t.exit_reason === 'take_profit' ? 'var(--green)'
                        : t.exit_reason === 'stop_loss' ? 'var(--red)'
                        : 'var(--text-4)',
                    }}>
                      {EXIT_LABELS[t.exit_reason] ?? t.exit_reason}
                    </span>
                  </td>
                  <td className="font-num" style={{ padding: '9px 12px', color: 'var(--text-4)', fontSize: 12 }}>
                    {t.signal_score ?? '—'}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {pages > 1 && (
        <div style={{ display: 'flex', justifyContent: 'center', gap: 8, marginTop: 16 }}>
          <button
            className="btn-secondary"
            onClick={() => setPage((p) => Math.max(0, p - 1))}
            disabled={page === 0}
            style={{ opacity: page === 0 ? 0.4 : 1 }}
          >
            ← Zurück
          </button>
          <span style={{ padding: '7px 12px', fontSize: 13, color: 'var(--text-3)' }}>
            {page + 1} / {pages}
          </span>
          <button
            className="btn-secondary"
            onClick={() => setPage((p) => Math.min(pages - 1, p + 1))}
            disabled={page === pages - 1}
            style={{ opacity: page === pages - 1 ? 0.4 : 1 }}
          >
            Weiter →
          </button>
        </div>
      )}
    </div>
  )
}

// ── Konfigurations-Formular ───────────────────────────────────────────────────

function ConfigForm({ onRun, isRunning }: {
  onRun: (cfg: BacktestConfig) => void
  isRunning: boolean
}) {
  const [symbol,  setSymbol]  = useState('NVDA')
  const [customSym, setCustom] = useState('')
  const [startDate, setStart]  = useState(oneYearAgoStr())
  const [endDate,   setEnd]    = useState(todayStr())
  const [capital,   setCapital] = useState(100_000)
  const [seed,      setSeed]    = useState(42)
  const [minScore,  setMinScore] = useState(65)

  const activeSym = customSym.toUpperCase() || symbol

  function handleSubmit() {
    if (!activeSym || !startDate || !endDate || capital <= 0) return
    onRun({
      symbol:          activeSym,
      start_date:      startDate,
      end_date:        endDate,
      initial_capital: capital,
      seed,
      min_score:       minScore,
    })
  }

  return (
    <div style={{
      display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
      gap: 14, alignItems: 'end',
    }}>
      {/* Symbol */}
      <div>
        <div className="label-caps" style={{ marginBottom: 8 }}>Symbol</div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5, marginBottom: 8 }}>
          {SYMBOLS.map((s) => (
            <button
              key={s}
              className={`filter-chip${symbol === s && !customSym ? ' active' : ''}`}
              onClick={() => { setSymbol(s); setCustom('') }}
              style={{ fontSize: 11 }}
            >
              {s}
            </button>
          ))}
        </div>
        <input
          type="text"
          placeholder="Eigenes Symbol…"
          value={customSym}
          onChange={(e) => setCustom(e.target.value.toUpperCase())}
          style={{ width: '100%', fontSize: 13 }}
        />
      </div>

      {/* Startdatum */}
      <div>
        <div className="label-caps" style={{ marginBottom: 8 }}>Von</div>
        <input
          type="date"
          value={startDate}
          max={endDate}
          onChange={(e) => setStart(e.target.value)}
          style={{ width: '100%', fontSize: 13, cursor: 'pointer' }}
        />
      </div>

      {/* Enddatum */}
      <div>
        <div className="label-caps" style={{ marginBottom: 8 }}>Bis</div>
        <input
          type="date"
          value={endDate}
          min={startDate}
          onChange={(e) => setEnd(e.target.value)}
          style={{ width: '100%', fontSize: 13, cursor: 'pointer' }}
        />
      </div>

      {/* Startkapital */}
      <div>
        <div className="label-caps" style={{ marginBottom: 8 }}>Startkapital CHF</div>
        <input
          type="number"
          value={capital}
          min={1000}
          step={10000}
          onChange={(e) => setCapital(Number(e.target.value))}
          style={{ width: '100%', fontSize: 13 }}
        />
      </div>

      {/* Min Score */}
      <div>
        <div className="label-caps" style={{ marginBottom: 8 }}>Min. Score ({minScore})</div>
        <input
          type="range" min={50} max={85} step={5}
          value={minScore}
          onChange={(e) => setMinScore(Number(e.target.value))}
          style={{ width: '100%', accentColor: 'var(--accent)', cursor: 'pointer' }}
        />
      </div>

      {/* Seed */}
      <div>
        <div className="label-caps" style={{ marginBottom: 8 }}>Seed (Reproduzierbarkeit)</div>
        <input
          type="number"
          value={seed}
          onChange={(e) => setSeed(Number(e.target.value))}
          style={{ width: '100%', fontSize: 13 }}
        />
      </div>

      {/* Submit */}
      <div style={{ paddingBottom: 2 }}>
        <button
          className="btn-primary"
          onClick={handleSubmit}
          disabled={isRunning}
          style={{ width: '100%', opacity: isRunning ? 0.7 : 1 }}
        >
          {isRunning ? (
            <>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"
                style={{ animation: 'spin 0.8s linear infinite' }}>
                <path d="M12 2a10 10 0 0 1 10 10"/>
              </svg>
              Läuft…
            </>
          ) : (
            <>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <polygon points="5 3 19 12 5 21 5 3"/>
              </svg>
              Backtest starten
            </>
          )}
        </button>
      </div>
    </div>
  )
}

// ── Hauptseite ────────────────────────────────────────────────────────────────

export default function BacktestPage() {
  const [backtestId, setBacktestId] = useState<string | null>(null)
  const [activeTab,  setActiveTab]  = useState<'metrics' | 'chart' | 'trades'>('metrics')

  const runMutation = useRunBacktest()
  const { data: result }  = useBacktestResult(backtestId)
  const { data: equityData } = useBacktestEquity(backtestId)

  async function handleRun(cfg: BacktestConfig) {
    setBacktestId(null)
    try {
      const res = await runMutation.mutateAsync(cfg)
      setBacktestId(res.backtest_id)
      setActiveTab('metrics')
    } catch {
      // error shown via isError below
    }
  }

  const isRunning = runMutation.isPending
  const hasError  = runMutation.isError
  const metrics   = result?.metrics ?? runMutation.data?.metrics

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 22 }}>

      {/* ── Konfiguration ── */}
      <div style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border-dim)',
        borderRadius: 12, padding: '20px 22px',
        boxShadow: 'var(--shadow-card)',
      }}>
        <div className="label-caps" style={{ marginBottom: 16 }}>Backtest Konfiguration</div>
        <ConfigForm onRun={handleRun} isRunning={isRunning} />
      </div>

      {/* ── Fehler ── */}
      {hasError && (
        <div style={{
          padding: '14px 18px', borderRadius: 10,
          background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.25)',
          color: 'var(--red)', fontSize: 13, fontWeight: 500,
        }}>
          Backtest-Fehler: Bitte Symbol und Zeitraum prüfen.
        </div>
      )}

      {/* ── Ergebnis-Header ── */}
      {metrics && (
        <div style={{
          display: 'flex', alignItems: 'center', gap: 20, flexWrap: 'wrap',
          padding: '16px 22px', borderRadius: 12,
          background: 'var(--bg-surface)', border: '1px solid var(--border-dim)',
          boxShadow: 'var(--shadow-card)',
        }}>
          <div>
            <div className="label-caps" style={{ marginBottom: 4 }}>Ergebnis</div>
            <div style={{ fontSize: 13, color: 'var(--text-3)' }}>
              {result?.config.symbol ?? runMutation.data?.symbol} ·{' '}
              {result?.config.start_date} → {result?.config.end_date}
            </div>
          </div>

          <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 12 }}>
            {(['metrics', 'chart', 'trades'] as const).map((tab) => (
              <button
                key={tab}
                className={`filter-chip${activeTab === tab ? ' active' : ''}`}
                onClick={() => setActiveTab(tab)}
              >
                {tab === 'metrics' ? 'Kennzahlen' : tab === 'chart' ? 'Equity-Kurve' : 'Trades'}
              </button>
            ))}
            {runMutation.data && (
              <span style={{ fontSize: 11, color: 'var(--text-4)', paddingLeft: 8 }}>
                {runMutation.data.duration_ms} ms
              </span>
            )}
          </div>
        </div>
      )}

      {/* ── Tabs ── */}
      {activeTab === 'metrics' && metrics && (
        <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-dim)', borderRadius: 12, padding: '20px 22px', boxShadow: 'var(--shadow-card)' }}>
          <div className="label-caps" style={{ marginBottom: 16 }}>Performance-Kennzahlen</div>
          <MetricGrid metrics={metrics} />
        </div>
      )}

      {activeTab === 'chart' && equityData && (
        <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-dim)', borderRadius: 12, padding: '20px 22px', boxShadow: 'var(--shadow-card)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
            <div className="label-caps">Equity-Kurve</div>
            <div style={{ display: 'flex', gap: 16 }}>
              <span style={{ fontSize: 12, color: 'var(--text-4)' }}>
                Start: <span className="font-num" style={{ color: 'var(--text-2)' }}>
                  CHF {fmtChf(equityData.initial_capital)}
                </span>
              </span>
              <span style={{ fontSize: 12, color: 'var(--text-4)' }}>
                Ende: <span className="font-num" style={{ color: equityData.final_equity >= equityData.initial_capital ? 'var(--green)' : 'var(--red)' }}>
                  CHF {fmtChf(equityData.final_equity)}
                </span>
              </span>
            </div>
          </div>
          <EquityChart data={equityData.equity_curve} initialCapital={equityData.initial_capital} />
        </div>
      )}

      {activeTab === 'trades' && result?.trades && (
        <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-dim)', borderRadius: 12, padding: '20px 22px', boxShadow: 'var(--shadow-card)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
            <div className="label-caps">Trade-Liste</div>
            <div style={{ display: 'flex', gap: 16, fontSize: 12, color: 'var(--text-4)' }}>
              <span>
                Gesamt: <span style={{ color: 'var(--text-2)', fontWeight: 600 }}>{result.trades.length}</span>
              </span>
              <span style={{ color: 'var(--green)' }}>
                ✓ {result.metrics.num_wins} Gewinne
              </span>
              <span style={{ color: 'var(--red)' }}>
                ✗ {result.metrics.num_losses} Verluste
              </span>
            </div>
          </div>
          <TradeTable trades={result.trades} />
        </div>
      )}

      {/* ── Leer-Zustand ── */}
      {!metrics && !isRunning && !hasError && (
        <div style={{
          display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16,
          padding: '60px 20px',
          background: 'var(--bg-surface)', border: '1px solid var(--border-dim)',
          borderRadius: 12, boxShadow: 'var(--shadow-card)',
        }}>
          <div style={{
            width: 56, height: 56, borderRadius: 14,
            background: 'var(--accent-dim)', border: '1px solid rgba(59,130,246,0.2)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" strokeWidth="2">
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
            </svg>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-1)', marginBottom: 6 }}>
              Backtest konfigurieren
            </div>
            <div style={{ fontSize: 13, color: 'var(--text-4)', maxWidth: 360 }}>
              Wähle Symbol, Zeitraum und Startkapital — dann klicke "Backtest starten".
              Die Simulation nutzt MockFeed-Preislogik mit reproduzierbarem Seed.
            </div>
          </div>
        </div>
      )}

    </div>
  )
}
