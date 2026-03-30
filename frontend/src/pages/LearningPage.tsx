/**
 * LearningPage — Lernsystem der TradeApp
 *
 * Zeigt:
 * - Systemleistung (Trefferquote, Accuracy je Fehlerart)
 * - Evaluations-Timeline mit allen bewerteten Empfehlungen
 * - Optimierungsvorschläge als kopierbare Prompts
 */
import { useState } from 'react'
import { useEvaluations, usePromptSuggestions } from '../hooks/useApi'
import type { Evaluation, PromptSuggestion, EvaluationStats } from '../api/types'
import { LoadingSpinner } from '../components/ui/LoadingSpinner'
import { StatTile } from '../components/ui/Card'

// ── Formatierung ──────────────────────────────────────────────────────────────

const ERROR_TYPE_META: Record<string, { label: string; color: string; icon: string }> = {
  correct:           { label: 'Korrekt',             color: 'var(--green)',  icon: '✓' },
  wrong_regime:      { label: 'Falsches Regime',      color: 'var(--red)',   icon: '⚠' },
  wrong_dominance:   { label: 'Falsche Dominanz',     color: '#f97316',      icon: '◈' },
  wrong_psychology:  { label: 'Psychologie falsch',   color: '#a78bfa',      icon: '◉' },
  wrong_liquidity:   { label: 'Liquidität falsch',    color: 'var(--amber)', icon: '◎' },
  wrong_timing:      { label: 'Timing falsch',        color: '#38bdf8',      icon: '⊙' },
  unknown:           { label: 'Unbekannt',            color: 'var(--text-4)', icon: '?' },
}

const PRIO_META: Record<string, { color: string; bg: string }> = {
  high:   { color: '#dc2626', bg: 'rgba(220,38,38,0.10)' },
  medium: { color: 'var(--amber)', bg: 'rgba(245,158,11,0.12)' },
  low:    { color: 'var(--text-3)', bg: 'var(--bg-elevated)' },
}

const ACTION_LABEL: Record<string, string> = {
  buy: 'Kaufen', sell: 'Verkaufen', hold: 'Halten',
  accumulate: 'Nachkaufen', reduce: 'Reduzieren',
  exit: 'Aussteigen', avoid: 'Meiden', watch: 'Beobachten',
}

function fmtDate(iso: string) {
  return new Date(iso).toLocaleDateString('de-CH', { day: '2-digit', month: '2-digit', year: '2-digit' })
}

// ── Performance Chart (einfache ASCII-ähnliche Balken) ───────────────────────

function ErrorTypeStats({ stats }: { stats: EvaluationStats }) {
  const byType = stats.by_error_type ?? {}
  const entries = Object.entries(byType).filter(([k]) => k !== 'unknown')

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      {entries.map(([type, d]) => {
        const meta = ERROR_TYPE_META[type] ?? ERROR_TYPE_META.unknown
        const winRate = typeof d.win_rate === 'number' ? d.win_rate : 0
        const avgAcc  = typeof d.avg_accuracy === 'number' ? d.avg_accuracy : 0
        return (
          <div key={type} style={{
            padding: '12px 14px', borderRadius: 9,
            background: 'var(--bg-card)',
            border: `1px solid ${type === 'correct' ? 'rgba(34,197,94,0.2)' : 'var(--border-dim)'}`,
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
              <span style={{ color: meta.color, fontSize: 14 }}>{meta.icon}</span>
              <span style={{ fontSize: 13, fontWeight: 700, color: meta.color, flex: 1 }}>{meta.label}</span>
              <span style={{ fontSize: 12, color: 'var(--text-4)' }}>{d.count}×</span>
            </div>
            <div style={{ display: 'flex', gap: 16 }}>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 11, color: 'var(--text-4)', marginBottom: 4 }}>Trefferquote</div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <div style={{ flex: 1, height: 4, background: 'var(--bg-elevated)', borderRadius: 2, overflow: 'hidden' }}>
                    <div style={{ height: '100%', width: `${winRate * 100}%`, background: meta.color, borderRadius: 2, transition: 'width 0.5s' }} />
                  </div>
                  <span className="font-num" style={{ fontSize: 12, fontWeight: 700, color: meta.color, width: 36, textAlign: 'right' }}>
                    {(winRate * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 11, color: 'var(--text-4)', marginBottom: 4 }}>Ø Accuracy</div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <div style={{ flex: 1, height: 4, background: 'var(--bg-elevated)', borderRadius: 2, overflow: 'hidden' }}>
                    <div style={{ height: '100%', width: `${avgAcc * 100}%`, background: 'var(--accent)', borderRadius: 2, transition: 'width 0.5s' }} />
                  </div>
                  <span className="font-num" style={{ fontSize: 12, fontWeight: 700, color: 'var(--accent)', width: 36, textAlign: 'right' }}>
                    {(avgAcc * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}

// ── Evaluations Timeline ──────────────────────────────────────────────────────

function EvaluationRow({ e }: { e: Evaluation }) {
  const meta = ERROR_TYPE_META[e.error_type ?? 'unknown'] ?? ERROR_TYPE_META.unknown
  const ret  = e.return_5d_pct ?? e.return_1d_pct ?? 0
  const retColor = ret > 0 ? 'var(--green)' : ret < 0 ? 'var(--red)' : 'var(--text-4)'

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '80px 60px 130px 90px 70px 60px 1fr',
      gap: 8,
      alignItems: 'center',
      padding: '10px 0',
      borderBottom: '1px solid var(--border-dim)',
    }}>
      <span style={{ fontSize: 12, color: 'var(--text-4)' }}>
        {e.evaluated_at ? fmtDate(e.evaluated_at) : '—'}
      </span>
      <span style={{ fontWeight: 700, color: 'var(--text-1)', fontSize: 13 }}>{e.symbol}</span>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        <span style={{
          fontSize: 11, padding: '2px 7px', borderRadius: 4, fontWeight: 600,
          background: e.correct ? 'rgba(34,197,94,0.1)' : 'rgba(239,68,68,0.1)',
          color: e.correct ? 'var(--green)' : 'var(--red)',
          border: `1px solid ${e.correct ? 'rgba(34,197,94,0.25)' : 'rgba(239,68,68,0.25)'}`,
        }}>
          {e.correct ? '✓' : '✗'} {ACTION_LABEL[e.predicted_action] ?? e.predicted_action}
        </span>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        <span style={{ fontSize: 12, color: meta.color }}>{meta.icon}</span>
        <span style={{ fontSize: 11, color: meta.color }}>{meta.label}</span>
      </div>
      <span className="font-num" style={{ fontSize: 13, fontWeight: 700, color: retColor }}>
        {ret >= 0 ? '+' : ''}{ret?.toFixed(1)}%
      </span>
      <span className="font-num" style={{
        fontSize: 12, fontWeight: 600,
        color: e.accuracy_score >= 0.65 ? 'var(--green)' : e.accuracy_score >= 0.4 ? 'var(--amber)' : 'var(--red)',
      }}>
        {(e.accuracy_score * 100).toFixed(0)}%
      </span>
      <span style={{ fontSize: 11, color: 'var(--text-4)', fontStyle: 'italic', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
        {e.lesson_learned ?? '—'}
      </span>
    </div>
  )
}

// ── Prompt Suggestion Card ────────────────────────────────────────────────────

function PromptCard({ s }: { s: PromptSuggestion }) {
  const [copied, setCopied] = useState(false)
  const prio = PRIO_META[s.priority] ?? PRIO_META.low

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(s.suggestion_prompt)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // Fallback: Text selektieren
    }
  }

  return (
    <div style={{
      borderRadius: 10,
      border: `1px solid ${prio.color}30`,
      background: 'var(--bg-card)',
      overflow: 'hidden',
    }}>
      {/* Header */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 10,
        padding: '12px 16px',
        background: prio.bg,
        borderBottom: `1px solid ${prio.color}20`,
      }}>
        <div style={{
          width: 8, height: 8, borderRadius: '50%',
          background: prio.color, flexShrink: 0,
        }} />
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-1)' }}>{s.category_label}</div>
          <div style={{ fontSize: 11, color: 'var(--text-4)', marginTop: 2 }}>
            {s.based_on_errors} Fehler analysiert
          </div>
        </div>
        <div style={{
          fontSize: 10, fontWeight: 700, letterSpacing: '0.06em',
          padding: '3px 8px', borderRadius: 4,
          background: `${prio.color}20`,
          color: prio.color,
          border: `1px solid ${prio.color}40`,
          textTransform: 'uppercase',
        }}>
          {s.priority === 'high' ? 'Hoch' : s.priority === 'medium' ? 'Mittel' : 'Niedrig'}
        </div>
      </div>

      {/* Problem */}
      <div style={{ padding: '10px 16px 0', fontSize: 12, color: 'var(--text-3)' }}>
        <span style={{ fontWeight: 600, color: 'var(--text-2)' }}>Problem: </span>
        {s.problem}
      </div>

      {/* Beispiel */}
      <div style={{ padding: '6px 16px 0', fontSize: 11, color: 'var(--text-4)', fontStyle: 'italic' }}>
        Bsp: {s.example_case}
      </div>

      {/* Prompt */}
      <div style={{ padding: '10px 16px 14px' }}>
        <div style={{ fontSize: 11, color: 'var(--text-4)', marginBottom: 6, fontWeight: 600, letterSpacing: '0.05em', textTransform: 'uppercase' }}>
          Optimierungsvorschlag
        </div>
        <div style={{
          padding: '12px 14px',
          borderRadius: 8,
          background: '#f8fafc',
          border: '1px solid var(--border-std)',
          fontFamily: 'monospace',
          fontSize: 12,
          color: '#15803d',
          lineHeight: 1.7,
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word',
        }}>
          {s.suggestion_prompt}
        </div>
        <button
          onClick={handleCopy}
          style={{
            marginTop: 10,
            padding: '7px 16px',
            borderRadius: 7,
            border: `1px solid ${copied ? 'rgba(34,197,94,0.4)' : 'var(--border-std)'}`,
            background: copied ? 'rgba(34,197,94,0.12)' : 'var(--bg-elevated)',
            color: copied ? 'var(--green)' : 'var(--text-2)',
            fontSize: 12, fontWeight: 600,
            cursor: 'pointer',
            transition: 'all var(--trans)',
          }}
        >
          {copied ? '✓ Kopiert!' : '📋 In Zwischenablage'}
        </button>
      </div>
    </div>
  )
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function LearningPage() {
  const { data: evalData, isLoading: evalLoading } = useEvaluations()
  const { data: suggestions, isLoading: suggLoading } = usePromptSuggestions()
  const [activeTab, setActiveTab] = useState<'timeline' | 'prompts'>('timeline')

  if (evalLoading || suggLoading) return <LoadingSpinner message="Lade Lerndaten…" fullPage />

  const stats      = evalData?.stats
  const evals      = evalData?.evaluations ?? []
  const suggs      = suggestions ?? []

  const winRate    = stats?.win_rate ?? 0
  const avgAcc     = stats?.avg_accuracy ?? 0
  const total      = stats?.total ?? 0
  const correct    = stats?.correct ?? 0

  const winColor   = winRate >= 0.65 ? 'var(--green)' : winRate >= 0.5 ? 'var(--amber)' : 'var(--red)'
  const highPrio   = suggs.filter(s => s.priority === 'high').length

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

      {/* ── Stat Tiles ── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
        <StatTile
          label="Gesamte Evaluationen"
          value={String(total)}
          sub={`${correct} korrekt`}
          mono
        />
        <StatTile
          label="Trefferquote"
          value={`${(winRate * 100).toFixed(1)}%`}
          sub={winRate >= 0.65 ? 'Ziel erreicht (≥65%)' : 'Ziel: 65%'}
          accentColor={winColor}
          mono
        />
        <StatTile
          label="Ø Accuracy Score"
          value={`${(avgAcc * 100).toFixed(1)}%`}
          sub="Über alle Empfehlungen"
          accentColor={avgAcc >= 0.65 ? 'var(--green)' : avgAcc >= 0.45 ? 'var(--amber)' : 'var(--red)'}
          mono
        />
        <StatTile
          label="Offene Optimierungen"
          value={String(highPrio)}
          sub={`${suggs.length} Vorschläge total`}
          negative={highPrio > 0}
          mono
        />
      </div>

      {/* ── Erklärungstext ── */}
      <div style={{
        padding: '12px 18px', borderRadius: 10,
        background: 'rgba(59,130,246,0.06)', border: '1px solid rgba(59,130,246,0.15)',
        fontSize: 13, color: 'var(--text-3)', lineHeight: 1.6,
      }}>
        <strong style={{ color: 'var(--accent)' }}>Lernsystem:</strong>{' '}
        Das System bewertet vergangene Empfehlungen nach 1/5/20 Tagen und klassifiziert Fehler nach Ursache
        (falsches Regime, falsche Dominanz, Psychologie, Liquidität, Timing). Die Optimierungsvorschläge sind
        direkt als Prompts nutzbar, um zukünftige Analysen zu verbessern.
        {total >= 5 && (
          <> Letzte {total} Empfehlungen: {(winRate * 100).toFixed(0)}% Trefferquote.</>
        )}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.6fr', gap: 20, alignItems: 'start' }}>

        {/* ── Fehlerarten-Statistik ── */}
        <div className="card">
          <div className="label-caps" style={{ marginBottom: 16 }}>Leistung je Fehlerart</div>
          {stats ? (
            <ErrorTypeStats stats={stats} />
          ) : (
            <div style={{ textAlign: 'center', padding: 24, color: 'var(--text-4)' }}>Keine Daten</div>
          )}
        </div>

        {/* ── Tabs: Timeline / Prompts ── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

          {/* Tab-Bar */}
          <div style={{
            display: 'flex', gap: 4,
            padding: 4, borderRadius: 10,
            background: 'var(--bg-card)',
            border: '1px solid var(--border-std)',
          }}>
            {([
              { key: 'timeline', label: `Evaluations (${evals.length})` },
              { key: 'prompts',  label: `Optimierungen (${suggs.length})` },
            ] as const).map(({ key, label }) => (
              <button
                key={key}
                onClick={() => setActiveTab(key)}
                style={{
                  flex: 1, padding: '8px 12px', borderRadius: 7,
                  border: 'none',
                  background: activeTab === key ? 'var(--bg-elevated)' : 'transparent',
                  color: activeTab === key ? 'var(--text-1)' : 'var(--text-4)',
                  fontSize: 13, fontWeight: activeTab === key ? 700 : 400,
                  cursor: 'pointer', transition: 'all var(--trans)',
                }}
              >{label}</button>
            ))}
          </div>

          {/* Tab Content */}
          {activeTab === 'timeline' && (
            <div className="card" style={{ padding: '12px 16px' }}>
              {/* Table Header */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: '80px 60px 130px 90px 70px 60px 1fr',
                gap: 8,
                padding: '0 0 8px',
                borderBottom: '1px solid var(--border-std)',
              }}>
                {['Datum', 'Symbol', 'Empfehlung', 'Fehlerart', 'Return', 'Score', 'Lektion'].map(h => (
                  <span key={h} style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-4)', letterSpacing: '0.06em', textTransform: 'uppercase' }}>
                    {h}
                  </span>
                ))}
              </div>
              {evals.length === 0 ? (
                <div style={{ textAlign: 'center', padding: 32, color: 'var(--text-4)' }}>Noch keine Evaluationen</div>
              ) : (
                evals.map(e => <EvaluationRow key={e.id} e={e} />)
              )}
            </div>
          )}

          {activeTab === 'prompts' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              {suggs.length === 0 ? (
                <div className="card" style={{ textAlign: 'center', padding: 40, color: 'var(--text-4)' }}>
                  Keine Optimierungsvorschläge
                </div>
              ) : (
                suggs.map(s => <PromptCard key={s.id} s={s} />)
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
