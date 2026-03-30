import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useWatchlist, useAddToWatchlist, useRemoveFromWatchlist } from '../hooks/useApi'
import type { WatchlistItem } from '../api/types'
import { LoadingSpinner, EmptyState } from '../components/ui/LoadingSpinner'

const fmt  = (n: number, d = 2) => n.toLocaleString('de-CH', { minimumFractionDigits: d, maximumFractionDigits: d })
const pnlColor = (v: number) => v > 0 ? 'var(--green)' : v < 0 ? 'var(--red)' : 'var(--text-3)'

const SIGNAL_COLORS: Record<string, string> = {
  buy: 'var(--green)', sell: 'var(--red)', hold: 'var(--text-3)',
  avoid: 'var(--red)', add: 'var(--green)', reduce: 'var(--gold)',
}

const SUGGESTED = ['AAPL', 'MSFT', 'NVDA', 'SPY', 'TSLA', 'AMZN', 'GOOGL', 'META', 'TSM', 'NOVN', 'ZGLD']

function WatchlistRow({ item, onRemove }: { item: WatchlistItem; onRemove: () => void }) {
  return (
    <tr
      style={{ borderBottom: '1px solid var(--border-dim)', transition: 'background var(--trans)' }}
      onMouseEnter={e => (e.currentTarget.style.background = 'var(--bg-hover)')}
      onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
    >
      <td style={{ padding: '14px 16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 32, height: 32, borderRadius: 8,
            background: 'var(--accent-dim)', display: 'flex',
            alignItems: 'center', justifyContent: 'center',
            fontSize: 12, fontWeight: 700, color: 'var(--accent)',
          }}>{item.symbol.slice(0, 2)}</div>
          <div>
            <div style={{ fontWeight: 700, color: 'var(--text-1)', fontSize: 14 }}>{item.symbol}</div>
            <div style={{ fontSize: 11, color: 'var(--text-4)' }}>{item.name}</div>
          </div>
        </div>
      </td>
      <td style={{ padding: '14px 16px', textAlign: 'right' }} className="font-num">
        <div style={{ fontWeight: 600, fontSize: 15 }}>{item.current_price > 0 ? fmt(item.current_price) : '—'}</div>
      </td>
      <td style={{ padding: '14px 16px', textAlign: 'right' }}>
        {item.current_price > 0 && (
          <span style={{
            display: 'inline-block', padding: '2px 8px', borderRadius: 6,
            background: item.change_pct >= 0 ? 'rgba(34,197,94,0.12)' : 'rgba(239,68,68,0.12)',
            color: pnlColor(item.change_pct), fontWeight: 600, fontSize: 12,
          }} className="font-num">
            {item.change_pct >= 0 ? '+' : ''}{fmt(item.change_pct, 2)}%
          </span>
        )}
      </td>
      <td style={{ padding: '14px 16px', textAlign: 'right' }}>
        {item.target_price && (
          <span className="font-num" style={{ color: 'var(--gold)', fontSize: 13 }}>
            {fmt(item.target_price)}
          </span>
        )}
      </td>
      <td style={{ padding: '14px 16px', textAlign: 'right' }}>
        {item.signal_score !== null && item.signal_type ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, justifyContent: 'flex-end' }}>
            <span style={{
              padding: '3px 9px', borderRadius: 6, fontSize: 11, fontWeight: 700,
              background: `${SIGNAL_COLORS[item.signal_type] ?? 'var(--text-4)'}22`,
              color: SIGNAL_COLORS[item.signal_type] ?? 'var(--text-4)',
              textTransform: 'uppercase', letterSpacing: '0.05em',
            }}>{item.signal_type}</span>
            <span className="font-num" style={{ fontSize: 13, color: 'var(--text-3)' }}>
              {item.signal_score}
            </span>
          </div>
        ) : <span style={{ color: 'var(--text-4)', fontSize: 12 }}>—</span>}
      </td>
      <td style={{ padding: '14px 16px', textAlign: 'right' }}>
        <span style={{ fontSize: 11, color: 'var(--text-4)' }}>{item.data_source}</span>
      </td>
      <td style={{ padding: '14px 16px', textAlign: 'right' }}>
        <button
          onClick={onRemove}
          style={{
            background: 'none', border: '1px solid var(--border-std)', borderRadius: 6,
            cursor: 'pointer', color: 'var(--text-4)', padding: '4px 10px', fontSize: 12,
            transition: 'all var(--trans)',
          }}
          onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--red)'; e.currentTarget.style.color = 'var(--red)' }}
          onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border-std)'; e.currentTarget.style.color = 'var(--text-4)' }}
        >Entfernen</button>
      </td>
    </tr>
  )
}

export default function WatchlistPage() {
  const qc = useQueryClient()
  const { data: items = [], isLoading } = useWatchlist()
  const { mutate: addMut, isPending: adding } = useAddToWatchlist()
  const { mutate: removeMut } = useRemoveFromWatchlist()
  const [newSym, setNewSym] = useState('')
  const [targetPrice, setTargetPrice] = useState('')
  const [notes, setNotes] = useState('')
  const [err, setErr] = useState('')

  const invalidate = () => qc.invalidateQueries({ queryKey: ['watchlist'] })

  const handleAdd = () => {
    const sym = newSym.trim().toUpperCase()
    if (!sym) return setErr('Symbol eingeben')
    if (items.some(i => i.symbol === sym)) return setErr(`${sym} ist bereits in der Watchlist`)
    setErr('')
    addMut(
      { symbol: sym, target_price: targetPrice ? parseFloat(targetPrice) : undefined, notes },
      {
        onSuccess: () => { invalidate(); setNewSym(''); setTargetPrice(''); setNotes('') },
        onError: () => setErr('Fehler beim Hinzufügen'),
      }
    )
  }

  const handleRemove = (symbol: string) => {
    removeMut(symbol, { onSuccess: invalidate })
  }

  const inputStyle: React.CSSProperties = {
    background: 'var(--bg-input)', border: '1px solid var(--border-std)',
    borderRadius: 8, color: 'var(--text-1)', padding: '9px 12px',
    fontSize: 14, outline: 'none',
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

      {/* ── Add Symbol ── */}
      <div className="card">
        <div className="label-caps" style={{ marginBottom: 16 }}>Symbol hinzufügen</div>

        {/* Quick-Add Chips */}
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 14 }}>
          {SUGGESTED.filter(s => !items.some(i => i.symbol === s)).map(s => (
            <button
              key={s}
              onClick={() => setNewSym(s)}
              style={{
                padding: '4px 11px', borderRadius: 6, border: '1px solid var(--border-std)',
                background: newSym === s ? 'var(--accent-dim)' : 'var(--bg-elevated)',
                color: newSym === s ? 'var(--accent)' : 'var(--text-3)',
                fontSize: 12, fontWeight: 600, cursor: 'pointer', transition: 'all var(--trans)',
              }}
            >{s}</button>
          ))}
        </div>

        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'flex-end' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <label style={{ fontSize: 11, color: 'var(--text-4)', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase' }}>Symbol</label>
            <input
              value={newSym} placeholder="z.B. TSLA"
              onChange={e => { setNewSym(e.target.value.toUpperCase()); setErr('') }}
              style={{ ...inputStyle, width: 120 }}
              onKeyDown={e => e.key === 'Enter' && handleAdd()}
            />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <label style={{ fontSize: 11, color: 'var(--text-4)', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase' }}>Kursziel (optional)</label>
            <input
              type="number" value={targetPrice} placeholder="z.B. 250"
              onChange={e => setTargetPrice(e.target.value)}
              style={{ ...inputStyle, width: 140 }}
            />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4, flex: 1, minWidth: 160 }}>
            <label style={{ fontSize: 11, color: 'var(--text-4)', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase' }}>Notiz</label>
            <input
              value={notes} placeholder="Optional…"
              onChange={e => setNotes(e.target.value)}
              style={{ ...inputStyle, width: '100%' }}
            />
          </div>
          <button
            className="btn-primary" onClick={handleAdd}
            disabled={adding || !newSym}
            style={{ opacity: adding || !newSym ? 0.6 : 1 }}
          >
            {adding ? '…' : '+ Hinzufügen'}
          </button>
        </div>
        {err && <div style={{ marginTop: 8, fontSize: 12, color: 'var(--red)' }}>{err}</div>}
      </div>

      {/* ── Watchlist Table ── */}
      <div className="card" style={{ padding: 0 }}>
        <div style={{ padding: '20px 24px 0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div className="label-caps">Watchlist</div>
          <span style={{ fontSize: 12, color: 'var(--text-4)' }}>{items.length} Symbole</span>
        </div>

        {isLoading ? <LoadingSpinner message="Lade Watchlist…" /> :
         !items.length ? <EmptyState message="Watchlist leer — Symbol oben hinzufügen" /> : (
          <div style={{ overflowX: 'auto', paddingBottom: 8 }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-std)' }}>
                  {['Symbol', 'Kurs', 'Änderung', 'Kursziel', 'Signal', 'Quelle', ''].map(h => (
                    <th key={h} style={{
                      padding: '10px 16px', textAlign: 'right', fontSize: 11,
                      fontWeight: 600, color: 'var(--text-4)', letterSpacing: '0.06em',
                      textTransform: 'uppercase',
                    }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {items.map(item => (
                  <WatchlistRow
                    key={item.symbol} item={item}
                    onRemove={() => handleRemove(item.symbol)}
                  />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
