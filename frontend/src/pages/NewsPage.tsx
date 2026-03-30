import { useState } from 'react'
import { useAllNews, useNewsForSymbol } from '../hooks/useApi'
import type { NewsItem, NewsSentiment } from '../api/types'
import { LoadingSpinner, EmptyState } from '../components/ui/LoadingSpinner'

const SYMBOLS = ['Alle', 'NVDA', 'MSFT', 'AAPL', 'NOVN', 'ZGLD', 'SPY']

const SENTIMENT_META: Record<NewsSentiment, { label: string; color: string; bg: string }> = {
  bullish: { label: 'Bullish',  color: 'var(--green)', bg: 'rgba(34,197,94,0.12)' },
  bearish: { label: 'Bearish',  color: 'var(--red)',   bg: 'rgba(239,68,68,0.12)' },
  neutral: { label: 'Neutral',  color: 'var(--text-3)', bg: 'var(--bg-elevated)' },
}

function timeAgo(isoStr: string): string {
  const diff = (Date.now() - new Date(isoStr).getTime()) / 1000
  if (diff < 3600)  return `vor ${Math.round(diff / 60)} Min.`
  if (diff < 86400) return `vor ${Math.round(diff / 3600)} Std.`
  return `vor ${Math.round(diff / 86400)} Tagen`
}

function NewsCard({ item }: { item: NewsItem }) {
  const s = SENTIMENT_META[item.sentiment]
  return (
    <div
      className="card"
      style={{ padding: 20, display: 'flex', flexDirection: 'column', gap: 12, position: 'relative' }}
    >
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12 }}>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
          <span style={{
            fontSize: 11, fontWeight: 700, padding: '2px 8px', borderRadius: 5,
            background: 'var(--accent-dim)', color: 'var(--accent)',
            letterSpacing: '0.05em', textTransform: 'uppercase',
          }}>{item.symbol}</span>
          <span style={{
            fontSize: 11, fontWeight: 600, padding: '2px 8px', borderRadius: 5,
            background: s.bg, color: s.color,
          }}>{s.label}</span>
          {item.is_mock && (
            <span style={{
              fontSize: 10, color: 'var(--text-4)', background: 'var(--bg-elevated)',
              border: '1px solid var(--border-dim)', padding: '1px 6px', borderRadius: 4,
            }}>Simuliert</span>
          )}
        </div>
        <div style={{ fontSize: 11, color: 'var(--text-4)', whiteSpace: 'nowrap', flexShrink: 0 }}>
          {timeAgo(item.published_at)}
        </div>
      </div>

      {/* Title */}
      <div style={{ fontWeight: 700, color: 'var(--text-1)', fontSize: 15, lineHeight: 1.4 }}>
        {item.title}
      </div>

      {/* Summary */}
      {item.summary && item.summary !== item.title && (
        <div style={{ color: 'var(--text-3)', fontSize: 13, lineHeight: 1.6 }}>
          {item.summary.length > 220 ? item.summary.slice(0, 220) + '…' : item.summary}
        </div>
      )}

      {/* Footer */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 'auto' }}>
        <span style={{ fontSize: 11, color: 'var(--text-4)' }}>{item.source}</span>
        {item.url && !item.is_mock && (
          <a
            href={item.url} target="_blank" rel="noopener noreferrer"
            style={{
              fontSize: 12, color: 'var(--accent)', textDecoration: 'none',
              display: 'flex', alignItems: 'center', gap: 4,
              padding: '4px 10px', borderRadius: 6,
              border: '1px solid var(--accent-glow)',
              background: 'var(--accent-dim)',
              transition: 'all var(--trans)',
            }}
          >
            Lesen →
          </a>
        )}
      </div>
    </div>
  )
}

function AllNewsView({ limitPer }: { limitPer: number }) {
  const { data: news = [], isLoading } = useAllNews(limitPer)
  if (isLoading) return <LoadingSpinner message="Lade Nachrichten…" />
  if (!news.length) return <EmptyState message="Keine Nachrichten verfügbar" />
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))', gap: 16 }}>
      {news.map(n => <NewsCard key={n.id} item={n} />)}
    </div>
  )
}

function SymbolNewsView({ symbol }: { symbol: string }) {
  const { data: news = [], isLoading } = useNewsForSymbol(symbol)
  if (isLoading) return <LoadingSpinner message={`Lade ${symbol} Nachrichten…`} />
  if (!news.length) return <EmptyState message={`Keine Nachrichten für ${symbol}`} />
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {news.map(n => <NewsCard key={n.id} item={n} />)}
    </div>
  )
}

export default function NewsPage() {
  const [selected, setSelected] = useState('Alle')
  const [limitPer, setLimitPer] = useState(3)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

      {/* ── Filter Bar ── */}
      <div className="filter-bar" style={{ flexWrap: 'wrap', gap: 12 }}>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          {SYMBOLS.map(s => (
            <button
              key={s}
              className={`filter-chip${selected === s ? ' active' : ''}`}
              onClick={() => setSelected(s)}
            >{s}</button>
          ))}
        </div>

        {selected === 'Alle' && (
          <>
            <div style={{ width: 1, height: 24, background: 'var(--border-std)' }} />
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <span className="label-caps">Je Symbol</span>
              <input
                type="range" min={1} max={8} step={1} value={limitPer}
                onChange={e => setLimitPer(Number(e.target.value))}
                style={{ width: 90, accentColor: 'var(--accent)' }}
              />
              <span className="font-num" style={{
                fontSize: 13, fontWeight: 700, color: 'var(--accent)',
                background: 'var(--accent-dim)', padding: '2px 7px', borderRadius: 6,
              }}>{limitPer}</span>
            </div>
          </>
        )}
      </div>

      {/* ── Sentiment Legend ── */}
      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
        {(Object.entries(SENTIMENT_META) as [NewsSentiment, typeof SENTIMENT_META[NewsSentiment]][]).map(([key, m]) => (
          <div key={key} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <div style={{ width: 8, height: 8, borderRadius: '50%', background: m.color }} />
            <span style={{ fontSize: 12, color: 'var(--text-3)' }}>{m.label}</span>
          </div>
        ))}
        <span style={{ fontSize: 12, color: 'var(--text-4)', marginLeft: 8 }}>
          · Sentiment wird automatisch aus dem Titeltext abgeleitet
        </span>
      </div>

      {/* ── Content ── */}
      {selected === 'Alle'
        ? <AllNewsView limitPer={limitPer} />
        : <SymbolNewsView symbol={selected} />
      }
    </div>
  )
}
