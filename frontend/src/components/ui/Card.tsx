import type { ReactNode, CSSProperties } from 'react'

interface CardProps {
  children: ReactNode
  className?: string
  style?: CSSProperties
  onClick?: () => void
  elevated?: boolean
}

export function Card({ children, className = '', style, onClick, elevated }: CardProps) {
  const base = elevated ? 'card card-elevated' : 'card'
  return (
    <div
      className={`${base} ${className} ${onClick ? 'card-hover' : ''}`}
      style={style}
      onClick={onClick}
    >
      {children}
    </div>
  )
}

export function CardHeader({
  title, subtitle, action,
}: { title: string; subtitle?: string; action?: ReactNode }) {
  return (
    <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 18 }}>
      <div>
        <div className="label-caps" style={{ marginBottom: 5 }}>{title}</div>
        {subtitle && (
          <div style={{ color: 'var(--text-3)', fontSize: 13, fontWeight: 400 }}>{subtitle}</div>
        )}
      </div>
      {action}
    </div>
  )
}

interface StatTileProps {
  label: string
  value: string | number
  sub?: string
  positive?: boolean
  negative?: boolean
  mono?: boolean
  icon?: ReactNode
  accentColor?: string
}

export function StatTile({ label, value, sub, positive, negative, mono, icon, accentColor }: StatTileProps) {
  const col = positive ? 'var(--green)' : negative ? 'var(--red)' : accentColor ?? 'var(--text-1)'
  const subCol = positive ? 'var(--green)' : negative ? 'var(--red)' : 'var(--text-4)'

  return (
    <div className="stat-tile">
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 12 }}>
        <span className="label-caps">{label}</span>
        {icon && (
          <div style={{
            width: 32, height: 32, borderRadius: 8,
            background: 'var(--bg-elevated)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: 'var(--text-4)',
          }}>
            {icon}
          </div>
        )}
      </div>
      <div
        className={mono ? 'font-num' : ''}
        style={{
          fontSize: 26,
          fontWeight: 700,
          color: col,
          lineHeight: 1.1,
          letterSpacing: mono ? '-0.02em' : '-0.01em',
        }}
      >
        {value}
      </div>
      {sub && (
        <div style={{ fontSize: 12, color: subCol, marginTop: 6, fontWeight: 500 }}>
          {sub}
        </div>
      )}
    </div>
  )
}

export function Divider() {
  return <div style={{ height: 1, background: 'var(--border-dim)', margin: '16px 0' }} />
}
