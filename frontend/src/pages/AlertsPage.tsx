import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useAlerts, useTriggeredAlerts, useCreateAlert, useDeleteAlert } from '../hooks/useApi'
import type { AlertConfig, AlertCreate, AlertCondition, AlertEvent } from '../api/types'
import { LoadingSpinner, EmptyState } from '../components/ui/LoadingSpinner'

const CONDITION_LABELS: Record<AlertCondition, string> = {
  price_above:        'Kurs steigt über',
  price_below:        'Kurs fällt unter',
  signal_score_above: 'Signal-Score über',
  signal_score_below: 'Signal-Score unter',
  regime_change:      'Regimewechsel',
}

const CONDITION_UNIT: Record<AlertCondition, string> = {
  price_above: 'CHF/USD', price_below: 'CHF/USD',
  signal_score_above: 'Punkte', signal_score_below: 'Punkte',
  regime_change: '',
}

const SYMBOLS = ['NVDA', 'MSFT', 'AAPL', 'NOVN', 'ZGLD', 'SPY']

const fmtDate = (iso: string) =>
  new Date(iso).toLocaleString('de-CH', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })

function AlertRow({ alert, onDelete }: { alert: AlertConfig; onDelete: () => void }) {
  const active = alert.active && !alert.triggered
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 16, padding: '14px 20px',
      borderBottom: '1px solid var(--border-dim)',
      background: alert.triggered ? 'rgba(245,158,11,0.04)' : 'transparent',
      transition: 'background var(--trans)',
    }}
      onMouseEnter={e => (e.currentTarget.style.background = alert.triggered ? 'rgba(245,158,11,0.07)' : 'var(--bg-hover)')}
      onMouseLeave={e => (e.currentTarget.style.background = alert.triggered ? 'rgba(245,158,11,0.04)' : 'transparent')}
    >
      {/* Status Dot */}
      <div style={{
        width: 8, height: 8, borderRadius: '50%', flexShrink: 0,
        background: alert.triggered ? 'var(--gold)' : active ? 'var(--green)' : 'var(--text-4)',
        boxShadow: alert.triggered ? '0 0 6px var(--gold)' : active ? '0 0 6px var(--green)' : 'none',
      }} />

      {/* Symbol */}
      <div style={{ fontWeight: 700, color: 'var(--text-1)', minWidth: 52 }}>{alert.symbol}</div>

      {/* Condition */}
      <div style={{ flex: 1, fontSize: 13, color: 'var(--text-2)' }}>
        {CONDITION_LABELS[alert.condition]}
        {alert.condition !== 'regime_change' && (
          <span className="font-num" style={{ fontWeight: 700, color: 'var(--text-1)', marginLeft: 6 }}>
            {alert.threshold} <span style={{ fontWeight: 400, color: 'var(--text-4)', fontSize: 11 }}>{CONDITION_UNIT[alert.condition]}</span>
          </span>
        )}
      </div>

      {/* Status Badge */}
      <span style={{
        fontSize: 11, fontWeight: 700, padding: '2px 9px', borderRadius: 5,
        background: alert.triggered ? 'rgba(245,158,11,0.15)' : active ? 'rgba(34,197,94,0.12)' : 'var(--bg-elevated)',
        color: alert.triggered ? 'var(--gold)' : active ? 'var(--green)' : 'var(--text-4)',
        letterSpacing: '0.05em', textTransform: 'uppercase',
      }}>
        {alert.triggered ? 'Ausgelöst' : active ? 'Aktiv' : 'Inaktiv'}
      </span>

      {/* Triggered info */}
      {alert.triggered && alert.triggered_at && (
        <div style={{ fontSize: 11, color: 'var(--text-4)', minWidth: 130, textAlign: 'right' }}>
          {fmtDate(alert.triggered_at)}
          {alert.triggered_value !== null && (
            <span className="font-num" style={{ display: 'block', color: 'var(--gold)', fontWeight: 600 }}>
              Wert: {alert.triggered_value?.toFixed(2)}
            </span>
          )}
        </div>
      )}

      {/* Delete */}
      <button
        onClick={onDelete}
        style={{
          background: 'none', border: '1px solid var(--border-std)', borderRadius: 6,
          cursor: 'pointer', color: 'var(--text-4)', padding: '4px 8px', fontSize: 12,
          transition: 'all var(--trans)', flexShrink: 0,
        }}
        onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--red)'; e.currentTarget.style.color = 'var(--red)' }}
        onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border-std)'; e.currentTarget.style.color = 'var(--text-4)' }}
      >
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/>
          <path d="M10 11v6M14 11v6"/><path d="M9 6V4h6v2"/>
        </svg>
      </button>
    </div>
  )
}

function EventRow({ event }: { event: AlertEvent }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 16, padding: '12px 20px',
      borderBottom: '1px solid var(--border-dim)',
    }}>
      <div style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--gold)', flexShrink: 0 }} />
      <div style={{ fontWeight: 700, minWidth: 52 }}>{event.symbol}</div>
      <div style={{ flex: 1, fontSize: 13, color: 'var(--text-2)' }}>{event.message}</div>
      <div style={{ fontSize: 11, color: 'var(--text-4)', textAlign: 'right', minWidth: 130 }}>
        {fmtDate(event.triggered_at)}
      </div>
    </div>
  )
}

function AlertForm({ onSuccess }: { onSuccess: () => void }) {
  const [form, setForm] = useState<AlertCreate>({
    symbol: 'NVDA', condition: 'price_above', threshold: 0, notes: '',
  })
  const [err, setErr] = useState('')
  const { mutate, isPending } = useCreateAlert()

  const set = <K extends keyof AlertCreate>(k: K, v: AlertCreate[K]) =>
    setForm(f => ({ ...f, [k]: v }))

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    setErr('')
    if (form.condition !== 'regime_change' && form.threshold <= 0)
      return setErr('Schwellenwert muss > 0 sein')

    mutate(form, {
      onSuccess: () => { onSuccess(); setForm({ symbol: 'NVDA', condition: 'price_above', threshold: 0, notes: '' }) },
      onError: () => setErr('Fehler beim Erstellen'),
    })
  }

  const inputStyle: React.CSSProperties = {
    background: 'var(--bg-input)', border: '1px solid var(--border-std)',
    borderRadius: 8, color: 'var(--text-1)', padding: '9px 12px',
    fontSize: 14, outline: 'none',
  }
  const labelStyle: React.CSSProperties = {
    fontSize: 11, fontWeight: 600, color: 'var(--text-4)',
    letterSpacing: '0.07em', textTransform: 'uppercase', marginBottom: 6, display: 'block',
  }
  const needsThreshold = form.condition !== 'regime_change'

  return (
    <form onSubmit={submit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <div>
          <label style={labelStyle}>Symbol</label>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            {SYMBOLS.map(s => (
              <button key={s} type="button"
                onClick={() => set('symbol', s)}
                style={{
                  padding: '5px 11px', borderRadius: 6, fontSize: 12, fontWeight: 600,
                  border: '1px solid', cursor: 'pointer', transition: 'all var(--trans)',
                  borderColor: form.symbol === s ? 'var(--accent)' : 'var(--border-std)',
                  background: form.symbol === s ? 'var(--accent-dim)' : 'var(--bg-elevated)',
                  color: form.symbol === s ? 'var(--accent)' : 'var(--text-3)',
                }}
              >{s}</button>
            ))}
          </div>
          <input
            type="text" placeholder="Anderes Symbol…" value={SYMBOLS.includes(form.symbol) ? '' : form.symbol}
            onChange={e => set('symbol', e.target.value.toUpperCase())}
            style={{ ...inputStyle, marginTop: 8, width: '100%', boxSizing: 'border-box' }}
          />
        </div>
        <div>
          <label style={labelStyle}>Bedingung</label>
          <select
            value={form.condition}
            onChange={e => set('condition', e.target.value as AlertCondition)}
            style={{ ...inputStyle, width: '100%', boxSizing: 'border-box', cursor: 'pointer' }}
          >
            {(Object.entries(CONDITION_LABELS) as [AlertCondition, string][]).map(([k, v]) => (
              <option key={k} value={k}>{v}</option>
            ))}
          </select>
        </div>
        {needsThreshold && (
          <div>
            <label style={labelStyle}>Schwellenwert ({CONDITION_UNIT[form.condition]})</label>
            <input
              type="number" min="0" step="0.01" value={form.threshold}
              onChange={e => set('threshold', parseFloat(e.target.value) || 0)}
              style={inputStyle} required
            />
          </div>
        )}
        <div>
          <label style={labelStyle}>Notiz</label>
          <input
            type="text" value={form.notes} placeholder="Optional…"
            onChange={e => set('notes', e.target.value)}
            style={{ ...inputStyle, width: '100%', boxSizing: 'border-box' }}
          />
        </div>
      </div>

      {err && <div style={{ padding: '8px 12px', borderRadius: 6, background: 'rgba(239,68,68,0.1)', color: 'var(--red)', fontSize: 13 }}>{err}</div>}
      <div>
        <button type="submit" className="btn-primary" disabled={isPending} style={{ opacity: isPending ? 0.7 : 1 }}>
          {isPending ? 'Wird erstellt…' : 'Alert erstellen'}
        </button>
      </div>
    </form>
  )
}

export default function AlertsPage() {
  const qc = useQueryClient()
  const { data: alerts = [], isLoading: loadAlerts } = useAlerts()
  const { data: history = [] } = useTriggeredAlerts()
  const { mutate: deleteMut } = useDeleteAlert()
  const [showForm, setShowForm] = useState(false)

  const inv = () => { qc.invalidateQueries({ queryKey: ['alerts'] }); qc.invalidateQueries({ queryKey: ['alerts', 'triggered'] }) }
  const handleDelete = (id: string) => deleteMut(id, { onSuccess: inv })

  const active    = alerts.filter(a => !a.triggered)
  const triggered = alerts.filter(a => a.triggered)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

      {/* ── Header Bar ── */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <div style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--green)', boxShadow: '0 0 6px var(--green)' }} />
            <span style={{ fontSize: 13, color: 'var(--text-3)' }}>{active.length} Aktiv</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <div style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--gold)' }} />
            <span style={{ fontSize: 13, color: 'var(--text-3)' }}>{triggered.length} Ausgelöst</span>
          </div>
        </div>
        <button
          className="btn-primary"
          onClick={() => setShowForm(f => !f)}
        >{showForm ? '× Schließen' : '+ Alert erstellen'}</button>
      </div>

      {/* ── Form ── */}
      {showForm && (
        <div className="card">
          <div className="label-caps" style={{ marginBottom: 16 }}>Neuer Alert</div>
          <AlertForm onSuccess={() => { inv(); setShowForm(false) }} />
        </div>
      )}

      {/* ── Active Alerts ── */}
      <div className="card" style={{ padding: 0 }}>
        <div style={{ padding: '20px 24px', borderBottom: '1px solid var(--border-std)', display: 'flex', justifyContent: 'space-between' }}>
          <div className="label-caps">Aktive Alerts</div>
          <span style={{ fontSize: 12, color: 'var(--text-4)' }}>{active.length} aktiv · {triggered.length} ausgelöst</span>
        </div>
        {loadAlerts ? <LoadingSpinner /> :
         !alerts.length ? <EmptyState message="Keine Alerts konfiguriert" /> : (
          [...active, ...triggered].map(a => (
            <AlertRow key={a.id} alert={a} onDelete={() => handleDelete(a.id)} />
          ))
        )}
      </div>

      {/* ── History ── */}
      {history.length > 0 && (
        <div className="card" style={{ padding: 0 }}>
          <div style={{ padding: '20px 24px', borderBottom: '1px solid var(--border-std)' }}>
            <div className="label-caps">Alert-Historie</div>
          </div>
          {history.map((e, i) => <EventRow key={i} event={e} />)}
        </div>
      )}
    </div>
  )
}
