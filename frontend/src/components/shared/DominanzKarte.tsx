/**
 * DominanzKarte — zeigt die aktuell dominante Marktebene,
 * Stärke als Balken, Trend (gaining/losing) und die Narrative-Erklärung.
 *
 * DominanzKarteConnected verwaltet zusätzlich:
 *  - 10s Timeout → "Dominanz nicht verfügbar" mit grauem Icon
 *  - API-Fehler (HTTP + backend error-Feld) → roter Hinweistext mit Grund
 *  - "↺ Neu laden" Button in beiden Fehlerzuständen
 */
import { useState, useEffect } from 'react'
import { useDominance } from '../../hooks/useApi'
import type { DominanceState } from '../../api/types'

const LAYER_META: Record<string, { label: string; color: string; icon: string }> = {
  fundamental:    { label: 'Fundamentaldaten', color: 'var(--accent)',  icon: '◆' },
  geopolitical:   { label: 'Geopolitik/Makro', color: 'var(--red)',    icon: '⚑' },
  liquidity:      { label: 'Liquidität',        color: 'var(--amber)',  icon: '◎' },
  psychology:     { label: 'Psychologie',       color: '#a78bfa',       icon: '◉' },
  microstructure: { label: 'Mikrostruktur',     color: 'var(--green)',  icon: '◈' },
  narrative:      { label: 'Narrativ',          color: '#f472b6',       icon: '◬' },
}

// ── Hilfs-Komponenten ─────────────────────────────────────────────────────────

function StrengthBar({ value, color }: { value: number; color: string }) {
  return (
    <div style={{ flex: 1, height: 5, background: 'var(--bg-elevated)', borderRadius: 3, overflow: 'hidden' }}>
      <div style={{
        height: '100%',
        width: `${Math.round(value * 100)}%`,
        background: color,
        borderRadius: 3,
        transition: 'width 0.6s ease',
      }} />
    </div>
  )
}

function ReloadButton({ onClick }: { onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      style={{
        display: 'inline-flex', alignItems: 'center', gap: 5,
        padding: '5px 12px', borderRadius: 6, cursor: 'pointer',
        fontSize: 12, fontWeight: 600,
        background: 'var(--bg-elevated)',
        color: 'var(--text-2)',
        border: '1px solid var(--border-std)',
        transition: 'background 0.15s, border-color 0.15s',
      }}
      onMouseEnter={e => {
        (e.currentTarget as HTMLButtonElement).style.background = 'var(--bg-hover)'
        ;(e.currentTarget as HTMLButtonElement).style.borderColor = 'var(--border-bold)'
      }}
      onMouseLeave={e => {
        (e.currentTarget as HTMLButtonElement).style.background = 'var(--bg-elevated)'
        ;(e.currentTarget as HTMLButtonElement).style.borderColor = 'var(--border-std)'
      }}
    >
      ↺ Neu laden
    </button>
  )
}

// ── Haupt-Karte (rein presentational) ────────────────────────────────────────

export function DominanzKarte({ data }: { data: DominanceState }) {
  const dom      = LAYER_META[data.dominant_layer] ?? { label: data.dominant_label, color: 'var(--accent)', icon: '●' }
  const strength = data.dominance_strength

  const strengthWord  = strength > 0.7 ? 'STARK' : strength > 0.45 ? 'MODERAT' : 'SCHWACH'
  const strengthColor = strength > 0.7 ? 'var(--red)' : strength > 0.45 ? 'var(--amber)' : 'var(--green)'

  const layers = Object.entries(data.layer_scores).sort(([, a], [, b]) => b - a)

  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div className="label-caps">Dominanz-Analyse</div>
        <div style={{
          fontSize: 11, fontWeight: 700, letterSpacing: '0.07em',
          padding: '3px 8px', borderRadius: 5,
          background: `${strengthColor}20`,
          color: strengthColor,
          border: `1px solid ${strengthColor}40`,
        }}>{strengthWord}</div>
      </div>

      {/* Dominant Layer Hero */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 14,
        padding: '14px 16px', borderRadius: 10,
        background: `${dom.color}12`,
        border: `1px solid ${dom.color}30`,
      }}>
        <div style={{
          width: 44, height: 44, borderRadius: 10,
          background: `${dom.color}20`,
          border: `1px solid ${dom.color}40`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 20, color: dom.color, flexShrink: 0,
        }}>{dom.icon}</div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: 16, fontWeight: 800, color: dom.color }}>{dom.label}</div>
          <div style={{ fontSize: 12, color: 'var(--text-4)', marginTop: 3 }}>
            Dominant · {Math.round(strength * 100)}% Stärke
          </div>
        </div>
        {/* Trend Badges */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4, alignItems: 'flex-end' }}>
          {data.gaining_layers.slice(0, 2).map(l => {
            const meta = LAYER_META[l]
            return (
              <div key={l} style={{
                fontSize: 10, fontWeight: 600,
                padding: '2px 7px', borderRadius: 4,
                background: 'rgba(34,197,94,0.12)',
                color: 'var(--green)',
                border: '1px solid rgba(34,197,94,0.25)',
              }}>
                ↑ {meta?.label ?? l}
              </div>
            )
          })}
          {data.losing_layers.slice(0, 2).map(l => {
            const meta = LAYER_META[l]
            return (
              <div key={l} style={{
                fontSize: 10, fontWeight: 600,
                padding: '2px 7px', borderRadius: 4,
                background: 'rgba(239,68,68,0.12)',
                color: 'var(--red)',
                border: '1px solid rgba(239,68,68,0.25)',
              }}>
                ↓ {meta?.label ?? l}
              </div>
            )
          })}
        </div>
      </div>

      {/* Layer Scores */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {layers.map(([layer, score]) => {
          const meta      = LAYER_META[layer] ?? { label: layer, color: 'var(--text-3)', icon: '●' }
          const isGaining = data.gaining_layers.includes(layer)
          const isLosing  = data.losing_layers.includes(layer)
          const isDom     = layer === data.dominant_layer
          return (
            <div key={layer} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <span style={{ fontSize: 12, color: meta.color, width: 16, textAlign: 'center', flexShrink: 0 }}>
                {meta.icon}
              </span>
              <span style={{
                fontSize: 12, width: 130, flexShrink: 0,
                fontWeight: isDom ? 700 : 400,
                color: isDom ? meta.color : 'var(--text-3)',
              }}>
                {meta.label}
              </span>
              <StrengthBar value={score} color={meta.color} />
              <span className="font-num" style={{
                fontSize: 12, fontWeight: 600, color: meta.color, width: 34, textAlign: 'right', flexShrink: 0,
              }}>
                {Math.round(score * 100)}%
              </span>
              {isGaining && <span style={{ fontSize: 10, color: 'var(--green)', flexShrink: 0 }}>↑</span>}
              {isLosing  && <span style={{ fontSize: 10, color: 'var(--red)',   flexShrink: 0 }}>↓</span>}
              {!isGaining && !isLosing && <span style={{ fontSize: 10, color: 'transparent', flexShrink: 0 }}>·</span>}
            </div>
          )
        })}
      </div>

      {/* Narrative */}
      <div style={{
        padding: '10px 14px', borderRadius: 8,
        background: 'var(--bg-elevated)',
        border: '1px solid var(--border-dim)',
        fontSize: 12, color: 'var(--text-3)', lineHeight: 1.6,
        fontStyle: 'italic',
      }}>
        {data.narrative_explanation}
      </div>
    </div>
  )
}

// ── Connected Wrapper mit Timeout + Error-Handling ────────────────────────────

export function DominanzKarteConnected() {
  const { data, isLoading, isError, refetch } = useDominance()
  const [timedOut, setTimedOut] = useState(false)

  // 10s Timeout-Timer: läuft nur wenn isLoading true ist
  useEffect(() => {
    if (!isLoading) {
      setTimedOut(false)
      return
    }
    const timer = setTimeout(() => setTimedOut(true), 10_000)
    return () => clearTimeout(timer)
  }, [isLoading])

  const handleReload = () => {
    setTimedOut(false)
    refetch()
  }

  // ── Zustand: Timeout ──
  if (timedOut) {
    return (
      <div className="card" style={{
        minHeight: 120, display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center', gap: 10,
      }}>
        <span style={{ fontSize: 28, color: 'var(--text-4)', lineHeight: 1 }}>◌</span>
        <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-3)' }}>
          Dominanz nicht verfügbar
        </span>
        <span style={{ fontSize: 11, color: 'var(--text-4)' }}>
          Timeout nach 10 Sekunden
        </span>
        <ReloadButton onClick={handleReload} />
      </div>
    )
  }

  // ── Zustand: Lädt ──
  if (isLoading) {
    return (
      <div className="card" style={{
        minHeight: 120, display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>
        <span style={{ fontSize: 12, color: 'var(--text-4)' }}>Lade Dominanz-Analyse…</span>
      </div>
    )
  }

  // ── Zustand: HTTP-Fehler ──
  if (isError || !data) {
    return (
      <div className="card" style={{
        minHeight: 100, display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center', gap: 8,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 14, color: 'var(--red)' }}>⚠</span>
          <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--red)' }}>
            Dominanz-Analyse nicht erreichbar
          </span>
        </div>
        <span style={{ fontSize: 11, color: 'var(--text-4)' }}>
          API-Fehler — Backend möglicherweise nicht verfügbar
        </span>
        <ReloadButton onClick={handleReload} />
      </div>
    )
  }

  // ── Zustand: HTTP 200, aber Backend meldet Fallback (error-Feld gesetzt) ──
  if (data.error) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '10px 14px', borderRadius: 8,
          background: 'rgba(220,38,38,0.06)',
          border: '1px solid rgba(220,38,38,0.18)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, minWidth: 0 }}>
            <span style={{ fontSize: 13, color: 'var(--red)', flexShrink: 0 }}>⚠</span>
            <div style={{ minWidth: 0 }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--red)' }}>
                Dominanz-Fallback aktiv
              </div>
              <div style={{
                fontSize: 11, color: 'var(--red)', opacity: 0.75, marginTop: 2,
                overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
              }}>
                {data.error}
              </div>
            </div>
          </div>
          <ReloadButton onClick={handleReload} />
        </div>
      </div>
    )
  }

  // ── Zustand: OK ──
  return <DominanzKarte data={data} />
}
