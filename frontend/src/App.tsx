import { useState, useEffect, useRef } from 'react'
import { Chart, registerables } from 'chart.js'
Chart.register(...registerables)

// ── Types ──────────────────────────────────────────
type Page = 'home' | 'heatmap' | 'signals' | 'portfolio' | 'macro' | 'journal'
type HmView = 'sec' | 'reg' | 'cty' | 'fx'
type HmTime = '1d' | '1w' | '1m' | 'ytd'

interface HeatmapItem {
  id: string; n: string; c1d: number; c1w: number; c1m: number; cYtd: number; w: number
  s: { t: string; c: number }[]
}

// ── Heatmap Color ──────────────────────────────────
const COL = (c: number) =>
  c >= 4 ? '#14532d' : c >= 2 ? '#15803d' : c >= 0.8 ? '#16a34a' :
  c >= 0.2 ? '#4ade80' : c > -0.2 ? '#374151' : c > -0.8 ? '#f87171' :
  c > -2 ? '#dc2626' : c > -4 ? '#991b1b' : '#450a0a'

// ── Data ───────────────────────────────────────────
const SECTORS: HeatmapItem[] = [
  { id:'tech',    n:'Technologie',    c1d:-1.8,  c1w:-3.2, c1m:-8.1,  cYtd:-12.4, w:28, s:[{t:'MSFT',c:-0.46},{t:'NVDA',c:2.43},{t:'AAPL',c:-1.20},{t:'META',c:0.81}] },
  { id:'health',  n:'Gesundheit',     c1d:0.9,   c1w:1.2,  c1m:3.4,   cYtd:5.1,   w:13, s:[{t:'LLY',c:1.81},{t:'NOVN',c:0.81}] },
  { id:'finance', n:'Finanzen',       c1d:-0.4,  c1w:-0.8, c1m:1.2,   cYtd:2.8,   w:13, s:[{t:'JPM',c:-0.51},{t:'V',c:0.32}] },
  { id:'energy',  n:'Energie',        c1d:2.8,   c1w:4.1,  c1m:9.2,   cYtd:14.3,  w:5,  s:[{t:'XOM',c:3.12},{t:'CVX',c:2.64}] },
  { id:'consumer',n:'Konsum',         c1d:-1.2,  c1w:-2.4, c1m:-4.8,  cYtd:-7.2,  w:10, s:[{t:'AMZN',c:-1.82},{t:'TSLA',c:-2.40}] },
  { id:'industry',n:'Industrie',      c1d:-0.3,  c1w:0.6,  c1m:2.1,   cYtd:3.4,   w:9,  s:[{t:'RTX',c:1.42},{t:'LMT',c:1.81}] },
  { id:'comm',    n:'Kommunikation',  c1d:-0.6,  c1w:-1.1, c1m:-2.8,  cYtd:-4.1,  w:8,  s:[{t:'NFLX',c:-0.41},{t:'DIS',c:-0.82}] },
  { id:'smi',     n:'SMI (CH)',       c1d:0.3,   c1w:0.8,  c1m:1.4,   cYtd:2.1,   w:7,  s:[{t:'NESN',c:0.40},{t:'NOVN',c:0.81}] },
  { id:'mats',    n:'Rohstoffe',      c1d:1.4,   c1w:2.8,  c1m:5.9,   cYtd:8.2,   w:3,  s:[] },
  { id:'utils',   n:'Versorger',      c1d:0.6,   c1w:1.0,  c1m:2.8,   cYtd:4.2,   w:3,  s:[] },
  { id:'re',      n:'Immobilien',     c1d:-0.8,  c1w:-1.4, c1m:-3.1,  cYtd:-5.8,  w:2,  s:[] },
]
const REGIONS: HeatmapItem[] = [
  { id:'na',  n:'Nordamerika',   c1d:-0.82, c1w:-1.4, c1m:-3.2, cYtd:-5.1,  w:42, s:[] },
  { id:'eu',  n:'Europa',        c1d:0.48,  c1w:0.9,  c1m:2.1,  cYtd:3.4,   w:26, s:[] },
  { id:'ap',  n:'Asien-Pazifik', c1d:-0.34, c1w:-0.8, c1m:-1.9, cYtd:-3.2,  w:24, s:[] },
  { id:'mea', n:'Naher Osten',   c1d:1.80,  c1w:3.2,  c1m:6.4,  cYtd:9.1,   w:4,  s:[] },
  { id:'la',  n:'Lateinamerika', c1d:-1.40, c1w:-2.8, c1m:-4.1, cYtd:-6.8,  w:4,  s:[] },
]
const COUNTRIES: HeatmapItem[] = [
  { id:'us', n:'USA',         c1d:-0.82, c1w:-1.4, c1m:-3.2, cYtd:-5.1,  w:28, s:[] },
  { id:'cn', n:'China',       c1d:-0.61, c1w:-0.9, c1m:-2.1, cYtd:-4.4,  w:14, s:[] },
  { id:'jp', n:'Japan',       c1d:-0.34, c1w:-0.8, c1m:-1.9, cYtd:-3.2,  w:6,  s:[] },
  { id:'de', n:'Deutschland', c1d:0.54,  c1w:0.9,  c1m:2.1,  cYtd:3.4,   w:5,  s:[] },
  { id:'in', n:'Indien',      c1d:1.20,  c1w:2.1,  c1m:4.2,  cYtd:6.8,   w:4,  s:[] },
  { id:'gb', n:'UK',          c1d:0.22,  c1w:0.4,  c1m:0.9,  cYtd:1.8,   w:4,  s:[] },
  { id:'fr', n:'Frankreich',  c1d:0.61,  c1w:1.0,  c1m:2.3,  cYtd:3.8,   w:4,  s:[] },
  { id:'br', n:'Brasilien',   c1d:-1.80, c1w:-2.8, c1m:-4.1, cYtd:-6.8,  w:3,  s:[] },
  { id:'ca', n:'Kanada',      c1d:0.40,  c1w:0.6,  c1m:1.2,  cYtd:2.1,   w:3,  s:[] },
  { id:'ch', n:'Schweiz',     c1d:0.31,  c1w:0.8,  c1m:1.4,  cYtd:2.1,   w:2,  s:[] },
  { id:'sa', n:'Saudi-Arab.', c1d:2.10,  c1w:3.2,  c1m:6.4,  cYtd:9.1,   w:2,  s:[] },
  { id:'il', n:'Israel',      c1d:-2.40, c1w:-4.1, c1m:-8.2, cYtd:-12.4, w:1,  s:[] },
  { id:'it', n:'Italien',     c1d:0.74,  c1w:1.1,  c1m:2.6,  cYtd:4.1,   w:2,  s:[] },
  { id:'mx', n:'Mexiko',      c1d:-1.10, c1w:-1.8, c1m:-3.4, cYtd:-5.2,  w:2,  s:[] },
]
const FX: HeatmapItem[] = [
  { id:'eurusd', n:'EUR/USD',       c1d:-0.18, c1w:-0.4, c1m:-0.9, cYtd:-1.8, w:20, s:[] },
  { id:'usdjpy', n:'USD/JPY',       c1d:0.22,  c1w:0.5,  c1m:1.1,  cYtd:2.4,  w:13, s:[] },
  { id:'gbpusd', n:'GBP/USD',       c1d:-0.12, c1w:-0.3, c1m:-0.6, cYtd:-1.2, w:10, s:[] },
  { id:'usdchf', n:'USD/CHF',       c1d:-0.19, c1w:-0.4, c1m:-0.8, cYtd:-1.6, w:8,  s:[] },
  { id:'eurchf', n:'EUR/CHF',       c1d:-0.19, c1w:-0.5, c1m:-0.9, cYtd:-1.8, w:7,  s:[] },
  { id:'xauusd', n:'XAU/USD (Gold)',c1d:-0.30, c1w:-1.2, c1m:-3.8, cYtd:12.4, w:6,  s:[] },
  { id:'xagusd', n:'XAG/USD (Silb)',c1d:0.80,  c1w:-2.1, c1m:-8.4, cYtd:18.2, w:3,  s:[] },
  { id:'usdcny', n:'USD/CNY',       c1d:0.08,  c1w:0.2,  c1m:0.3,  cYtd:0.8,  w:9,  s:[] },
  { id:'audusd', n:'AUD/USD',       c1d:-0.31, c1w:-0.7, c1m:-1.4, cYtd:-2.8, w:6,  s:[] },
  { id:'usdbrl', n:'USD/BRL',       c1d:0.82,  c1w:1.4,  c1m:2.8,  cYtd:5.6,  w:4,  s:[] },
  { id:'usdinr', n:'USD/INR',       c1d:0.12,  c1w:0.2,  c1m:0.5,  cYtd:1.1,  w:5,  s:[] },
  { id:'usdcad', n:'USD/CAD',       c1d:0.14,  c1w:0.3,  c1m:0.6,  cYtd:1.2,  w:6,  s:[] },
]
const HM_DATA: Record<HmView, HeatmapItem[]> = { sec: SECTORS, reg: REGIONS, cty: COUNTRIES, fx: FX }

const INDICES = [
  { id:'sp500',  label:'S&P 500', value:"5'218", chg:-0.82 },
  { id:'nasdaq', label:'NASDAQ',  value:"23'898",chg:-1.14 },
  { id:'smi',    label:'SMI',     value:"12'480",chg:0.31  },
  { id:'dax',    label:'DAX',     value:"22'150",chg:0.54  },
  { id:'gold',   label:'Gold',    value:"$4'850",chg:-0.30 },
  { id:'oel',    label:'Öl WTI',  value:"$99.40",chg:1.21  },
  { id:'eurchf', label:'EUR/CHF', value:"0.937", chg:-0.21 },
  { id:'vix',    label:'VIX',     value:"24.5",  chg:-1.20 },
]

// ── Treemap Component ──────────────────────────────
function Treemap({ data, time, mini = false, onItem, onStock }: {
  data: HeatmapItem[]; time: HmTime; mini?: boolean
  onItem?: (id: string) => void; onStock?: (sym: string) => void
}) {
  const getChg = (item: HeatmapItem) =>
    time === '1d' ? item.c1d : time === '1w' ? item.c1w : time === '1m' ? item.c1m : item.cYtd

  const rowSz = mini ? 4 : 5
  const rows: HeatmapItem[][] = []
  for (let i = 0; i < data.length; i += rowSz) rows.push(data.slice(i, i + rowSz))

  return (
    <div style={{ display:'flex', flexDirection:'column', gap:2 }}>
      {rows.map((row, ri) => (
        <div key={ri} style={{ display:'flex', gap:2 }}>
          {row.map(item => {
            const chg = getChg(item)
            const minH = mini ? 44 : item.w >= 20 ? 130 : item.w >= 10 ? 100 : 72
            return (
              <div key={item.id}
                onClick={() => onItem?.(item.id)}
                style={{
                  flex: item.w, minHeight: minH, background: COL(chg),
                  borderRadius: 5, padding: '6px 8px', cursor: 'pointer',
                  border: '1.5px solid transparent', overflow: 'hidden',
                  display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
                  transition: 'border-color .12s',
                }}
                onMouseEnter={e => (e.currentTarget.style.borderColor = 'rgba(255,255,255,.4)')}
                onMouseLeave={e => (e.currentTarget.style.borderColor = 'transparent')}
              >
                <div>
                  <div style={{ fontSize:10, fontWeight:600, fontFamily:'var(--font-head)', color:'#fff', lineHeight:1.2, overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>{item.n}</div>
                  <div style={{ fontSize:10, color:'rgba(255,255,255,.75)', fontFamily:'var(--font-num)' }}>{chg > 0 ? '+' : ''}{chg.toFixed(2)}%</div>
                </div>
                {!mini && item.s.length > 0 && item.w >= 7 && (
                  <div style={{ display:'flex', flexWrap:'wrap', gap:1, marginTop:5 }}>
                    {item.s.map(st => (
                      <div key={st.t}
                        onClick={e => { e.stopPropagation(); onStock?.(st.t.toLowerCase()) }}
                        style={{ background: COL(st.c), borderRadius:3, padding:'2px 5px', cursor:'pointer' }}
                      >
                        <div style={{ fontSize:9, fontWeight:700, fontFamily:'var(--font-head)', color:'#fff' }}>{st.t}</div>
                        <div style={{ fontSize:9, color:'rgba(255,255,255,.75)', fontFamily:'var(--font-num)' }}>{st.c > 0 ? '+' : ''}{st.c.toFixed(1)}%</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      ))}
    </div>
  )
}

// ── Button Component ───────────────────────────────
function Btn({ children, variant = 'ghost', size = 'md', pill = false, onClick, style }: {
  children: React.ReactNode; variant?: 'primary'|'buy'|'sell'|'ghost'|'ai'|'outline'
  size?: 'xl'|'lg'|'md'|'sm'|'xs'; pill?: boolean; onClick?: () => void; style?: React.CSSProperties
}) {
  const bg: Record<string, string> = {
    primary: '#3d8ef8', buy: '#16a34a', sell: '#dc2626',
    ghost: 'var(--bg-elevated)', ai: '#0c447c', outline: 'transparent',
  }
  const color: Record<string, string> = {
    primary: '#fff', buy: '#fff', sell: '#fff',
    ghost: 'var(--text-2)', ai: '#93c5fd', outline: '#3d8ef8',
  }
  const pad: Record<string, string> = {
    xl:'12px 24px', lg:'10px 20px', md:'8px 16px', sm:'6px 12px', xs:'4px 10px'
  }
  const fs: Record<string, string> = { xl:'15px', lg:'13px', md:'12px', sm:'11px', xs:'10px' }
  return (
    <button onClick={onClick} style={{
      display:'inline-flex', alignItems:'center', justifyContent:'center', gap:6,
      border: variant === 'outline' ? '1.5px solid #3d8ef8' : 'none',
      cursor:'pointer', fontFamily:'var(--font-body)', fontWeight:500,
      borderRadius: pill ? 999 : 10, transition:'all .14s',
      background: bg[variant], color: color[variant],
      padding: pad[size], fontSize: fs[size], whiteSpace:'nowrap',
      ...style
    }}
    onMouseEnter={e => { (e.currentTarget as HTMLButtonElement).style.opacity = '.85' }}
    onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.opacity = '1' }}
    onMouseDown={e => { (e.currentTarget as HTMLButtonElement).style.transform = 'scale(.97)' }}
    onMouseUp={e => { (e.currentTarget as HTMLButtonElement).style.transform = 'scale(1)' }}
    >
      {children}
    </button>
  )
}

// ── Tag Component ──────────────────────────────────
function Tag({ children, variant = 'neutral' }: {
  children: React.ReactNode; variant?: 'buy'|'sell'|'hold'|'avoid'|'info'|'neutral'
}) {
  const styles: Record<string, React.CSSProperties> = {
    buy:     { background:'rgba(34,197,94,.1)',    color:'#22c55e', border:'1px solid rgba(34,197,94,.2)' },
    sell:    { background:'rgba(239,68,68,.1)',    color:'#ef4444', border:'1px solid rgba(239,68,68,.2)' },
    hold:    { background:'rgba(245,158,11,.1)',   color:'#f59e0b', border:'1px solid rgba(245,158,11,.2)' },
    avoid:   { background:'rgba(239,68,68,.06)',   color:'#f87171', border:'1px solid rgba(239,68,68,.15)' },
    info:    { background:'rgba(61,142,248,.12)',  color:'#3d8ef8', border:'1px solid rgba(61,142,248,.2)' },
    neutral: { background:'rgba(255,255,255,.04)', color:'var(--text-2)', border:'1px solid var(--border-std)' },
  }
  return (
    <span style={{
      display:'inline-flex', alignItems:'center', gap:4,
      fontSize:10, fontWeight:600, fontFamily:'var(--font-head)',
      padding:'3px 8px', borderRadius:999, whiteSpace:'nowrap',
      ...styles[variant]
    }}>{children}</span>
  )
}

// ── Score Bar ──────────────────────────────────────
function ScoreBar({ score }: { score: number }) {
  const color = score >= 75 ? '#22c55e' : score >= 55 ? '#f59e0b' : '#ef4444'
  return (
    <div style={{ display:'flex', alignItems:'center', gap:8 }}>
      <div style={{ flex:1, height:4, background:'var(--border-std)', borderRadius:2, overflow:'hidden' }}>
        <div style={{ width:`${score}%`, height:'100%', background:color, borderRadius:2, transition:'width .7s ease' }} />
      </div>
      <span style={{ fontFamily:'var(--font-num)', fontSize:11, fontWeight:500, color, width:32, textAlign:'right' }}>{score}</span>
    </div>
  )
}

// ── Detail Panel ───────────────────────────────────
interface DetailData {
  t: string
  k: { l: string; v: string; h: string }[]
  s: { c: string; t: string }[]
  buy: boolean
  p: string
}

const DETAILS: Record<string, DetailData> = {
  msft: { t:'Microsoft MSFT', buy:true, p:'Erstelle MSFT Trade-Plan für CHF 284k Portfolio',
    k:[{l:'Kurs',v:'USD 371.04',h:'−0.46% heute'},{l:'Score',v:'80/100',h:'Kaufen'},{l:'CRV',v:'1 : 2.8',h:'Ziel $445'},{l:'Stop-Loss',v:'$344',h:'−7.3%'},{l:'P/E fwd',v:'22.3x',h:'Mehrjahrestief'},{l:'Azure YoY',v:'+29%',h:'Q2 2026'}],
    s:[{c:'#22c55e',t:'Fundamentals intakt trotz −33% Korrektur — Markt übertreibt'},{c:'#22c55e',t:'CEO Nadella Score 91/100 — Track Record exzellent seit 2014'},{c:'#f59e0b',t:'Makrodruck kurzfristig — gestaffelter Einstieg empfohlen'}] },
  nvda: { t:'NVIDIA NVDA', buy:true, p:'Erstelle NVDA Kaufplan für CHF-Portfolio',
    k:[{l:'Kurs',v:'USD 879.50',h:'▲ +2.43%'},{l:'Score',v:'85/100',h:'Kaufen'},{l:'CRV',v:'1 : 3.1',h:'Sehr attraktiv'},{l:'Datacenter',v:'+122% YoY',h:'AI-Boom'},{l:'P/E fwd',v:'28.4x',h:'AI-Premium'},{l:'Stop',v:'$798',h:'−9.3%'}],
    s:[{c:'#22c55e',t:'Stärkste AI-Infrastrukturposition weltweit — strukturelles Wachstum'},{c:'#22c55e',t:'Broadcom + Nokia 6G Partnerschaft = neue Umsatzquellen 2026/27'},{c:'#f59e0b',t:'Bewertung erfordert perfekte Execution — Enttäuschungsrisiko beachten'}] },
  novn: { t:'Novartis NOVN', buy:true, p:'Analysiere Novartis für CHF-Portfolio',
    k:[{l:'Kurs',v:'CHF 92.40',h:'▲ +0.81%'},{l:'Score',v:'75/100',h:'Kaufen'},{l:'Dividende',v:'3.2%',h:'15J Wachstum'},{l:'P/E fwd',v:'14.2x',h:'Günstig'},{l:'Währung',v:'CHF',h:'Kein FX-Risiko'},{l:'Sektor',v:'Defensiv',h:'Ideal jetzt'}],
    s:[{c:'#22c55e',t:'Defensiver Safe-Haven — ideal in aktueller NFP-Schock Korrekturphase'},{c:'#22c55e',t:'CHF-Titel: Kein Währungsrisiko für Schweizer Anleger'},{c:'#f59e0b',t:'US-Pharma-Preisregulierung als Risiko mittelfristig beobachten'}] },
  tsla: { t:'Tesla TSLA — Meiden', buy:false, p:'Erkläre warum Tesla kein gutes Investment ist',
    k:[{l:'Kurs',v:'USD 248.10',h:'▼ −2.40%'},{l:'Score',v:'58/100',h:'Meiden'},{l:'P/E fwd',v:'68x',h:'Massiv teuer'},{l:'YTD',v:'−22.4%',h:'Underperformer'},{l:'Marge',v:'mid-single%',h:'War 25%'},{l:'BYD',v:'Überholt',h:'EU + Asien'}],
    s:[{c:'#ef4444',t:'Score 58: Hohe Bewertung + sinkende Margen + CEO-Ablenkung'},{c:'#ef4444',t:'BYD überholt in Europa und Asien — Marktanteil strukturell rückläufig'},{c:'#f59e0b',t:'Energiesparte wächst, aber noch zu klein um EV-Schwäche zu kompensieren'}] },
  gold: { t:'Gold XAU/USD', buy:true, p:'Erstelle Kaufplan für Gold-ETF ZGLD',
    k:[{l:'Kurs',v:"$4'850",h:'−0.30%'},{l:'ATH Jan 26',v:"$5'598",h:'Stärkstes Jahr 1979'},{l:'Support',v:"$4'550",h:'200-Tage-Linie'},{l:'GLD Abfluss',v:'−$2.1 Mrd.',h:'Profit-Taking'},{l:'SLV Zufluss',v:'+$559 Mio.',h:'Rotation'},{l:'Ziel',v:"$5'800",h:'Mittelfristig'}],
    s:[{c:'#22c55e',t:'Trendstruktur intakt — über $4\'550 bleibt Ausblick bullisch'},{c:'#22c55e',t:'Iran + CHF Safe-Haven + Zentralbankkäufe = strukturelle Unterstützung'},{c:'#f59e0b',t:'Kurzfristige Konsolidierung möglich — gestaffelt einsteigen'}] },
  zinsen: { t:'Fed & Zinspolitik', buy:false, p:'Erkläre Fed-Dilemma und Auswirkungen auf CHF-Portfolio',
    k:[{l:'Fed Rate',v:'3.75%',h:'2. Pause'},{l:'10J Rendite',v:'4.15%',h:'Flache Kurve'},{l:'SNB',v:'0.50%',h:'Stabil'},{l:'PCE',v:'2.7%',h:'Über Ziel'},{l:'Nächste Senkung',v:'Jul 2026',h:'60%'},{l:'Stagflation',v:'Risiko Mittel',h:''}],
    s:[{c:'#ef4444',t:'Fed-Dilemma: Inflation 2.7% + NFP −92k = kein Spielraum'},{c:'#f59e0b',t:'Öl $99 heizt Inflation weiter an — Senkungen unwahrscheinlicher'},{c:'#22c55e',t:'Historisch: Zinspausen sind oft beste Einstiegszeitpunkte'}] },
  arbeitsmarkt: { t:'US-Arbeitsmarkt', buy:false, p:'Welche Positionen sind vom schwachen Arbeitsmarkt betroffen?',
    k:[{l:'NFP Feb',v:'−92\'000',h:'Schock'},{l:'Erwartet',v:'+60\'000',h:'Enttäuschung'},{l:'Arbeitslosigkeit',v:'4.4%',h:'Steigend'},{l:'Lohnwachstum',v:'3.6%',h:'Normalisiert'},{l:'Erstanträge',v:"199'000",h:'Stabil'},{l:'Rezessionsrisiko',v:'Mittel',h:''}],
    s:[{c:'#ef4444',t:'Stärkster Jobverlust seit 2020 — Rezessionsrisiko steigt'},{c:'#ef4444',t:'Zyklische Werte meiden: Retail, Automotive, Transport'},{c:'#22c55e',t:'Defensiv aufstocken: NOVN, Versorger, Basiskonsumgüter'}] },
  geopolitik: { t:'Geopolitik-Radar', buy:false, p:'Analysiere Geopolitik-Risiken und schlage Absicherung vor',
    k:[{l:'Iran-Konflikt',v:'Woche 4',h:'Hormuz'},{l:'Öl WTI',v:'$99.40',h:'+40% seit Start'},{l:'US-China',v:'Mittel',h:'Halbleiter'},{l:'SECO CH',v:'Tief',h:'Kein Alarm'},{l:'NATO',v:'Stufe 2',h:'Rüstung ↑'},{l:'Ceasefire',v:'Außer Reichweite',h:''}],
    s:[{c:'#22c55e',t:'Energie-Profiteure: XOM, CVX, Shell, TotalEnergies massiv stark'},{c:'#22c55e',t:'Waffenstillstand würde Tech-Rallye +5–10% über Nacht auslösen'},{c:'#f59e0b',t:'Halbleiter: US-Exportkontrollen betreffen NVDA, ASML — prüfen'}] },
}

// ── Main App ───────────────────────────────────────
export default function App() {
  const [page, setPage] = useState<Page>('home')
  const [hmView, setHmView] = useState<HmView>('sec')
  const [hmTime, setHmTime] = useState<HmTime>('1d')
  const [detailId, setDetailId] = useState<string | null>(null)
  const [tradeModal, setTradeModal] = useState(false)
  const [tradeSym, setTradeSym] = useState('MSFT')
  const [isDark, setIsDark] = useState(true)
  const portChartRef = useRef<HTMLCanvasElement>(null)
  const allocChartRef = useRef<HTMLCanvasElement>(null)
  const portChartInst = useRef<Chart | null>(null)
  const allocChartInst = useRef<Chart | null>(null)

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light')
  }, [isDark])

  useEffect(() => {
    if (page === 'portfolio') {
      setTimeout(() => {
        if (portChartRef.current && !portChartInst.current) {
          portChartInst.current = new Chart(portChartRef.current, {
            type: 'line',
            data: {
              labels: ['Apr','Mai','Jun','Jul','Aug','Sep','Okt','Nov','Dez','Jan','Feb','Mär'],
              datasets: [
                { label:'Portfolio', data:[248000,254000,268000,291000,274000,280000,264000,296000,278000,286000,292000,284620], borderColor:'#3d8ef8', borderWidth:2, pointRadius:0, tension:.3, fill:true, backgroundColor:'rgba(61,142,248,0.06)' },
                { label:'SMI', data:[260000,262000,270000,278000,275000,279000,282000,289000,286000,284000,286000,285000], borderColor:'rgba(255,255,255,0.2)', borderWidth:1.5, pointRadius:0, tension:.3, fill:false, borderDash:[4,3] },
              ]
            },
            options: { responsive:true, maintainAspectRatio:false, plugins:{ legend:{ display:false } }, scales:{ x:{ grid:{ display:false }, ticks:{ color:'#4e5a6e', font:{size:10} } }, y:{ grid:{ color:'rgba(255,255,255,0.04)' }, ticks:{ color:'#4e5a6e', font:{size:10}, callback:(v:any)=>'CHF '+Math.round(v/1000)+'k' } } } }
          })
        }
        if (allocChartRef.current && !allocChartInst.current) {
          allocChartInst.current = new Chart(allocChartRef.current, {
            type: 'doughnut',
            data: {
              labels:['NVDA','MSFT','NOVN','ZGLD','Cash'],
              datasets:[{ data:[52100,48240,38800,32400,113080], backgroundColor:['#16a34a','#3d8ef8','#22d3ee','#f59e0b','#374151'], borderWidth:0 }]
            },
            options:{ responsive:true, maintainAspectRatio:false, cutout:'68%', plugins:{ legend:{ display:true, position:'right', labels:{ color:'#8b95a8', font:{size:10}, boxWidth:10 } } } }
          })
        }
      }, 100)
    }
    return () => {
      if (page !== 'portfolio') {
        portChartInst.current?.destroy(); portChartInst.current = null
        allocChartInst.current?.destroy(); allocChartInst.current = null
      }
    }
  }, [page])

  const detail = detailId ? DETAILS[detailId] : null

  const navStyle = (p: Page): React.CSSProperties => ({
    display:'flex', alignItems:'center', gap:6, padding:'11px 14px',
    fontSize:12, fontWeight:500, fontFamily:'var(--font-head)',
    color: page === p ? 'var(--accent)' : 'var(--text-3)',
    borderBottom: page === p ? '2px solid var(--accent)' : '2px solid transparent',
    cursor:'pointer', whiteSpace:'nowrap', transition:'all var(--trans)',
  })

  const ctrlBtn = (active: boolean): React.CSSProperties => ({
    fontSize:10, padding:'4px 10px', borderRadius:999, cursor:'pointer',
    fontFamily:'var(--font-body)', fontWeight:500, border:'none', transition:'all .14s',
    background: active ? 'var(--accent)' : 'var(--bg-elevated)',
    color: active ? '#fff' : 'var(--text-2)',
  })

  // ── Render ──────────────────────────────────────
  return (
    <div style={{ display:'flex', flexDirection:'column', height:'100vh', overflow:'hidden', background:'var(--bg-base)' }}>

      {/* ── TopBar ── */}
      <header style={{ display:'flex', alignItems:'center', justifyContent:'space-between', padding:'0 20px', height:56, background:'var(--bg-surface)', borderBottom:'1px solid var(--border-std)', flexShrink:0, zIndex:100 }}>
        <div style={{ display:'flex', alignItems:'center', gap:10 }}>
          <div style={{ width:34, height:34, background:'linear-gradient(135deg,#1d4ed8,#3d8ef8)', borderRadius:10, display:'flex', alignItems:'center', justifyContent:'center', boxShadow:'0 0 12px rgba(61,142,248,.3)' }}>
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
              <path d="M3 13L7.5 7.5L11 10.5L15 4" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <circle cx="15" cy="4" r="1.8" fill="white"/>
            </svg>
          </div>
          <span style={{ fontFamily:'var(--font-head)', fontSize:17, fontWeight:700, color:'var(--text-1)', letterSpacing:'-.01em' }}>TradeApp</span>
          <div style={{ display:'flex', alignItems:'center', gap:5, fontSize:11, color:'var(--text-3)', padding:'3px 8px', background:'var(--bg-elevated)', borderRadius:999, border:'1px solid var(--border-dim)' }}>
            <span style={{ width:6, height:6, borderRadius:'50%', background:'var(--green)', animation:'pulse 1.6s infinite', display:'inline-block' }}/>
            Live · 27 Mär 2026
          </div>
        </div>

        <div style={{ display:'flex', alignItems:'center', gap:10 }}>
          <div onClick={() => setDetailId('portfolio-overview')} style={{ background:'var(--bg-elevated)', border:'1px solid var(--border-std)', borderRadius:10, padding:'8px 14px', textAlign:'right', cursor:'pointer' }}>
            <div style={{ fontFamily:'var(--font-num)', fontSize:18, fontWeight:500, color:'var(--text-1)' }}>CHF 284'620</div>
            <div style={{ fontSize:11, color:'var(--green)', marginTop:1 }}>▲ +1'240 (+0.44%) heute</div>
          </div>
          <button onClick={() => setIsDark(!isDark)} style={{ width:36, height:36, display:'flex', alignItems:'center', justifyContent:'center', background:'var(--bg-elevated)', border:'1px solid var(--border-std)', borderRadius:10, cursor:'pointer', color:'var(--text-2)' }}>
            {isDark ? '☀' : '🌙'}
          </button>
          <Btn variant="buy" size="lg" pill onClick={() => { setTradeSym('MSFT'); setTradeModal(true) }}>
            + Trade
          </Btn>
        </div>
      </header>

      {/* ── Alert Strip ── */}
      <div style={{ display:'flex', alignItems:'center', background:'var(--bg-surface)', borderBottom:'1px solid var(--border-std)', overflowX:'auto', flexShrink:0 }}>
        {[
          { dot:'#ef4444', text:'Iran · Öl $99.40', id:'geopolitik' },
          { dot:'#ef4444', text:'NFP −92k · Rezessionsrisiko', id:'arbeitsmarkt' },
          { dot:'#f59e0b', text:'Fed 3.75% · Pause', id:'zinsen' },
          { dot:'#22c55e', text:'MSFT Score 80 · Kaufsignal', id:'msft' },
        ].map((a, i) => (
          <div key={i} onClick={() => setDetailId(a.id)} style={{ display:'flex', alignItems:'center', gap:6, padding:'7px 16px', fontSize:11, color:'var(--text-2)', borderRight:'1px solid var(--border-dim)', cursor:'pointer', whiteSpace:'nowrap', flexShrink:0, transition:'background var(--trans)' }}
            onMouseEnter={e => (e.currentTarget.style.background = 'var(--bg-hover)')}
            onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
          >
            <span style={{ width:5, height:5, borderRadius:'50%', background:a.dot, flexShrink:0, display:'inline-block' }}/>
            {a.text}
          </div>
        ))}
        <div style={{ marginLeft:'auto', padding:'0 12px', flexShrink:0 }}>
          <Btn variant="ghost" size="xs" pill onClick={() => setDetailId('alerts')}>Alle →</Btn>
        </div>
      </div>

      {/* ── Nav Tabs ── */}
      <nav style={{ display:'flex', background:'var(--bg-surface)', borderBottom:'1px solid var(--border-std)', padding:'0 16px', flexShrink:0, overflowX:'auto' }}>
        {(['home','heatmap','signals','portfolio','macro','journal'] as Page[]).map(p => (
          <div key={p} onClick={() => setPage(p)} style={navStyle(p)}>
            {p === 'home' && '○'} {p === 'heatmap' && '▦'} {p === 'signals' && '◎'}
            {p === 'portfolio' && '◈'} {p === 'macro' && '◇'} {p === 'journal' && '≡'}
            {p.charAt(0).toUpperCase() + p.slice(1)}
          </div>
        ))}
      </nav>

      {/* ── Pulse Strip ── */}
      <div style={{ display:'grid', gridTemplateColumns:'repeat(8,minmax(0,1fr))', background:'var(--bg-surface)', borderBottom:'1px solid var(--border-std)', flexShrink:0 }}>
        {INDICES.map(idx => (
          <div key={idx.id} onClick={() => setDetailId(idx.id)} style={{ padding:'9px 14px', cursor:'pointer', borderRight:'1px solid var(--border-dim)', transition:'background var(--trans)' }}
            onMouseEnter={e => (e.currentTarget.style.background = 'var(--bg-hover)')}
            onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
          >
            <div style={{ fontSize:9, fontWeight:600, fontFamily:'var(--font-head)', letterSpacing:'.06em', textTransform:'uppercase', color:'var(--text-3)', marginBottom:3 }}>{idx.label}</div>
            <div style={{ fontFamily:'var(--font-num)', fontSize:13, fontWeight:500, color:'var(--text-1)' }}>{idx.value}</div>
            <div style={{ fontSize:10, fontFamily:'var(--font-num)', color: idx.chg > 0 ? 'var(--green)' : idx.chg < 0 ? 'var(--red)' : 'var(--text-3)', marginTop:2 }}>
              {idx.chg > 0 ? '▲' : idx.chg < 0 ? '▼' : '→'} {idx.chg > 0 ? '+' : ''}{idx.chg.toFixed(2)}%
            </div>
          </div>
        ))}
      </div>

      {/* ── Main Content ── */}
      <div style={{ flex:1, overflow:'hidden', display:'flex', position:'relative' }}>

        {/* ── HOME ── */}
        {page === 'home' && (
          <div style={{ display:'grid', gridTemplateColumns:'1fr 300px', flex:1, overflow:'hidden' }}>

            {/* Left */}
            <div style={{ overflowY:'auto', borderRight:'1px solid var(--border-std)' }}>

              {/* Sentiment */}
              <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', padding:'12px 16px 8px' }}>
                <span className="label-caps">Marktlage</span>
                <Btn variant="ghost" size="xs" pill onClick={() => setDetailId('sentiment')}>Details →</Btn>
              </div>
              <div style={{ display:'grid', gridTemplateColumns:'repeat(4,minmax(0,1fr))', gap:8, padding:'0 16px 12px', borderBottom:'1px solid var(--border-dim)' }} className="stagger">
                {[
                  { label:'Fear & Greed', value:'32', sub:'Angst-Zone', tag:'info' as const, tagText:'Hist. Kaufsignal', id:'sentiment', color:'var(--red)' },
                  { label:'Fed Rate', value:'3.75%', sub:'Pause · 2. Sitzung', tag:'hold' as const, tagText:'Nächste: Jul 26', id:'zinsen', color:'var(--text-1)' },
                  { label:'NFP Februar', value:'−92k', sub:'Erw. +60k', tag:'sell' as const, tagText:'Rezessionsrisiko', id:'arbeitsmarkt', color:'var(--red)' },
                  { label:'Marktphase', value:'Korrektur', sub:'Tech −12% YTD', tag:'hold' as const, tagText:'Defensiv posit.', id:'marktphase', color:'var(--amber)' },
                ].map((item, i) => (
                  <div key={i} onClick={() => setDetailId(item.id)} style={{ background:'var(--bg-elevated)', border:'1px solid var(--border-std)', borderRadius:14, padding:'12px 14px', cursor:'pointer', transition:'all var(--trans)' }}
                    onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--border-bold)'; e.currentTarget.style.background = 'var(--bg-hover)' }}
                    onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border-std)'; e.currentTarget.style.background = 'var(--bg-elevated)' }}
                  >
                    <div className="label-caps" style={{ marginBottom:5 }}>{item.label}</div>
                    <div style={{ fontFamily:'var(--font-num)', fontSize: item.value.length > 6 ? 15 : 20, fontWeight:500, color:item.color }}>{item.value}</div>
                    <div style={{ fontSize:10, color:'var(--text-3)', marginTop:2 }}>{item.sub}</div>
                    <div style={{ marginTop:7 }}><Tag variant={item.tag}>{item.tagText}</Tag></div>
                  </div>
                ))}
              </div>

              {/* Mini Heatmap */}
              <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', padding:'12px 16px 8px' }}>
                <span className="label-caps">Sektor-Heatmap</span>
                <Btn variant="ghost" size="xs" pill onClick={() => setPage('heatmap')}>Vollbild →</Btn>
              </div>
              <div style={{ padding:'0 16px 12px', borderBottom:'1px solid var(--border-dim)' }}>
                <Treemap data={SECTORS} time={hmTime} mini onItem={setDetailId} onStock={setDetailId} />
              </div>

              {/* Briefing */}
              <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', padding:'12px 16px 8px' }}>
                <span className="label-caps">KI-Tagesbriefing</span>
                <span style={{ fontSize:9, fontFamily:'var(--font-head)', fontWeight:600, letterSpacing:'.06em', color:'var(--accent)', background:'var(--accent-dim)', padding:'3px 8px', borderRadius:999 }}>27 Mär · 15:42</span>
              </div>
              <div style={{ padding:'0 16px 12px', borderBottom:'1px solid var(--border-dim)' }} className="stagger">
                {[
                  { dot:'var(--red)',   text:'Energie profitiert massiv', sub:'Öl $99 durch Iran-Krieg. XOM, CVX, Shell stark. Airlines leiden.', id:'geopolitik' },
                  { dot:'var(--green)', text:'MSFT Kaufsignal', sub:'Score 80/100, −33% vom ATH, Fundamentals intakt. Azure +29% YoY ignoriert.', id:'msft' },
                  { dot:'var(--red)',   text:'NFP −92k Schock', sub:'Defensiv positionieren. Zykliker reduzieren. NOVN, Versorger als Schutz.', id:'arbeitsmarkt' },
                  { dot:'var(--amber)', text:'Gold-Konsolidierung', sub:'$4\'850, Support $4\'550 intakt. GLD Abfluss = Profit-Taking, kein Trendbruch.', id:'gold' },
                  { dot:'var(--green)', text:'Fear & Greed 32', sub:'Historisch: Unter 35 = immer starke Einstiegspunkte für Qualitätsaktien.', id:'sentiment' },
                ].map((b, i) => (
                  <div key={i} onClick={() => setDetailId(b.id)} style={{ display:'flex', alignItems:'flex-start', gap:10, padding:'8px 10px', borderRadius:10, cursor:'pointer', marginBottom:2, transition:'background var(--trans)' }}
                    onMouseEnter={e => (e.currentTarget.style.background = 'var(--bg-hover)')}
                    onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
                  >
                    <span style={{ width:7, height:7, borderRadius:'50%', background:b.dot, flexShrink:0, marginTop:4, display:'inline-block' }}/>
                    <div style={{ flex:1, fontSize:11, color:'var(--text-2)', lineHeight:1.5 }}>
                      <b style={{ color:'var(--text-1)', fontWeight:500 }}>{b.text}</b> — {b.sub}
                    </div>
                    <span style={{ fontSize:12, color:'var(--text-3)' }}>›</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Right */}
            <div style={{ overflowY:'auto', display:'flex', flexDirection:'column' }}>

              {/* Signals */}
              <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', padding:'12px 12px 8px' }}>
                <span className="label-caps">Top-Signale</span>
                <Btn variant="ghost" size="xs" pill onClick={() => setPage('signals')}>Alle →</Btn>
              </div>
              <div style={{ display:'flex', flexDirection:'column', gap:5, padding:'0 12px 12px' }} className="stagger">
                {[
                  { sym:'NVDA', tag:'buy' as const, price:'$879', info:'CRV 1:3.1', score:85 },
                  { sym:'MSFT', tag:'buy' as const, price:'$371', info:'CRV 1:2.8', score:80 },
                  { sym:'NOVN', tag:'buy' as const, price:'CHF 92', info:'Div. 3.2%', score:75 },
                  { sym:'TSLA', tag:'avoid' as const, price:'$248', info:'P/E 68x', score:58 },
                ].map((s, i) => (
                  <div key={i} onClick={() => setDetailId(s.sym.toLowerCase())} style={{ display:'flex', alignItems:'center', gap:10, padding:'10px 12px', borderRadius:14, background:'var(--bg-elevated)', border:'1px solid var(--border-std)', cursor:'pointer', transition:'all var(--trans)' }}
                    onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--border-bold)'; e.currentTarget.style.background = 'var(--bg-hover)' }}
                    onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border-std)'; e.currentTarget.style.background = 'var(--bg-elevated)' }}
                  >
                    <span style={{ fontFamily:'var(--font-head)', fontSize:14, fontWeight:800, color:'var(--text-1)', width:48, flexShrink:0 }}>{s.sym}</span>
                    <div style={{ flex:1, minWidth:0 }}>
                      <div style={{ display:'flex', alignItems:'center', gap:6, marginBottom:5 }}>
                        <Tag variant={s.tag}>{s.tag === 'buy' ? 'Kaufen' : 'Meiden'}</Tag>
                        <span style={{ fontFamily:'var(--font-num)', fontSize:11, color:'var(--text-3)' }}>{s.price} · {s.info}</span>
                      </div>
                      <ScoreBar score={s.score} />
                    </div>
                    {s.tag === 'buy' && (
                      <Btn variant="buy" size="xs" pill onClick={e => { e.stopPropagation(); setTradeSym(s.sym); setTradeModal(true) }}>Kaufen</Btn>
                    )}
                  </div>
                ))}
              </div>

              <div style={{ height:1, background:'var(--border-dim)', margin:'2px 12px' }}/>

              {/* Portfolio Mini */}
              <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', padding:'10px 12px 8px' }}>
                <span className="label-caps">Portfolio</span>
                <Btn variant="ghost" size="xs" pill onClick={() => setPage('portfolio')}>Alle →</Btn>
              </div>
              <div style={{ padding:'0 12px 12px', display:'flex', flexDirection:'column', gap:1 }} className="stagger">
                {[
                  { sym:'NVDA', name:'NVIDIA · 18.3%', val:"52'100", pnl:'+12.1%', up:true, bar:100 },
                  { sym:'MSFT', name:'Microsoft · 17.0%', val:"48'240", pnl:'−8.4%', up:false, bar:83 },
                  { sym:'NOVN', name:'Novartis · 13.6%', val:"38'800", pnl:'+4.2%', up:true, bar:66 },
                  { sym:'ZGLD', name:'Gold ETF · 11.4%', val:"32'400", pnl:'+18.4%', up:true, bar:55 },
                  { sym:'Cash', name:'Liquidität · 39.7%', val:"113'080", pnl:'—', up:null, bar:39 },
                ].map((p, i) => (
                  <div key={i} onClick={() => p.sym !== 'Cash' && setDetailId(p.sym.toLowerCase())} style={{ display:'flex', alignItems:'center', gap:8, padding:'8px 10px', borderRadius:10, cursor: p.sym !== 'Cash' ? 'pointer' : 'default', transition:'background var(--trans)' }}
                    onMouseEnter={e => { if (p.sym !== 'Cash') e.currentTarget.style.background = 'var(--bg-hover)' }}
                    onMouseLeave={e => { e.currentTarget.style.background = 'transparent' }}
                  >
                    <span style={{ fontFamily:'var(--font-head)', fontSize:13, fontWeight:800, color: p.sym === 'Cash' ? 'var(--text-3)' : 'var(--text-1)', width:50, flexShrink:0 }}>{p.sym}</span>
                    <div style={{ flex:1, minWidth:0 }}>
                      <div style={{ fontSize:10, color:'var(--text-3)', marginBottom:4, overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>{p.name}</div>
                      <div style={{ height:3, borderRadius:2, background:'var(--border-std)', overflow:'hidden' }}>
                        <div style={{ width:`${p.bar}%`, height:'100%', borderRadius:2, background: p.up === null ? 'var(--accent)' : p.up ? 'var(--green)' : 'var(--red)' }}/>
                      </div>
                    </div>
                    <div style={{ textAlign:'right', flexShrink:0 }}>
                      <div style={{ fontFamily:'var(--font-num)', fontSize:12, fontWeight:500, color:'var(--text-1)' }}>CHF {p.val}</div>
                      <div style={{ fontFamily:'var(--font-num)', fontSize:10, color: p.up === null ? 'var(--text-3)' : p.up ? 'var(--green)' : 'var(--red)' }}>{p.pnl}</div>
                    </div>
                  </div>
                ))}
              </div>

              <div style={{ height:1, background:'var(--border-dim)', margin:'2px 12px' }}/>

              {/* Makro Mini */}
              <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', padding:'10px 12px 8px' }}>
                <span className="label-caps">Makro-Radar</span>
                <Btn variant="ghost" size="xs" pill onClick={() => setPage('macro')}>Alle →</Btn>
              </div>
              <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:5, padding:'0 12px 12px' }} className="stagger">
                {[
                  { l:'Inflation PCE', v:'2.7%', s:'Über 2%-Ziel', c:'var(--amber)', id:'inflation' },
                  { l:'Fed Rate',      v:'3.75%', s:'Pause',        c:'var(--text-1)', id:'zinsen' },
                  { l:'Gold',          v:"$4'850", s:'Konsolidierung', c:'var(--amber)', id:'gold' },
                  { l:'Öl WTI',        v:'$99.40', s:'Iran-Risiko',  c:'var(--red)', id:'oel' },
                ].map((m, i) => (
                  <div key={i} onClick={() => setDetailId(m.id)} style={{ background:'var(--bg-elevated)', border:'1px solid var(--border-std)', borderRadius:10, padding:'9px 11px', cursor:'pointer', transition:'all var(--trans)' }}
                    onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--border-bold)'}
                    onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border-std)'}
                  >
                    <div className="label-caps" style={{ marginBottom:3 }}>{m.l}</div>
                    <div style={{ fontFamily:'var(--font-num)', fontSize:15, fontWeight:500, color:m.c }}>{m.v}</div>
                    <div style={{ fontSize:10, color:'var(--text-3)', marginTop:1 }}>{m.s}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ── HEATMAP ── */}
        {page === 'heatmap' && (
          <div style={{ flex:1, display:'flex', flexDirection:'column', overflow:'hidden' }}>
            <div style={{ display:'flex', alignItems:'center', gap:8, padding:'10px 16px', borderBottom:'1px solid var(--border-std)', background:'var(--bg-surface)', flexWrap:'wrap' }}>
              <span className="label-caps" style={{ marginRight:4 }}>Ansicht</span>
              {(['sec','reg','cty','fx'] as HmView[]).map(v => (
                <button key={v} onClick={() => setHmView(v)} style={ctrlBtn(hmView === v)}>
                  {v === 'sec' ? 'Sektoren' : v === 'reg' ? 'Kontinente' : v === 'cty' ? 'Länder' : 'Währungen'}
                </button>
              ))}
              <div style={{ width:1, height:20, background:'var(--border-std)', margin:'0 4px' }}/>
              <span className="label-caps" style={{ marginRight:4 }}>Zeitraum</span>
              {(['1d','1w','1m','ytd'] as HmTime[]).map(t => (
                <button key={t} onClick={() => setHmTime(t)} style={ctrlBtn(hmTime === t)}>
                  {t === '1d' ? '1T' : t === '1w' ? '1W' : t === '1m' ? '1M' : 'YTD'}
                </button>
              ))}
            </div>
            <div style={{ flex:1, padding:'12px 16px', overflowY:'auto' }}>
              <Treemap data={HM_DATA[hmView]} time={hmTime} onItem={setDetailId} onStock={setDetailId} />
            </div>
            <div style={{ display:'flex', alignItems:'center', gap:5, padding:'4px 16px 8px', flexWrap:'wrap', fontSize:10, color:'var(--text-3)' }}>
              Legende:
              {['#450a0a','#991b1b','#dc2626','#f87171'].map(c => <span key={c} style={{ width:14, height:7, borderRadius:2, background:c, display:'inline-block' }}/>)}
              negativ
              <span style={{ width:14, height:7, borderRadius:2, background:'#374151', display:'inline-block', margin:'0 3px' }}/>
              neutral
              {['#4ade80','#16a34a','#15803d','#14532d'].map(c => <span key={c} style={{ width:14, height:7, borderRadius:2, background:c, display:'inline-block' }}/>)}
              positiv · Klick = Detailanalyse
            </div>
          </div>
        )}

        {/* ── SIGNALS ── */}
        {page === 'signals' && (
          <div style={{ flex:1, overflowY:'auto', padding:16, display:'flex', flexDirection:'column', gap:12 }}>
            <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between' }}>
              <span className="label-caps">Kaufsignale — 27. März 2026</span>
              <Btn variant="ai" size="sm" onClick={() => alert('KI-Screener:\n\nIn der Prod-App: Claude API scannt 500+ Aktien nach Score >75 und CRV >1:2')}>KI-Screener ↗</Btn>
            </div>
            {[
              { sym:'NVDA', name:'NVIDIA Corporation',    score:85, price:'$879.50', stop:'$798',   target:"$1'050", crv:'3.1', color:'#1d4738', reasons:['Datacenter +122% YoY','RSI 58 nicht überkauft','AI-Infrastruktur Megatrend'] },
              { sym:'MSFT', name:'Microsoft Corporation', score:80, price:'$371.04', stop:'$344',   target:'$445',   crv:'2.8', color:'#163350', reasons:['Azure +29% YoY','−33% vom ATH','P/E 22.3x Mehrjahrestief'] },
              { sym:'NOVN', name:'Novartis AG',            score:75, price:'CHF 92', stop:'CHF 86', target:'CHF 104',crv:'1.8', color:'#1e3a1a', reasons:['Defensiv in Korrektur','Dividende 3.2%','Kein FX-Risiko für CHF'] },
              { sym:'XOM',  name:'ExxonMobil',             score:78, price:'$118.40',stop:'$108',   target:'$136',   crv:'1.7', color:'#2d1f0d', reasons:['Energie +33% YTD','Öl $99 Iran','FCF 8.4%'] },
            ].map((s, i) => (
              <div key={i} onClick={() => setDetailId(s.sym.toLowerCase())} style={{ background:'var(--bg-surface)', border:'1px solid var(--border-std)', borderRadius:20, padding:16, cursor:'pointer', transition:'all var(--trans)' }}
                onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--border-bold)'; e.currentTarget.style.background = 'var(--bg-elevated)' }}
                onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border-std)'; e.currentTarget.style.background = 'var(--bg-surface)' }}
              >
                <div style={{ display:'flex', alignItems:'flex-start', justifyContent:'space-between', marginBottom:12 }}>
                  <div style={{ display:'flex', alignItems:'center', gap:12 }}>
                    <div style={{ width:42, height:42, borderRadius:10, background:s.color, display:'flex', alignItems:'center', justifyContent:'center', fontFamily:'var(--font-head)', fontSize:14, fontWeight:800, color:'#fff' }}>{s.sym.substring(0,2)}</div>
                    <div>
                      <div style={{ fontFamily:'var(--font-head)', fontSize:18, fontWeight:800, color:'var(--text-1)' }}>{s.sym}</div>
                      <div style={{ fontSize:11, color:'var(--text-3)' }}>{s.name}</div>
                    </div>
                  </div>
                  <div style={{ display:'flex', alignItems:'center', gap:8 }}>
                    <Tag variant="buy">Kaufen</Tag>
                    <Btn variant="buy" size="md" pill onClick={e => { e.stopPropagation(); setTradeSym(s.sym); setTradeModal(true) }}>Kaufen</Btn>
                  </div>
                </div>
                <div style={{ display:'grid', gridTemplateColumns:'repeat(4,minmax(0,1fr))', gap:8, marginBottom:12 }}>
                  {[{l:'Kurs',v:s.price},{l:'Stop-Loss',v:s.stop,c:'var(--red)'},{l:'Kursziel',v:s.target,c:'var(--green)'},{l:'CRV',v:`1 : ${s.crv}`,c:'var(--green)'}].map((m,j) => (
                    <div key={j} style={{ background:'var(--bg-elevated)', borderRadius:10, padding:'8px 10px' }}>
                      <div className="label-caps" style={{ marginBottom:2 }}>{m.l}</div>
                      <div style={{ fontFamily:'var(--font-num)', fontSize:14, fontWeight:500, color:m.c || 'var(--text-1)' }}>{m.v}</div>
                    </div>
                  ))}
                </div>
                <div style={{ display:'flex', alignItems:'center', gap:8, marginBottom:10 }}>
                  <span className="label-caps" style={{ width:50, flexShrink:0 }}>Score</span>
                  <ScoreBar score={s.score} />
                </div>
                <div style={{ display:'flex', flexWrap:'wrap', gap:5 }}>
                  {s.reasons.map((r, j) => <span key={j} style={{ fontSize:10, color:'var(--text-3)', background:'var(--bg-elevated)', padding:'3px 8px', borderRadius:999, border:'1px solid var(--border-std)' }}>{r}</span>)}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* ── PORTFOLIO ── */}
        {page === 'portfolio' && (
          <div style={{ flex:1, overflowY:'auto', padding:16, display:'flex', flexDirection:'column', gap:12 }}>
            <div style={{ display:'grid', gridTemplateColumns:'repeat(4,minmax(0,1fr))', gap:8 }} className="stagger">
              {[{l:'Gesamtwert',v:"CHF 284'620",s:'▲ +1\'240 heute',c:'var(--green)'},{l:'YTD Performance',v:'−3.2%',s:'vs. SMI +2.1%',c:'var(--red)'},{l:'Portfolio-Score',v:'74/100',s:'Solide',c:'var(--green)'},{l:'Cash-Quote',v:'39.7%',s:"CHF 113'080",c:'var(--accent)'}].map((k,i)=>(
                <div key={i} style={{ background:'var(--bg-surface)', border:'1px solid var(--border-std)', borderRadius:14, padding:'14px 16px' }}>
                  <div className="label-caps" style={{ marginBottom:6 }}>{k.l}</div>
                  <div style={{ fontFamily:'var(--font-num)', fontSize:22, fontWeight:500, color:k.c }}>{k.v}</div>
                  <div style={{ fontSize:10, color:'var(--text-3)', marginTop:3 }}>{k.s}</div>
                </div>
              ))}
            </div>
            <div style={{ background:'var(--bg-surface)', border:'1px solid var(--border-std)', borderRadius:20, overflow:'hidden' }}>
              <div style={{ display:'grid', gridTemplateColumns:'60px 1fr 100px 100px 70px 60px 80px', padding:'10px 16px', background:'var(--bg-elevated)', borderBottom:'1px solid var(--border-std)', fontSize:9, fontWeight:600, fontFamily:'var(--font-head)', letterSpacing:'.07em', textTransform:'uppercase', color:'var(--text-3)' }}>
                <span>Titel</span><span>Name</span><span>Wert CHF</span><span>Kurs</span><span>G/V</span><span>Score</span><span>Aktion</span>
              </div>
              {[
                { sym:'NVDA', name:'NVIDIA Corp.',  sub:'18.3% · NASDAQ', val:"52'100", qty:'59 Stk.',  price:'$879.50', pchg:'+2.43%', up:true,  pnl:'+12.1%', score:85 },
                { sym:'MSFT', name:'Microsoft',     sub:'17.0% · NASDAQ', val:"48'240", qty:'130 Stk.', price:'$371.04', pchg:'−0.46%', up:false, pnl:'−8.4%',  score:80 },
                { sym:'NOVN', name:'Novartis AG',   sub:'13.6% · SIX',    val:"38'800", qty:'420 Stk.', price:'CHF 92',  pchg:'+0.81%', up:true,  pnl:'+4.2%',  score:75 },
                { sym:'ZGLD', name:'Gold ETF (ZGLD)',sub:'11.4% · SIX',   val:"32'400", qty:'68 Ant.',  price:'CHF 476', pchg:'−0.30%', up:false, pnl:'+18.4%', score:77 },
              ].map((p, i) => (
                <div key={i} onClick={() => setDetailId(p.sym.toLowerCase())} style={{ display:'grid', gridTemplateColumns:'60px 1fr 100px 100px 70px 60px 80px', padding:'12px 16px', borderBottom:'1px solid var(--border-dim)', cursor:'pointer', alignItems:'center', transition:'background var(--trans)' }}
                  onMouseEnter={e => (e.currentTarget.style.background = 'var(--bg-hover)')}
                  onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
                >
                  <span style={{ fontFamily:'var(--font-head)', fontSize:14, fontWeight:800, color:'var(--text-1)' }}>{p.sym}</span>
                  <div><div style={{ fontSize:11, color:'var(--text-2)' }}>{p.name}</div><div style={{ fontSize:10, color:'var(--text-3)' }}>{p.sub}</div></div>
                  <div><div style={{ fontFamily:'var(--font-num)', fontSize:12 }}>{p.val}</div><div style={{ fontFamily:'var(--font-num)', fontSize:10, color:'var(--text-3)' }}>{p.qty}</div></div>
                  <div><div style={{ fontFamily:'var(--font-num)', fontSize:12 }}>{p.price}</div><div style={{ fontFamily:'var(--font-num)', fontSize:10, color: p.up ? 'var(--green)' : 'var(--red)' }}>{p.pchg}</div></div>
                  <div style={{ fontFamily:'var(--font-num)', fontSize:12, color: p.pnl.startsWith('+') ? 'var(--green)' : 'var(--red)' }}>{p.pnl}</div>
                  <Tag variant="buy">{p.score}</Tag>
                  <Btn variant="ghost" size="xs" onClick={e => { e.stopPropagation(); setDetailId(p.sym.toLowerCase()) }}>Analyse</Btn>
                </div>
              ))}
            </div>
            <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:12 }}>
              <div style={{ background:'var(--bg-surface)', border:'1px solid var(--border-std)', borderRadius:20, padding:16 }}>
                <div className="label-caps" style={{ marginBottom:10 }}>Portfolio-Entwicklung (12 Monate)</div>
                <div style={{ position:'relative', height:160 }}><canvas ref={portChartRef}/></div>
              </div>
              <div style={{ background:'var(--bg-surface)', border:'1px solid var(--border-std)', borderRadius:20, padding:16 }}>
                <div className="label-caps" style={{ marginBottom:10 }}>Sektor-Allokation</div>
                <div style={{ position:'relative', height:160 }}><canvas ref={allocChartRef}/></div>
              </div>
            </div>
            <div style={{ display:'flex', gap:8 }}>
              <Btn variant="primary" size="lg" style={{ flex:1, justifyContent:'center' }} onClick={() => alert('Rebalancing-Plan:\n\nEmpfehlung: MSFT +5%, NVDA +3%, Cash −8%\n\nIn Prod-App: Claude API erstellt vollständigen Plan')}>Portfolio optimieren ↗</Btn>
              <Btn variant="ghost" size="lg" style={{ flex:1, justifyContent:'center' }} onClick={() => alert('Steuer-Report CH:\n\nStempelsteuer: CHF 89.40\nVerrechnungssteuer: CHF 840\nVermögenssteuerwert: CHF 284\'620')}>Steuer-Report (CH)</Btn>
            </div>
          </div>
        )}

        {/* ── MACRO ── */}
        {page === 'macro' && (
          <div style={{ flex:1, overflowY:'auto', padding:16, display:'flex', flexDirection:'column', gap:14 }}>
            <div>
              <div className="label-caps" style={{ marginBottom:8 }}>Zentralbanken</div>
              <div style={{ display:'grid', gridTemplateColumns:'repeat(4,minmax(0,1fr))', gap:8 }} className="stagger">
                {[{l:'Fed · USA',v:'3.75%',s:'Pause',tag:'hold',id:'zinsen'},{l:'SNB · CH',v:'0.50%',s:'Stabil',tag:'info',id:'snb'},{l:'EZB · EU',v:'2.40%',s:'Senkung mögl.',tag:'buy',id:'ezb'},{l:'BoJ · JP',v:'0.50%',s:'Normalisierung',tag:'hold',id:'boj'}].map((m,i)=>(
                  <div key={i} onClick={() => setDetailId(m.id)} style={{ background:'var(--bg-surface)', border:'1px solid var(--border-std)', borderRadius:20, padding:'14px 16px', cursor:'pointer', transition:'all var(--trans)' }}
                    onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--border-bold)'; e.currentTarget.style.background = 'var(--bg-elevated)' }}
                    onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border-std)'; e.currentTarget.style.background = 'var(--bg-surface)' }}
                  >
                    <div className="label-caps" style={{ marginBottom:6 }}>{m.l}</div>
                    <div style={{ fontFamily:'var(--font-num)', fontSize:20, fontWeight:500, color:'var(--text-1)' }}>{m.v}</div>
                    <div style={{ fontSize:10, color:'var(--text-3)', marginTop:2 }}>{m.s}</div>
                    <div style={{ marginTop:8 }}><Tag variant={m.tag as any}>{m.s}</Tag></div>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <div className="label-caps" style={{ marginBottom:8 }}>Konjunktur & Märkte</div>
              <div style={{ display:'grid', gridTemplateColumns:'repeat(4,minmax(0,1fr))', gap:8 }} className="stagger">
                {[{l:'CPI USA',v:'2.4%',s:'Über Ziel',c:'var(--amber)',id:'inflation'},{l:'NFP Feb',v:'−92k',s:'Schock',c:'var(--red)',id:'arbeitsmarkt'},{l:'10J Rendite',v:'4.15%',s:'Flach',c:'var(--text-1)',id:'zinsen'},{l:'Öl WTI',v:'$99.40',s:'Iran-Effekt',c:'var(--red)',id:'oel'},{l:'Gold XAU',v:"$4'850",s:'Konsolidierung',c:'var(--amber)',id:'gold'},{l:'Fear&Greed',v:'32',s:'Angst-Zone',c:'var(--red)',id:'sentiment'},{l:'EUR/CHF',v:'0.937',s:'Safe-Haven',c:'var(--text-1)',id:'eurchf'},{l:'VIX',v:'24.5',s:'Erhöht',c:'var(--amber)',id:'vix'}].map((m,i)=>(
                  <div key={i} onClick={() => setDetailId(m.id)} style={{ background:'var(--bg-surface)', border:'1px solid var(--border-std)', borderRadius:20, padding:'14px 16px', cursor:'pointer', transition:'all var(--trans)' }}
                    onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--border-bold)'; e.currentTarget.style.background = 'var(--bg-elevated)' }}
                    onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border-std)'; e.currentTarget.style.background = 'var(--bg-surface)' }}
                  >
                    <div className="label-caps" style={{ marginBottom:6 }}>{m.l}</div>
                    <div style={{ fontFamily:'var(--font-num)', fontSize:20, fontWeight:500, color:m.c }}>{m.v}</div>
                    <div style={{ fontSize:10, color:'var(--text-3)', marginTop:2 }}>{m.s}</div>
                  </div>
                ))}
              </div>
            </div>
            <Btn variant="ai" size="lg" style={{ width:'100%', justifyContent:'center' }} onClick={() => alert('KI-Analyse wird gestartet…\n\nIn der Prod-App: Claude erklärt alle Makro-Zusammenhänge und Auswirkungen auf dein CHF-Portfolio')}>
              Makro-Zusammenhänge erklären ↗
            </Btn>
          </div>
        )}

        {/* ── JOURNAL ── */}
        {page === 'journal' && (
          <div style={{ flex:1, overflowY:'auto', padding:16, display:'flex', flexDirection:'column', gap:12 }}>
            <div style={{ display:'grid', gridTemplateColumns:'repeat(4,minmax(0,1fr))', gap:8 }} className="stagger">
              {[{l:'Trades gesamt',v:'34',s:'Letztes Jahr',c:'var(--text-1)'},{l:'Trefferquote',v:'62%',s:'Ø Markt: 50%',c:'var(--green)'},{l:'Häufigster Bias',v:'FOMO',s:'8× erkannt',c:'var(--amber)'},{l:'Bias-Kosten',v:"−CHF 8'240",s:'Verlorene Rendite',c:'var(--red)'}].map((k,i)=>(
                <div key={i} style={{ background:'var(--bg-surface)', border:'1px solid var(--border-std)', borderRadius:14, padding:'14px 16px' }}>
                  <div className="label-caps" style={{ marginBottom:6 }}>{k.l}</div>
                  <div style={{ fontFamily:'var(--font-num)', fontSize: k.v.length > 5 ? 16 : 22, fontWeight:500, color:k.c }}>{k.v}</div>
                  <div style={{ fontSize:10, color:'var(--text-3)', marginTop:3 }}>{k.s}</div>
                </div>
              ))}
            </div>
            <div className="label-caps" style={{ marginTop:4 }}>Bias-Analyse</div>
            <div style={{ display:'grid', gridTemplateColumns:'repeat(3,minmax(0,1fr))', gap:8 }} className="stagger">
              {[
                { n:'FOMO', count:'8×', cost:"−CHF 4'120 · 50%", c:'var(--red)', border:'var(--red)', desc:'Kauf nach starkem Anstieg ohne Rücksetzer. TSLA nach +18% — danach −22%.' },
                { n:'Loss Aversion', count:'6×', cost:"−CHF 2'880 · 35%", c:'var(--red)', border:'var(--red)', desc:'Stop-Loss ignoriert. Ø 4.2 Wochen über Limit gehalten.' },
                { n:'Rache-Trade', count:'4×', cost:"−CHF 980 · 12%", c:'var(--amber)', border:'var(--amber)', desc:'Alle 4 innerhalb 2h nach Verlust-Trade. Alle 4 waren Verluste.' },
                { n:'Anchoring', count:'5×', cost:"−CHF 620 · 8%", c:'var(--amber)', border:'var(--amber)', desc:'Fixierung auf Einstandskurs statt aktuelle Bewertung.' },
                { n:'Overconfidence', count:'3×', cost:"−CHF 840 · 10%", c:'var(--amber)', border:'var(--amber)', desc:'Nach 3+ Gewinnen Position um 84% erhöht. Alle 3 folgenden: Verluste.' },
                { n:'Confirmation Bias', count:'2×', cost:"−CHF 280 · 3%", c:'var(--green)', border:'var(--green)', desc:'Nur 2 Mal gegenteilige Signale ignoriert. Investment Committee hilft.' },
              ].map((b, i) => (
                <div key={i} style={{ background:'var(--bg-surface)', border:'1px solid var(--border-std)', borderRadius:20, padding:14, borderTop:`2px solid ${b.border}` }}>
                  <div style={{ fontFamily:'var(--font-head)', fontSize:12, fontWeight:700, color:'var(--text-1)', marginBottom:4 }}>{b.n}</div>
                  <div style={{ fontFamily:'var(--font-num)', fontSize:22, fontWeight:500, color:b.c }}>{b.count}</div>
                  <div style={{ fontSize:11, color:'var(--text-3)' }}>{b.cost}</div>
                  <div style={{ fontSize:11, color:'var(--text-2)', marginTop:8, paddingTop:8, borderTop:'1px solid var(--border-dim)', lineHeight:1.5 }}>{b.desc}</div>
                </div>
              ))}
            </div>
            <div style={{ background:'var(--bg-surface)', border:'1px solid var(--border-std)', borderRadius:20, overflow:'hidden' }}>
              <div style={{ display:'grid', gridTemplateColumns:'60px 60px 100px 80px 60px 80px 1fr', padding:'8px 14px', background:'var(--bg-elevated)', borderBottom:'1px solid var(--border-std)', fontSize:9, fontWeight:600, fontFamily:'var(--font-head)', letterSpacing:'.06em', textTransform:'uppercase', color:'var(--text-3)' }}>
                <span>Titel</span><span>Datum</span><span>Resultat</span><span>Haltezeit</span><span>CRV</span><span>Bias</span><span>Notiz</span>
              </div>
              {[
                { sym:'NVDA', d:'Feb 26', r:'+CHF 4\'820', up:true,  h:'6 Wo.',   crv:'1:3.4', bias:'buy',  b:'Rational',    note:'Plan befolgt, Ziel erreicht' },
                { sym:'TSLA', d:'Jan 26', r:'−CHF 3\'200', up:false, h:'8 Wo.',   crv:'1:0.4', bias:'sell', b:'FOMO',         note:'Kauf nach +18% — klassisches FOMO' },
                { sym:'ZGLD', d:'Nov 25', r:'+CHF 6\'100', up:true,  h:'4 Wo.',   crv:'1:4.1', bias:'buy',  b:'Rational',    note:'Iran-Geopolitik antizipiert' },
                { sym:'MSFT', d:'Dez 25', r:'−CHF 1\'840', up:false, h:'12 Wo.',  crv:'1:0.6', bias:'sell', b:'Loss Av.',     note:'Stop-Loss 3 Wochen ignoriert' },
                { sym:'AAPL', d:'Okt 25', r:'−CHF 1\'100', up:false, h:'1 Std.',  crv:'1:0.2', bias:'sell', b:'Rache-Trade', note:'2h nach TSLA-Verlust geöffnet' },
              ].map((t, i) => (
                <div key={i} style={{ display:'grid', gridTemplateColumns:'60px 60px 100px 80px 60px 80px 1fr', padding:'10px 14px', borderBottom:'1px solid var(--border-dim)', fontSize:11, alignItems:'center', transition:'background var(--trans)', cursor:'pointer' }}
                  onMouseEnter={e => (e.currentTarget.style.background = 'var(--bg-hover)')}
                  onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
                >
                  <span style={{ fontFamily:'var(--font-head)', fontWeight:800, color:'var(--text-1)' }}>{t.sym}</span>
                  <span style={{ color:'var(--text-3)' }}>{t.d}</span>
                  <span style={{ fontFamily:'var(--font-num)', color: t.up ? 'var(--green)' : 'var(--red)' }}>{t.r}</span>
                  <span style={{ color:'var(--text-3)' }}>{t.h}</span>
                  <span style={{ fontFamily:'var(--font-num)', color: t.up ? 'var(--green)' : 'var(--red)' }}>{t.crv}</span>
                  <Tag variant={t.bias as any}>{t.b}</Tag>
                  <span style={{ color:'var(--text-3)', overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>{t.note}</span>
                </div>
              ))}
            </div>
            <Btn variant="ai" size="lg" style={{ width:'100%', justifyContent:'center' }} onClick={() => alert('Bias-Analyse:\n\nIn der Prod-App: Claude analysiert alle 34 Trades und erstellt personalisiertes Regelwerk')}>Personalisiertes Regelwerk erstellen ↗</Btn>
          </div>
        )}

        {/* ── Detail Panel ── */}
        {detail && (
          <div style={{ position:'absolute', top:0, right:0, bottom:0, width:380, background:'var(--bg-surface)', borderLeft:'1px solid var(--border-bold)', boxShadow:'-8px 0 32px rgba(0,0,0,.5)', zIndex:200, overflowY:'auto', display:'flex', flexDirection:'column', animation:'slideIn 200ms ease' }}>
            <div style={{ display:'flex', alignItems:'center', gap:10, padding:'14px 16px', borderBottom:'1px solid var(--border-std)', flexShrink:0 }}>
              <Btn variant="ghost" size="sm" onClick={() => setDetailId(null)}>← Zurück</Btn>
              <span style={{ fontFamily:'var(--font-head)', fontSize:14, fontWeight:700, color:'var(--text-1)', flex:1 }}>{detail.t}</span>
            </div>
            <div style={{ padding:'14px 16px', flex:1 }}>
              <div style={{ display:'grid', gridTemplateColumns:'repeat(3,minmax(0,1fr))', gap:6, marginBottom:12 }}>
                {detail.k.map((k, i) => (
                  <div key={i} style={{ background:'var(--bg-elevated)', borderRadius:10, padding:'9px 11px' }}>
                    <div className="label-caps" style={{ marginBottom:2 }}>{k.l}</div>
                    <div style={{ fontFamily:'var(--font-num)', fontSize:14, fontWeight:500, color:'var(--text-1)' }}>{k.v}</div>
                    <div style={{ fontSize:10, color:'var(--text-3)', marginTop:1 }}>{k.h}</div>
                  </div>
                ))}
              </div>
              <div style={{ display:'flex', flexDirection:'column', gap:4, marginBottom:12 }}>
                {detail.s.map((s, i) => (
                  <div key={i} style={{ display:'flex', gap:8, padding:'7px 10px', borderRadius:10, background:'var(--bg-elevated)', fontSize:11, color:'var(--text-2)', lineHeight:1.5 }}>
                    <span style={{ width:6, height:6, borderRadius:'50%', background:s.c, flexShrink:0, marginTop:4, display:'inline-block' }}/>
                    {s.t}
                  </div>
                ))}
              </div>
              <div style={{ display:'flex', gap:6 }}>
                {detail.buy && <Btn variant="buy" size="md" style={{ flex:1, justifyContent:'center' }} onClick={() => { setTradeSym(detail.t.split(' ')[0]); setTradeModal(true) }}>Order</Btn>}
                <Btn variant="ghost" size="md" style={{ flex:1, justifyContent:'center' }}>Watchlist</Btn>
                <Btn variant="ai" size="md" style={{ flex:1, justifyContent:'center' }} onClick={() => alert(`KI-Analyse:\n\n${detail.p}\n\nIn der Prod-App via Claude API`)}>KI ↗</Btn>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* ── Trade Modal ── */}
      {tradeModal && (
        <div style={{ position:'absolute', inset:0, zIndex:300, background:'rgba(8,12,18,.8)', backdropFilter:'blur(4px)', display:'flex', alignItems:'center', justifyContent:'center', animation:'fadeUp 180ms ease' }}
          onClick={e => { if (e.target === e.currentTarget) setTradeModal(false) }}
        >
          <div style={{ background:'var(--bg-surface)', border:'1px solid var(--border-bold)', borderRadius:20, width:440, maxWidth:'95vw', overflow:'hidden', boxShadow:'var(--shadow-card)' }}>
            <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', padding:'16px 20px', borderBottom:'1px solid var(--border-std)' }}>
              <span style={{ fontFamily:'var(--font-head)', fontSize:15, fontWeight:800, color:'var(--text-1)' }}>{tradeSym} — Neue Order</span>
              <button onClick={() => setTradeModal(false)} style={{ background:'none', border:'none', color:'var(--text-2)', cursor:'pointer', fontSize:18 }}>✕</button>
            </div>
            <div style={{ padding:'16px 20px', display:'flex', flexDirection:'column', gap:14 }}>
              <div>
                <div className="label-caps" style={{ marginBottom:6 }}>Order-Typ</div>
                <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:4 }}>
                  {['Market','Limit','Stop','OCO'].map((t, i) => (
                    <div key={i} style={{ padding:8, fontSize:11, fontFamily:'var(--font-head)', fontWeight:600, background: i === 0 ? 'var(--accent-dim)' : 'var(--bg-elevated)', color: i === 0 ? 'var(--accent)' : 'var(--text-2)', border: `1px solid ${i === 0 ? 'rgba(61,142,248,.3)' : 'var(--border-std)'}`, borderRadius:10, cursor:'pointer', textAlign:'center' }}>{t}</div>
                  ))}
                </div>
              </div>
              <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:10 }}>
                <div>
                  <div className="label-caps" style={{ marginBottom:6 }}>Betrag (CHF)</div>
                  <input defaultValue="14000" style={{ width:'100%', height:40, padding:'0 12px', background:'var(--bg-elevated)', border:'1px solid var(--border-std)', borderRadius:10, color:'var(--text-1)', fontFamily:'var(--font-num)', fontSize:14, outline:'none' }}/>
                </div>
                <div>
                  <div className="label-caps" style={{ marginBottom:6 }}>Stop-Loss</div>
                  <input defaultValue="344" style={{ width:'100%', height:40, padding:'0 12px', background:'var(--bg-elevated)', border:'1px solid var(--border-std)', borderRadius:10, color:'var(--text-1)', fontFamily:'var(--font-num)', fontSize:14, outline:'none' }}/>
                </div>
              </div>
              <div>
                <div className="label-caps" style={{ marginBottom:6 }}>Kursziel</div>
                <input defaultValue="445" style={{ width:'100%', height:40, padding:'0 12px', background:'var(--bg-elevated)', border:'1px solid var(--border-std)', borderRadius:10, color:'var(--text-1)', fontFamily:'var(--font-num)', fontSize:14, outline:'none' }}/>
              </div>
              <div style={{ background:'var(--bg-elevated)', borderRadius:10, border:'1px solid var(--border-std)', padding:12, display:'flex', flexDirection:'column', gap:5 }}>
                {[{k:'Geschätzte Stückzahl',v:'37 Aktien'},{k:'1%-Risiko-Limit',v:'CHF 2\'846 max.'},{k:'Stempelsteuer (CH)',v:'CHF 10.50'},{k:'CRV',v:'1 : 2.8 ✓'},{k:'Score bei Einstieg',v:'80/100 · Kaufen'}].map((r,i)=>(
                  <div key={i} style={{ display:'flex', justifyContent:'space-between', fontSize:11 }}>
                    <span style={{ color:'var(--text-3)' }}>{r.k}</span>
                    <span style={{ fontFamily:'var(--font-num)', fontWeight:500, color: r.v.includes('✓') ? 'var(--green)' : 'var(--text-1)' }}>{r.v}</span>
                  </div>
                ))}
              </div>
            </div>
            <div style={{ padding:'12px 20px', borderTop:'1px solid var(--border-std)', display:'flex', gap:8 }}>
              <Btn variant="buy" size="lg" pill style={{ flex:2, justifyContent:'center' }} onClick={() => { alert(`Order platziert!\n\n${tradeSym} · CHF 14\'000\nIn der Prod-App: Direkt via IBKR ausgeführt`); setTradeModal(false) }}>Kauforder ausführen</Btn>
              <Btn variant="ghost" size="lg" pill style={{ flex:1, justifyContent:'center' }} onClick={() => setTradeModal(false)}>Abbrechen</Btn>
            </div>
          </div>
        </div>
      )}

    </div>
  )
}
