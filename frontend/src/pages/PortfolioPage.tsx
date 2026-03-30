import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { usePortfolioSummary, useCreateTrade, useDeleteTrade } from '../hooks/useApi'
import type { PortfolioPosition, PortfolioTrade, PortfolioTradeCreate } from '../api/types'

// ── Helpers ───────────────────────────────────────────────────────────────────

const fmt = (n: number, dec = 2) =>
  n.toLocaleString('de-CH', { minimumFractionDigits: dec, maximumFractionDigits: dec })

const fmtDate = (iso: string) =>
  new Date(iso).toLocaleDateString('de-CH', { day: '2-digit', month: '2-digit', year: 'numeric' })

const pnlColor = (v: number) =>
  v > 0 ? 'var(--green)' : v < 0 ? 'var(--red)' : 'var(--text-3)'

// ── Stat Tile ─────────────────────────────────────────────────────────────────

function Tile({ label, value, sub, color }: { label: string; value: string; sub?: string; color?: string }) {
  return (
    <div className="stat-tile">
      <div className="label-caps" style={{ marginBottom: 8 }}>{label}</div>
      <div className="font-num" style={{ fontSize: 26, fontWeight: 700, color: color ?? 'var(--text-1)' }}>
        {value}
      </div>
      {sub && <div style={{ fontSize: 12, color: 'var(--text-4)', marginTop: 4 }}>{sub}</div>}
    </div>
  )
}

// ── Positions Table ───────────────────────────────────────────────────────────

function PositionsTable({ positions }: { positions: PortfolioPosition[] }) {
  if (!positions.length) return (
    <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--text-4)' }}>
      Keine offenen Positionen
    </div>
  )

  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{ borderBottom: '1px solid var(--border-std)' }}>
            {['Symbol', 'Name', 'Menge', 'Ø Einstieg', 'Aktuell', 'Wert CHF', 'Unreal. PnL', 'PnL %', 'Gewicht'].map(h => (
              <th key={h} style={{
                padding: '8px 12px', textAlign: 'right', fontSize: 11,
                fontWeight: 600, color: 'var(--text-4)', letterSpacing: '0.06em',
                textTransform: 'uppercase',
              }}
                className={h === 'Symbol' || h === 'Name' ? undefined : undefined}
              >{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {positions.map((p) => (
            <tr
              key={p.symbol}
              style={{ borderBottom: '1px solid var(--border-dim)', transition: 'background var(--trans)' }}
              onMouseEnter={e => (e.currentTarget.style.background = 'var(--bg-hover)')}
              onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
            >
              <td style={{ padding: '12px 12px', fontWeight: 700, color: 'var(--text-1)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <div style={{
                    width: 28, height: 28, borderRadius: 6,
                    background: 'var(--accent-dim)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: 11, fontWeight: 700, color: 'var(--accent)',
                  }}>
                    {p.symbol.slice(0, 2)}
                  </div>
                  {p.symbol}
                </div>
              </td>
              <td style={{ padding: '12px 12px', color: 'var(--text-3)', fontSize: 13 }}>{p.name}</td>
              <td style={{ padding: '12px 12px', textAlign: 'right' }} className="font-num">{fmt(p.quantity, 0)}</td>
              <td style={{ padding: '12px 12px', textAlign: 'right' }} className="font-num">
                {fmt(p.avg_entry_price, 2)} {p.currency}
              </td>
              <td style={{ padding: '12px 12px', textAlign: 'right' }} className="font-num">
                {fmt(p.current_price, 2)} {p.currency}
              </td>
              <td style={{ padding: '12px 12px', textAlign: 'right', fontWeight: 600 }} className="font-num">
                {fmt(p.value_chf)} CHF
              </td>
              <td style={{ padding: '12px 12px', textAlign: 'right', color: pnlColor(p.unrealized_pnl), fontWeight: 600 }} className="font-num">
                {p.unrealized_pnl >= 0 ? '+' : ''}{fmt(p.unrealized_pnl)} CHF
              </td>
              <td style={{ padding: '12px 12px', textAlign: 'right' }}>
                <span style={{
                  display: 'inline-block',
                  padding: '2px 8px', borderRadius: 6,
                  background: p.unrealized_pnl_pct >= 0 ? 'rgba(34,197,94,0.12)' : 'rgba(239,68,68,0.12)',
                  color: pnlColor(p.unrealized_pnl_pct),
                  fontWeight: 600, fontSize: 12,
                }} className="font-num">
                  {p.unrealized_pnl_pct >= 0 ? '+' : ''}{fmt(p.unrealized_pnl_pct, 2)}%
                </span>
              </td>
              <td style={{ padding: '12px 12px', textAlign: 'right', color: 'var(--text-3)' }} className="font-num">
                {fmt(p.weight_pct, 1)}%
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// ── Trade History ─────────────────────────────────────────────────────────────

function TradeHistory({ trades, onDelete }: { trades: PortfolioTrade[]; onDelete: (id: string) => void }) {
  const [page, setPage] = useState(0)
  const PAGE = 15
  const total = Math.ceil(trades.length / PAGE)
  const visible = trades.slice(page * PAGE, page * PAGE + PAGE)

  if (!trades.length) return (
    <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--text-4)' }}>
      Noch keine Trades erfasst
    </div>
  )

  return (
    <div>
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border-std)' }}>
              {['Datum', 'Symbol', 'Aktion', 'Menge', 'Preis', 'Währung', 'Gebühren', 'Wert CHF', 'Notiz', ''].map(h => (
                <th key={h} style={{
                  padding: '8px 12px', textAlign: 'right', fontSize: 11,
                  fontWeight: 600, color: 'var(--text-4)', letterSpacing: '0.06em',
                  textTransform: 'uppercase',
                }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {visible.map((t) => (
              <tr
                key={t.id}
                style={{
                  borderBottom: '1px solid var(--border-dim)',
                  background: t.action === 'buy' ? 'rgba(34,197,94,0.03)' : 'rgba(239,68,68,0.03)',
                  transition: 'background var(--trans)',
                }}
                onMouseEnter={e => (e.currentTarget.style.background = 'var(--bg-hover)')}
                onMouseLeave={e => (e.currentTarget.style.background = t.action === 'buy' ? 'rgba(34,197,94,0.03)' : 'rgba(239,68,68,0.03)')}
              >
                <td style={{ padding: '10px 12px', color: 'var(--text-3)', fontSize: 12 }}>
                  {fmtDate(t.timestamp)}
                </td>
                <td style={{ padding: '10px 12px', fontWeight: 700, color: 'var(--text-1)' }}>{t.symbol}</td>
                <td style={{ padding: '10px 12px' }}>
                  <span style={{
                    display: 'inline-block', padding: '2px 8px', borderRadius: 5,
                    background: t.action === 'buy' ? 'rgba(34,197,94,0.15)' : 'rgba(239,68,68,0.15)',
                    color: t.action === 'buy' ? 'var(--green)' : 'var(--red)',
                    fontSize: 11, fontWeight: 700, letterSpacing: '0.05em', textTransform: 'uppercase',
                  }}>
                    {t.action === 'buy' ? 'Kauf' : 'Verkauf'}
                  </span>
                </td>
                <td style={{ padding: '10px 12px', textAlign: 'right' }} className="font-num">{fmt(t.quantity, 2)}</td>
                <td style={{ padding: '10px 12px', textAlign: 'right' }} className="font-num">{fmt(t.price, 2)}</td>
                <td style={{ padding: '10px 12px', textAlign: 'right', color: 'var(--text-3)', fontSize: 12 }}>{t.currency}</td>
                <td style={{ padding: '10px 12px', textAlign: 'right', color: 'var(--text-4)' }} className="font-num">
                  {fmt(t.fees, 2)}
                </td>
                <td style={{ padding: '10px 12px', textAlign: 'right', fontWeight: 600 }} className="font-num">
                  {fmt(t.value_chf, 2)}
                </td>
                <td style={{ padding: '10px 12px', color: 'var(--text-4)', fontSize: 12, maxWidth: 160,
                  overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {t.notes || '—'}
                </td>
                <td style={{ padding: '10px 12px', textAlign: 'right' }}>
                  <button
                    onClick={() => onDelete(t.id)}
                    style={{
                      background: 'none', border: 'none', cursor: 'pointer',
                      color: 'var(--text-4)', padding: '4px 6px', borderRadius: 4,
                      transition: 'color var(--trans)',
                    }}
                    onMouseEnter={e => (e.currentTarget.style.color = 'var(--red)')}
                    onMouseLeave={e => (e.currentTarget.style.color = 'var(--text-4)')}
                    title="Trade löschen"
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polyline points="3 6 5 6 21 6"/>
                      <path d="M19 6l-1 14H6L5 6"/>
                      <path d="M10 11v6M14 11v6"/>
                      <path d="M9 6V4h6v2"/>
                    </svg>
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {total > 1 && (
        <div style={{ display: 'flex', justifyContent: 'center', gap: 8, marginTop: 16 }}>
          <button
            className="btn-secondary" onClick={() => setPage(p => Math.max(0, p - 1))}
            disabled={page === 0} style={{ opacity: page === 0 ? 0.4 : 1 }}
          >← Vorher</button>
          <span style={{ display: 'flex', alignItems: 'center', fontSize: 13, color: 'var(--text-3)' }}>
            {page + 1} / {total}
          </span>
          <button
            className="btn-secondary" onClick={() => setPage(p => Math.min(total - 1, p + 1))}
            disabled={page >= total - 1} style={{ opacity: page >= total - 1 ? 0.4 : 1 }}
          >Weiter →</button>
        </div>
      )}
    </div>
  )
}

// ── Trade Form ────────────────────────────────────────────────────────────────

const SYMBOLS = ['NVDA', 'MSFT', 'AAPL', 'NOVN', 'ZGLD', 'SPY']

function TradeForm({ onSuccess }: { onSuccess: () => void }) {
  const [form, setForm] = useState<PortfolioTradeCreate>({
    symbol: 'NVDA', action: 'buy', quantity: 1, price: 0,
    fees: 0, currency: 'USD', notes: '',
  })
  const [customSym, setCustomSym] = useState('')
  const [error, setError] = useState('')
  const { mutate, isPending } = useCreateTrade()

  const set = (k: keyof PortfolioTradeCreate, v: unknown) =>
    setForm(f => ({ ...f, [k]: v }))

  const activeSymbol = customSym.trim().toUpperCase() || form.symbol

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    if (!activeSymbol) return setError('Symbol erforderlich')
    if (form.quantity <= 0) return setError('Menge muss > 0 sein')
    if (form.price <= 0) return setError('Preis muss > 0 sein')

    mutate(
      { ...form, symbol: activeSymbol },
      {
        onSuccess: () => {
          onSuccess()
          setForm({ symbol: 'NVDA', action: 'buy', quantity: 1, price: 0, fees: 0, currency: 'USD', notes: '' })
          setCustomSym('')
        },
        onError: (err: unknown) => {
          const msg = err instanceof Error ? err.message : 'Fehler beim Speichern'
          setError(msg)
        },
      }
    )
  }

  const inputStyle: React.CSSProperties = {
    background: 'var(--bg-input)', border: '1px solid var(--border-std)',
    borderRadius: 8, color: 'var(--text-1)', padding: '9px 12px',
    fontSize: 14, width: '100%', outline: 'none', boxSizing: 'border-box',
  }
  const labelStyle: React.CSSProperties = {
    fontSize: 11, fontWeight: 600, color: 'var(--text-4)',
    letterSpacing: '0.07em', textTransform: 'uppercase', marginBottom: 6, display: 'block',
  }

  return (
    <form onSubmit={submit} style={{ maxWidth: 640 }}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>

        {/* Symbol */}
        <div style={{ gridColumn: '1 / -1' }}>
          <label style={labelStyle}>Symbol</label>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 8 }}>
            {SYMBOLS.map(s => (
              <button
                key={s} type="button"
                onClick={() => { set('symbol', s); setCustomSym('') }}
                style={{
                  padding: '5px 12px', borderRadius: 6, fontSize: 13, fontWeight: 600,
                  border: '1px solid',
                  borderColor: activeSymbol === s && !customSym ? 'var(--accent)' : 'var(--border-std)',
                  background: activeSymbol === s && !customSym ? 'var(--accent-dim)' : 'var(--bg-elevated)',
                  color: activeSymbol === s && !customSym ? 'var(--accent)' : 'var(--text-3)',
                  cursor: 'pointer', transition: 'all var(--trans)',
                }}
              >{s}</button>
            ))}
          </div>
          <input
            type="text" placeholder="Anderes Symbol eingeben…" value={customSym}
            onChange={e => setCustomSym(e.target.value.toUpperCase())}
            style={{ ...inputStyle, width: '100%' }}
          />
        </div>

        {/* Aktion */}
        <div>
          <label style={labelStyle}>Aktion</label>
          <div style={{ display: 'flex', gap: 0, borderRadius: 8, overflow: 'hidden', border: '1px solid var(--border-std)' }}>
            {(['buy', 'sell'] as const).map(a => (
              <button
                key={a} type="button"
                onClick={() => set('action', a)}
                style={{
                  flex: 1, padding: '9px 0', border: 'none', cursor: 'pointer',
                  fontSize: 13, fontWeight: 700, transition: 'all var(--trans)',
                  background: form.action === a
                    ? (a === 'buy' ? 'rgba(34,197,94,0.2)' : 'rgba(239,68,68,0.2)')
                    : 'var(--bg-elevated)',
                  color: form.action === a
                    ? (a === 'buy' ? 'var(--green)' : 'var(--red)')
                    : 'var(--text-4)',
                }}
              >
                {a === 'buy' ? 'Kaufen' : 'Verkaufen'}
              </button>
            ))}
          </div>
        </div>

        {/* Währung */}
        <div>
          <label style={labelStyle}>Währung</label>
          <div style={{ display: 'flex', gap: 0, borderRadius: 8, overflow: 'hidden', border: '1px solid var(--border-std)' }}>
            {['USD', 'CHF'].map(c => (
              <button
                key={c} type="button"
                onClick={() => set('currency', c)}
                style={{
                  flex: 1, padding: '9px 0', border: 'none', cursor: 'pointer',
                  fontSize: 13, fontWeight: 600, transition: 'all var(--trans)',
                  background: form.currency === c ? 'var(--accent-dim)' : 'var(--bg-elevated)',
                  color: form.currency === c ? 'var(--accent)' : 'var(--text-4)',
                }}
              >{c}</button>
            ))}
          </div>
        </div>

        {/* Menge */}
        <div>
          <label style={labelStyle}>Menge (Stück)</label>
          <input
            type="number" min="0.0001" step="0.0001" value={form.quantity}
            onChange={e => set('quantity', parseFloat(e.target.value) || 0)}
            style={inputStyle} required
          />
        </div>

        {/* Preis */}
        <div>
          <label style={labelStyle}>Preis ({form.currency})</label>
          <input
            type="number" min="0.0001" step="0.01" value={form.price}
            onChange={e => set('price', parseFloat(e.target.value) || 0)}
            style={inputStyle} required
          />
        </div>

        {/* Gebühren */}
        <div>
          <label style={labelStyle}>Gebühren (CHF)</label>
          <input
            type="number" min="0" step="0.01" value={form.fees}
            onChange={e => set('fees', parseFloat(e.target.value) || 0)}
            style={inputStyle}
          />
        </div>

        {/* Datum */}
        <div>
          <label style={labelStyle}>Datum (optional)</label>
          <input
            type="date"
            onChange={e => set('timestamp', e.target.value ? new Date(e.target.value).toISOString() : undefined)}
            style={inputStyle}
          />
        </div>

        {/* Notiz */}
        <div style={{ gridColumn: '1 / -1' }}>
          <label style={labelStyle}>Notiz</label>
          <input
            type="text" placeholder="Optional: Begründung, Strategie…" value={form.notes}
            onChange={e => set('notes', e.target.value)}
            style={inputStyle}
          />
        </div>
      </div>

      {/* Vorschau */}
      {form.price > 0 && form.quantity > 0 && (
        <div style={{
          marginTop: 16, padding: '12px 16px', borderRadius: 8,
          background: 'var(--bg-elevated)', border: '1px solid var(--border-std)',
          display: 'flex', gap: 24, flexWrap: 'wrap',
        }}>
          <div>
            <div style={labelStyle}>Transaktionswert</div>
            <div className="font-num" style={{ fontWeight: 700, color: 'var(--text-1)' }}>
              {(form.quantity * form.price).toLocaleString('de-CH', { maximumFractionDigits: 2 })} {form.currency}
            </div>
          </div>
          <div>
            <div style={labelStyle}>Stempelsteuer (0.075%)</div>
            <div className="font-num" style={{ color: 'var(--text-3)' }}>
              {(form.quantity * form.price * 0.00075).toLocaleString('de-CH', { maximumFractionDigits: 2 })} {form.currency}
            </div>
          </div>
        </div>
      )}

      {error && (
        <div style={{
          marginTop: 12, padding: '10px 14px', borderRadius: 8,
          background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)',
          color: 'var(--red)', fontSize: 13,
        }}>{error}</div>
      )}

      <div style={{ marginTop: 20, display: 'flex', gap: 10 }}>
        <button
          type="submit" className="btn-primary" disabled={isPending}
          style={{ opacity: isPending ? 0.7 : 1 }}
        >
          {isPending ? 'Wird gespeichert…' : form.action === 'buy' ? 'Kauf erfassen' : 'Verkauf erfassen'}
        </button>
        <button
          type="button" className="btn-secondary"
          onClick={() => { setForm({ symbol: 'NVDA', action: 'buy', quantity: 1, price: 0, fees: 0, currency: 'USD', notes: '' }); setCustomSym(''); setError('') }}
        >
          Zurücksetzen
        </button>
      </div>
    </form>
  )
}

// ── Main Page ─────────────────────────────────────────────────────────────────

type Tab = 'positions' | 'form' | 'history'

export default function PortfolioPage() {
  const [tab, setTab] = useState<Tab>('positions')
  const queryClient = useQueryClient()
  const { data: summary, isLoading, isError } = usePortfolioSummary()
  const { mutate: deleteTrade } = useDeleteTrade()

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['portfolio', 'summary'] })

  const handleDelete = (id: string) => {
    if (!confirm('Trade wirklich löschen?')) return
    deleteTrade(id, { onSuccess: invalidate })
  }

  const TAB_LABELS: { key: Tab; label: string; count?: number }[] = [
    { key: 'positions', label: 'Positionen', count: summary?.num_open_pos },
    { key: 'form',     label: 'Trade erfassen' },
    { key: 'history',  label: 'Trade-Historie', count: summary?.num_trades },
  ]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

      {/* ── Stat Tiles ── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
        <Tile
          label="Gesamtwert"
          value={summary ? `${fmt(summary.total_value_chf)} CHF` : '—'}
          sub={summary ? `Start: ${fmt(summary.starting_capital_chf)} CHF` : undefined}
        />
        <Tile
          label="Investiert"
          value={summary ? `${fmt(summary.positions_value_chf)} CHF` : '—'}
          sub={summary ? `Einstand: ${fmt(summary.invested_chf)} CHF` : undefined}
        />
        <Tile
          label="Cash"
          value={summary ? `${fmt(summary.cash_chf)} CHF` : '—'}
          sub={summary ? `${summary.cash_chf >= 0 ? 'Verfügbar' : 'Überzogen'}` : undefined}
          color={summary && summary.cash_chf < 0 ? 'var(--red)' : undefined}
        />
        <Tile
          label="Gesamt-PnL"
          value={summary ? `${summary.total_pnl_chf >= 0 ? '+' : ''}${fmt(summary.total_pnl_chf)} CHF` : '—'}
          sub={summary ? `${summary.total_pnl_pct >= 0 ? '+' : ''}${fmt(summary.total_pnl_pct, 2)}% seit Start` : undefined}
          color={summary ? pnlColor(summary.total_pnl_chf) : undefined}
        />
      </div>

      {/* ── PnL Detail Bar ── */}
      {summary && (
        <div style={{
          display: 'flex', gap: 24, padding: '14px 20px',
          background: 'var(--bg-surface)', borderRadius: 12,
          border: '1px solid var(--border-std)',
          flexWrap: 'wrap',
        }}>
          {[
            { label: 'Unrealisiert', value: summary.unrealized_pnl_chf },
            { label: 'Realisiert',   value: summary.realized_pnl_chf },
            { label: 'Heute',        value: summary.today_pnl_chf },
          ].map(({ label, value }) => (
            <div key={label}>
              <div className="label-caps" style={{ marginBottom: 4 }}>{label}</div>
              <div className="font-num" style={{ fontWeight: 700, color: pnlColor(value), fontSize: 16 }}>
                {value >= 0 ? '+' : ''}{fmt(value)} CHF
              </div>
            </div>
          ))}
          <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center' }}>
            <div className="label-caps" style={{ color: 'var(--text-4)', fontSize: 11 }}>
              {summary.num_open_pos} Positionen · {summary.num_trades} Trades
            </div>
          </div>
        </div>
      )}

      {/* ── Card with Tabs ── */}
      <div className="card" style={{ padding: 0 }}>
        {/* Tab Bar */}
        <div style={{
          display: 'flex', gap: 0, borderBottom: '1px solid var(--border-std)',
          padding: '0 24px',
        }}>
          {TAB_LABELS.map(({ key, label, count }) => (
            <button
              key={key}
              onClick={() => setTab(key)}
              style={{
                padding: '14px 20px', border: 'none', cursor: 'pointer',
                background: 'none', fontSize: 13, fontWeight: tab === key ? 700 : 500,
                color: tab === key ? 'var(--accent)' : 'var(--text-3)',
                borderBottom: tab === key ? '2px solid var(--accent)' : '2px solid transparent',
                marginBottom: -1, transition: 'all var(--trans)',
                display: 'flex', alignItems: 'center', gap: 8,
              }}
            >
              {label}
              {count !== undefined && (
                <span style={{
                  fontSize: 11, fontWeight: 700,
                  background: tab === key ? 'var(--accent-dim)' : 'var(--bg-elevated)',
                  color: tab === key ? 'var(--accent)' : 'var(--text-4)',
                  padding: '1px 6px', borderRadius: 10,
                }}>{count}</span>
              )}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div style={{ padding: 24 }}>
          {isLoading && (
            <div style={{ textAlign: 'center', padding: '40px 0' }}>
              <div className="skeleton" style={{ height: 200, borderRadius: 8 }} />
            </div>
          )}

          {isError && (
            <div style={{
              textAlign: 'center', padding: '32px', color: 'var(--red)',
              background: 'rgba(239,68,68,0.08)', borderRadius: 8,
            }}>
              Fehler beim Laden der Portfolio-Daten
            </div>
          )}

          {!isLoading && !isError && summary && (
            <>
              {tab === 'positions' && (
                <PositionsTable positions={summary.positions} />
              )}
              {tab === 'form' && (
                <TradeForm onSuccess={() => { invalidate(); setTab('history') }} />
              )}
              {tab === 'history' && (
                <TradeHistory trades={summary.trades} onDelete={handleDelete} />
              )}
            </>
          )}
        </div>
      </div>

    </div>
  )
}
