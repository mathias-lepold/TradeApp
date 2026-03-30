import type { ReactNode } from 'react'
import type { SignalType, RecommendationAction, RecommendationPriority } from '../../api/types'

interface BadgeProps {
  children: ReactNode
  variant?: 'buy' | 'sell' | 'hold' | 'avoid' | 'neutral' | 'green' | 'red' | 'amber' | 'blue' | 'dim'
  size?: 'sm' | 'md' | 'lg'
}

const STYLES: Record<NonNullable<BadgeProps['variant']>, string> = {
  buy:     'badge-buy',
  sell:    'badge-sell',
  hold:    'badge-hold',
  avoid:   'badge-avoid',
  green:   'badge-buy',
  red:     'badge-sell',
  amber:   'badge-hold',
  blue:    'badge-blue',
  neutral: 'badge-dim',
  dim:     'badge-dim',
}

const SIZE_CLASS: Record<NonNullable<BadgeProps['size']>, string> = {
  sm: '',
  md: 'badge-md',
  lg: 'badge-lg',
}

export function Badge({ children, variant = 'neutral', size = 'sm' }: BadgeProps) {
  return (
    <span className={`badge ${STYLES[variant]} ${SIZE_CLASS[size]}`}>
      {children}
    </span>
  )
}

export function SignalTypeBadge({ type }: { type: SignalType }) {
  const map: Record<SignalType, BadgeProps['variant']> = {
    buy: 'buy', sell: 'sell', hold: 'hold', avoid: 'avoid', reduce: 'sell', add: 'buy',
  }
  const labels: Record<SignalType, string> = {
    buy: 'Kaufen', sell: 'Verkaufen', hold: 'Halten',
    avoid: 'Meiden', reduce: 'Reduzieren', add: 'Aufstocken',
  }
  return <Badge variant={map[type]} size="md">{labels[type]}</Badge>
}

export function ActionBadge({ action }: { action: RecommendationAction }) {
  const map: Record<RecommendationAction, BadgeProps['variant']> = {
    buy: 'buy', sell: 'sell', hold: 'hold', avoid: 'avoid',
    add: 'buy', reduce: 'sell', exit: 'sell', rebalance: 'amber', wait: 'dim',
  }
  const labels: Record<RecommendationAction, string> = {
    buy: 'Kaufen', sell: 'Verkaufen', hold: 'Halten', avoid: 'Meiden',
    add: 'Aufstocken', reduce: 'Reduzieren', exit: 'Ausstieg',
    rebalance: 'Rebalancieren', wait: 'Abwarten',
  }
  return <Badge variant={map[action]} size="md">{labels[action]}</Badge>
}

export function PriorityDot({ priority, size = 'md' }: { priority: RecommendationPriority; size?: 'sm' | 'md' | 'lg' }) {
  const colors: Record<RecommendationPriority, string> = {
    urgent: 'var(--red)', high: 'var(--amber)', normal: 'var(--accent)', low: 'var(--text-4)',
  }
  const dim = size === 'lg' ? 10 : size === 'md' ? 8 : 6
  return (
    <span style={{
      display: 'inline-block',
      width: dim, height: dim,
      borderRadius: '50%',
      background: colors[priority],
      flexShrink: 0,
      boxShadow: `0 0 6px ${colors[priority]}80`,
    }} />
  )
}
