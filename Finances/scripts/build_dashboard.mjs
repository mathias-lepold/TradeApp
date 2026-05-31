#!/usr/bin/env node
// build_dashboard.mjs - erzeugt EIN in sich geschlossenes HTML-Dashboard.
//
// Inhalt:
//   1) Dein Kern-Portfolio (aus watchlist.md, angereichert mit den 00_REPORT.md-Analysen)
//   2) Markt-Explorer: ALLE US-Aktien (1 FMP-Screener-Abruf), durchsuchbar, sortierbar,
//      anklickbar -> Detailkarte mit allen vorhandenen Kennzahlen + /analyze-Befehl.
//
// Liest:
//   .env (FMP_API_KEY, falls nicht schon als Umgebungsvariable gesetzt)
//   watchlist.md
//   research/<TICKER>/00_REPORT.md
//   screen_results/<strategie>_*.md  (optional, nur fuer Info)
//
// Schreibt:
//   dashboard.html  (oder eigener Pfad als 1. Argument, z.B. dein OneDrive-Ordner)
//
// Nutzung:
//   node scripts/build_dashboard.mjs
//   node scripts/build_dashboard.mjs "C:/Users/<Name>/OneDrive/dashboard.html"
//   node scripts/build_dashboard.mjs --mock      (Demo ohne API-Key, zum Anschauen)
//
// Keine externen Pakete noetig (Node 18+).

import { readFileSync, writeFileSync, existsSync, readdirSync } from "node:fs";
import { join } from "node:path";

const args = process.argv.slice(2);
const MOCK = args.includes("--mock");
const OUT = args.find(a => !a.startsWith("--")) || "dashboard.html";
const ROOT = process.cwd();
const read = p => (existsSync(p) ? readFileSync(p, "utf8") : "");

// FMP-Key aus Umgebung oder .env
function apiKey() {
  if (process.env.FMP_API_KEY) return process.env.FMP_API_KEY.trim();
  const env = read(join(ROOT, ".env"));
  const m = env.match(/FMP_API_KEY\s*=\s*(.+)/);
  return m ? m[1].trim() : "";
}

// ---------- Watchlist (Kern-Portfolio) ----------
function parseWatchlist() {
  const txt = read(join(ROOT, "watchlist.md"));
  const start = txt.search(/Kern-Portfolio/i);
  if (start < 0) return [];
  const rest = txt.slice(start);
  const end = rest.search(/\n##\s/);
  const section = end > 0 ? rest.slice(0, end) : rest;
  const rows = [];
  for (const line of section.split("\n")) {
    if (!line.trim().startsWith("|")) continue;
    const cells = line.split("|").slice(1, -1).map(c => c.trim());
    if (cells.length < 5) continue;
    const ticker = cells[0];
    if (!ticker || /^ticker$/i.test(ticker) || /^-+$/.test(ticker)) continue;
    rows.push({ ticker, name: cells[1], typ: cells[2], wlAmpel: cells[4], notiz: cells[5] || "" });
  }
  return rows;
}

// ---------- Einzel-Report (00_REPORT.md) ----------
const AMPELS = ["🟢", "🟡", "🔴"];
function parseReport(ticker) {
  const p = join(ROOT, "research", ticker, "00_REPORT.md");
  if (!existsSync(p)) return null;
  const t = read(p);
  const m = (re) => (t.match(re) || [])[1]?.trim() || "";
  const ampelLine = (t.match(/Ampel:[^\n]*/) || [""])[0];
  let ampel = "";
  const filledTemplate = /🟢\s*\/\s*🟡\s*\/\s*🔴/.test(ampelLine);
  if (!filledTemplate) ampel = AMPELS.find(a => ampelLine.includes(a)) || "";
  const begruendung = (ampelLine.split(/[—-]/).slice(1).join("-")).replace(/\*/g, "").trim();
  const listAfter = (heading) => {
    const idx = t.indexOf(heading);
    if (idx < 0) return [];
    const after = t.slice(idx + heading.length);
    const cut = after.search(/\n##?\s/);
    const block = after.slice(0, cut >= 0 ? cut : after.length);
    return block.split("\n")
      .map(l => l.replace(/^\s*(\d+\.|[-*])\s*/, "").trim())
      .filter(l => l && l !== "…" && !/^…$/.test(l))
      .slice(0, 3);
  };
  return {
    company: m(/Gesamt-Report:\s*(.+?)\s*\(/),
    date: m(/Analysedatum:\**\s*([0-9]{4}-[0-9]{2}-[0-9]{2})/),
    price: m(/Aktueller Kurs:\**\s*([^()\n·*]+)/),
    ampel, begruendung,
    fairValue: m(/Faire Wertspanne[^|]*\|\s*([^|]+?)\s*\|/),
    sector: m(/Sektor\/Branche:\**\s*([^\n]+)/).replace(/\*/g, ""),
    marketCap: m(/Marktkapitalisierung:\**\s*([^\n]+)/).replace(/\*/g, ""),
    pros: listAfter("Top-3 Pro"),
    contras: listAfter("Top-3 Contra"),
  };
}

// ---------- US-Aktien-Universum (1 FMP-Abruf) ----------
async function fetchUniverse(key) {
  const base = "https://financialmodelingprep.com/stable/company-screener";
  const p = new URLSearchParams({
    country: "US", exchange: "NASDAQ,NYSE,AMEX",
    isEtf: "false", isFund: "false", isActivelyTrading: "true", limit: "12000",
  });
  const res = await fetch(`${base}?${p.toString()}&apikey=${key}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const data = await res.json();
  if (!Array.isArray(data)) throw new Error("unerwartete Antwort");
  return data.map(d => ({
    t: d.symbol, n: d.companyName || "", s: d.sector || "", i: d.industry || "",
    mc: Number(d.marketCap) || 0, p: Number(d.price) || 0, b: Number(d.beta) || 0,
    d: Number(d.lastAnnualDividend) || 0, v: Number(d.volume) || 0, e: d.exchangeShortName || "",
  })).filter(x => x.t);
}

function mockUniverse() {
  return [
    { t: "NVDA", n: "NVIDIA Corp", s: "Technology", i: "Semiconductors", mc: 5.1e12, p: 211, b: 1.7, d: 0.04, v: 2.1e8, e: "NASDAQ" },
    { t: "AAPL", n: "Apple Inc", s: "Technology", i: "Consumer Electronics", mc: 4.58e12, p: 295, b: 1.2, d: 1.0, v: 5e7, e: "NASDAQ" },
    { t: "MSFT", n: "Microsoft Corp", s: "Technology", i: "Software", mc: 3.34e12, p: 450, b: 0.9, d: 3.0, v: 2e7, e: "NASDAQ" },
    { t: "KO", n: "Coca-Cola Co", s: "Consumer Defensive", i: "Beverages", mc: 2.6e11, p: 62, b: 0.6, d: 1.94, v: 1.2e7, e: "NYSE" },
    { t: "PLTR", n: "Palantir Technologies", s: "Technology", i: "Software", mc: 3.59e11, p: 155, b: 2.6, d: 0, v: 6e7, e: "NASDAQ" },
  ];
}

// ---------- letztes Screening (nur fuer Info-Zeile) ----------
function latestScreenInfo() {
  const dir = join(ROOT, "screen_results");
  if (!existsSync(dir)) return "";
  const files = readdirSync(dir).filter(f => f.endsWith(".md"));
  if (!files.length) return "";
  files.sort();
  return files[files.length - 1].replace(/\.md$/, "");
}

// ====================== Zusammenbau ======================
const core = parseWatchlist().map(r => ({ ...r, rep: parseReport(r.ticker) }));

let universe = [];
let universeNote = "";
if (MOCK) {
  universe = mockUniverse();
  universeNote = "Demo-Daten (--mock)";
} else {
  const key = apiKey();
  if (!key) {
    universeNote = "⚠️ Kein FMP_API_KEY gefunden – Markt-Liste leer. Lege .env an (siehe STRATEGIEN.md).";
  } else {
    try {
      universe = await fetchUniverse(key);
      universeNote = `${universe.length.toLocaleString("de-DE")} US-Aktien · Stand ${new Date().toISOString().slice(0, 10)}`;
    } catch (e) {
      universeNote = `⚠️ Markt-Liste konnte nicht geladen werden (${e.message}).`;
    }
  }
}

// Analysen an Universums-Eintraege anheften (fuer Ampel/Detail in der grossen Liste)
const repByTicker = {};
for (const c of core) if (c.rep) repByTicker[c.ticker] = c.rep;
for (const s of universe) {
  const rep = repByTicker[s.t];
  if (rep) s.r = { a: rep.ampel, g: rep.begruendung, fv: rep.fairValue, dt: rep.date, pr: rep.pros, co: rep.contras };
}

// Portfolio-Daten fuer die JS-Seite aufbereiten
const portfolio = core.map(c => ({
  t: c.ticker, n: (c.rep && c.rep.company) || c.name, ty: c.typ, no: c.notiz,
  a: (c.rep && c.rep.ampel) || (AMPELS.includes(c.wlAmpel) ? c.wlAmpel : ""),
  r: c.rep ? { a: c.rep.ampel, g: c.rep.begruendung, fv: c.rep.fairValue, dt: c.rep.date, pr: c.rep.pros, co: c.rep.contras, price: c.rep.price } : null,
}));

const stamp = new Date().toISOString().slice(0, 16).replace("T", " ");
const screenInfo = latestScreenInfo();

const css = `
:root{--g:#16a34a;--y:#d97706;--r:#dc2626;--n:#9ca3af;--bg:#f7f8fa;--card:#fff;--bd:#e5e7eb;--tx:#111827;--mut:#6b7280}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--tx);font:16px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;padding:env(safe-area-inset-top) 0 60px}
.wrap{max-width:1100px;margin:0 auto;padding:0 16px}
header.top{padding:22px 0 6px}
h1{font-size:24px;margin:0 0 2px}
.sub{color:var(--mut);font-size:13px}
.disclaimer{background:#fff7ed;border:1px solid #fed7aa;color:#9a3412;border-radius:10px;padding:9px 13px;font-size:13px;margin:12px 0}
h2{font-size:18px;margin:26px 0 12px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px}
.card{background:var(--card);border:1px solid var(--bd);border-left:5px solid var(--n);border-radius:14px;padding:13px 15px;box-shadow:0 1px 2px rgba(0,0,0,.04)}
.card.g{border-left-color:var(--g)}.card.y{border-left-color:var(--y)}.card.r{border-left-color:var(--r)}
.card .hd{display:flex;justify-content:space-between;align-items:center;gap:8px}
.ticker{font-weight:700;font-size:17px}
.typ{font-size:12px;color:var(--mut);margin:2px 0 6px}
.dot{width:13px;height:13px;border-radius:50%;background:var(--n);flex:0 0 auto}
.dot.g{background:var(--g)}.dot.y{background:var(--y)}.dot.r{background:var(--r)}
.reason{font-size:14px;margin:6px 0}
.kv{display:flex;justify-content:space-between;gap:10px;font-size:14px;padding:3px 0;border-top:1px dashed var(--bd)}
.kv span{color:var(--mut)}.kv b{text-align:right}
.muted{color:var(--mut)}.small{font-size:12px}
code{background:#eef2ff;color:#3730a3;padding:2px 7px;border-radius:6px;font-size:13px}
details{margin-top:6px}summary{cursor:pointer;font-size:14px;color:var(--mut)}
details ul{margin:4px 0 8px;padding-left:18px;font-size:14px}
.tools{position:sticky;top:0;background:var(--bg);padding:8px 0;z-index:5;display:flex;gap:8px;flex-wrap:wrap}
.tools input,.tools select{font:15px inherit;padding:9px 12px;border:1px solid var(--bd);border-radius:10px;background:#fff}
.tools input{flex:1;min-width:140px}
.count{color:var(--mut);font-size:13px;margin:4px 0 8px}
.list{background:var(--card);border:1px solid var(--bd);border-radius:14px;overflow:hidden}
.row{display:grid;grid-template-columns:62px 1fr auto;gap:10px;align-items:center;padding:11px 14px;border-bottom:1px solid var(--bd);cursor:pointer}
.row:last-child{border-bottom:0}
.row:hover{background:#f9fafb}
.row .t{font-weight:700}
.row .nm{color:var(--mut);font-size:13px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.row .rt{display:flex;align-items:center;gap:8px;font-size:13px;color:var(--mut);justify-self:end}
.detail{padding:12px 16px;background:#fafafa;border-bottom:1px solid var(--bd);font-size:14px}
.detail .grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:2px 18px}
.analyze{background:#eef2ff;border:1px solid #c7d2fe;border-radius:10px;padding:9px 12px;margin-top:10px;font-size:14px}
.more{display:block;width:100%;padding:12px;border:0;background:#fff;border-top:1px solid var(--bd);font:600 15px inherit;color:#3730a3;cursor:pointer}
details.sector{background:var(--card);border:1px solid var(--bd);border-radius:12px;margin-bottom:8px;overflow:hidden}
details.sector>summary{padding:13px 16px;font-weight:600;cursor:pointer;list-style:none}
details.sector>summary::-webkit-details-marker{display:none}
details.sector>summary:before{content:"▸ ";color:var(--mut)}
details.sector[open]>summary:before{content:"▾ "}
details.sector .list{border:0;border-top:1px solid var(--bd);border-radius:0}
details.sector .row{align-items:start}
details.sector .nm{white-space:normal;color:var(--tx)}
details.sector .nm b{font-weight:600}
.biz{display:block;color:var(--mut);font-size:12px;line-height:1.35;margin-top:2px}
footer{margin-top:30px;color:var(--mut);font-size:12px;text-align:center}
`;

// Browser-JS bewusst OHNE Template-Strings / ${...}, damit es nicht mit Node kollidiert.
const js = `
var STOCKS = __STOCKS__;
var PORTFOLIO = __PORTFOLIO__;
var shown = 300, q = "", sortKey = "mc";

function cls(a){return a==="🟢"?"g":a==="🟡"?"y":a==="🔴"?"r":"n";}
function esc(s){return String(s==null?"":s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");}
function cap(n){if(!n)return "–";if(n>=1e12)return "$"+(n/1e12).toFixed(2)+" Bio.";if(n>=1e9)return "$"+(n/1e9).toFixed(1)+" Mrd.";if(n>=1e6)return "$"+(n/1e6).toFixed(0)+" Mio.";return "$"+n;}
function px(n){return n?("$"+n.toFixed(2)):"–";}
function yld(s){return (s.d&&s.p)?((s.d/s.p*100).toFixed(1)+" %"):"–";}
function vol(n){return n?n.toLocaleString("de-DE"):"–";}

function kv(label,val){return '<div class="kv"><span>'+esc(label)+'</span><b>'+esc(val)+'</b></div>';}

function analysisBlock(r){
  if(!r) return "";
  var h='<div class="reason"><b>'+(r.a||"")+'</b> '+esc(r.g||"")+'</div>';
  if(r.fv) h+=kv("Faire Spanne",r.fv);
  if(r.dt) h+=kv("Analysiert",r.dt);
  if(r.pr&&r.pr.length){h+='<b>✅ Pro</b><ul>';r.pr.forEach(function(x){h+='<li>'+esc(x)+'</li>';});h+='</ul>';}
  if(r.co&&r.co.length){h+='<b>⛔ Contra</b><ul>';r.co.forEach(function(x){h+='<li>'+esc(x)+'</li>';});h+='</ul>';}
  return h;
}

function detail(s){
  var bz=biz(s.t);
  var bl=bz?('<div class="muted" style="margin-bottom:8px">🏢 '+esc(bz)+'</div>'):"";
  var g='<div class="grid2">'+
    kv("Sektor",s.s||"–")+kv("Branche",s.i||"–")+
    kv("Marktkap.",cap(s.mc))+kv("Kurs",px(s.p))+
    kv("Div.-Rendite",yld(s))+kv("Beta",s.b?s.b.toFixed(2):"–")+
    kv("Volumen",vol(s.v))+kv("Börse",s.e||"–")+'</div>';
  var a = s.r ? ('<div style="margin-top:10px">'+analysisBlock(s.r)+'</div>')
             : '<div class="muted small" style="margin-top:8px">Tiefe Kennzahlen (KGV, ROE, Wachstum…) erscheinen nach der Tiefenanalyse.</div>';
  var cmd='<div class="analyze">🔍 <b>Tiefenanalyse starten</b> – in Claude Code eingeben:<br><code>/analyze '+esc(s.t)+'</code></div>';
  return '<div class="detail">'+bl+g+a+cmd+'</div>';
}

function filtered(){
  var t=q.trim().toLowerCase();
  var arr=STOCKS.filter(function(s){return !t || s.t.toLowerCase().indexOf(t)>=0 || (s.n&&s.n.toLowerCase().indexOf(t)>=0);});
  arr.sort(function(a,b){
    if(sortKey==="name")return (a.n||"").localeCompare(b.n||"");
    if(sortKey==="p")return b.p-a.p;
    if(sortKey==="yld")return (b.d/b.p||0)-(a.d/a.p||0);
    return b.mc-a.mc;
  });
  return arr;
}

function renderList(){
  var arr=filtered();
  var slice=arr.slice(0,shown);
  var html="";
  slice.forEach(function(s){
    var dot=s.r?('<span class="dot '+cls(s.r.a)+'"></span>'):"";
    html+='<div class="row" onclick="toggle(this,\\''+s.t+'\\')">'+
      '<span class="t">'+esc(s.t)+'</span>'+
      '<span class="nm">'+esc(s.n)+'</span>'+
      '<span class="rt">'+cap(s.mc)+dot+'</span></div>';
  });
  if(arr.length>shown) html+='<button class="more" onclick="shown+=300;renderList()">Mehr anzeigen ('+(arr.length-shown)+' weitere)</button>';
  document.getElementById("list").innerHTML=html || '<div class="row"><span class="muted">Keine Treffer.</span></div>';
  document.getElementById("count").textContent=arr.length.toLocaleString("de-DE")+" Aktien"+(q?" gefunden":"")+" · "+Math.min(shown,arr.length)+" angezeigt";
}

var openTicker=null;
function toggle(rowEl,t){
  var ex=rowEl.nextSibling;
  if(ex&&ex.className==="detail"){ex.parentNode.removeChild(ex);openTicker=null;return;}
  var old=document.querySelector(".detail");if(old)old.parentNode.removeChild(old);
  var s=STOCKS.filter(function(x){return x.t===t;})[0];if(!s)return;
  var div=document.createElement("div");div.innerHTML=detail(s);
  rowEl.parentNode.insertBefore(div.firstChild,rowEl.nextSibling);openTicker=t;
}

function renderPortfolio(){
  var h="";
  PORTFOLIO.forEach(function(p){
    var c=cls(p.a);
    var body = p.r ? analysisBlock(p.r) : '<p class="muted">Noch nicht analysiert.'+(p.no?" "+esc(p.no):"")+'</p><div class="muted small">Tipp: <code>/analyze '+esc(p.t)+'</code></div>';
    h+='<article class="card '+c+'"><div class="hd"><div><span class="ticker">'+esc(p.t)+'</span> <span class="muted">'+esc(p.n)+'</span></div><span class="dot '+c+'"></span></div>'+
       '<div class="typ">'+esc(p.ty||"")+'</div>'+body+'</article>';
  });
  document.getElementById("portfolio").innerHTML=h;
}

// Kurzbeschreibungen der größten US-Werte (kuratiert, keine API-Abrufe).
// Fehlt ein Ticker, wird einfach keine Beschreibung gezeigt.
var BIZ={
  // Technology
  AAPL:"iPhone, Mac & Dienste-Ökosystem",MSFT:"Windows, Office & Azure-Cloud",NVDA:"KI- & Grafikchips",
  AVGO:"Halbleiter & Infrastruktur-Software",ORCL:"Datenbanken & Unternehmens-Cloud",CRM:"CRM-Cloud-Software (Salesforce)",
  AMD:"Prozessoren & Grafikchips",ADBE:"Kreativ- & Dokumentensoftware",CSCO:"Netzwerktechnik & Hardware",
  ACN:"IT- & Strategieberatung",TXN:"Analog-Halbleiter",QCOM:"Mobilfunk-Chips & Patente",
  INTC:"Prozessoren & Chipfertigung",IBM:"IT-Dienste, Software & Mainframes",NOW:"Workflow-Cloud (ServiceNow)",
  INTU:"Steuer- & Finanzsoftware (TurboTax)",AMAT:"Maschinen für die Chipfertigung",MU:"Speicherchips (DRAM/NAND)",
  PLTR:"Datenanalyse-Software",
  // Communication Services
  GOOGL:"Google-Suche, Werbung & YouTube",GOOG:"Google-Suche, Werbung & YouTube",META:"Facebook, Instagram & WhatsApp",
  NFLX:"Video-Streaming",DIS:"Medien, Filme & Freizeitparks",CMCSA:"Kabel/Breitband & NBCUniversal",
  T:"Telekommunikation (AT&T)",VZ:"Telekommunikation (Verizon)",TMUS:"Mobilfunk (T-Mobile US)",
  CHTR:"Kabel & Breitband",EA:"Videospiele",
  // Consumer Cyclical
  AMZN:"Online-Handel & AWS-Cloud",TSLA:"Elektroautos & Energiespeicher",HD:"Baumarkt-Kette (Home Depot)",
  MCD:"Fast-Food-Kette",NKE:"Sportartikel & Bekleidung",LOW:"Baumarkt-Kette (Lowe's)",
  SBUX:"Kaffeehaus-Kette",BKNG:"Online-Reisebuchung",TJX:"Discount-Mode (TK Maxx)",ABNB:"Vermittlung von Unterkünften",
  // Consumer Defensive
  WMT:"Größte Einzelhandelskette der USA",COST:"Großhandels-Clubs (Costco)",PG:"Markenkonsumgüter (P&G)",
  KO:"Getränke (Coca-Cola)",PEP:"Getränke & Snacks (PepsiCo)",PM:"Tabak (international)",
  MO:"Tabak (USA, Altria)",MDLZ:"Snacks & Süßwaren",CL:"Körperpflege (Colgate)",TGT:"Einzelhandelskette (Target)",
  // Healthcare
  LLY:"Pharma (Diabetes-/Abnehm-Mittel)",UNH:"Krankenversicherung & Gesundheitsdienste",JNJ:"Pharma & Medizintechnik",
  ABBV:"Biopharma-Medikamente",MRK:"Pharma (Merck & Co.)",TMO:"Labor- & Diagnostik-Ausrüstung",
  ABT:"Medizintechnik & Diagnostik",PFE:"Pharma (Pfizer)",DHR:"Life-Science & Diagnostik",
  AMGN:"Biotechnologie",ISRG:"OP-Roboter (da Vinci)",BMY:"Pharma (Bristol-Myers Squibb)",
  // Financial Services
  "BRK-B":"Beteiligungs-Konglomerat (Buffett)","BRK.B":"Beteiligungs-Konglomerat (Buffett)",JPM:"Größte US-Bank",
  V:"Zahlungsnetzwerk (Visa)",MA:"Zahlungsnetzwerk (Mastercard)",BAC:"Großbank (Bank of America)",
  WFC:"Großbank (Wells Fargo)",GS:"Investmentbank (Goldman Sachs)",MS:"Investmentbank & Vermögensverwaltung",
  AXP:"Kreditkarten (American Express)",BLK:"Vermögensverwaltung (BlackRock)",SPGI:"Ratings & Finanzdaten",
  C:"Großbank (Citigroup)",SCHW:"Online-Broker (Charles Schwab)",
  // Industrials
  GE:"Flugzeugtriebwerke (GE Aerospace)",CAT:"Bau- & Bergbaumaschinen",RTX:"Luftfahrt & Rüstung (Raytheon)",
  HON:"Industrie- & Technik-Konglomerat",UNP:"Güter-Eisenbahn",BA:"Flugzeugbau (Boeing)",
  DE:"Landmaschinen (John Deere)",LMT:"Rüstung (Lockheed Martin)",UPS:"Paket- & Logistikdienst",
  ETN:"Elektrotechnik & Energiemanagement",GD:"Rüstung (General Dynamics)",NOC:"Rüstung (Northrop Grumman)",
  // Energy
  XOM:"Öl & Gas (ExxonMobil)",CVX:"Öl & Gas (Chevron)",COP:"Öl- & Gasförderung",
  SLB:"Ölfeld-Dienstleistungen",EOG:"Öl- & Gasförderung",MPC:"Raffinerien (Marathon)",
  PSX:"Raffinerien (Phillips 66)",WMB:"Erdgas-Pipelines",OXY:"Öl & Gas (Occidental)",
  VLO:"Raffinerien (Valero)",KMI:"Pipeline-Infrastruktur",
  // Basic Materials
  LIN:"Industriegase (Linde)",SHW:"Farben & Lacke (Sherwin-Williams)",APD:"Industriegase (Air Products)",
  ECL:"Wasser- & Hygiene-Chemie",FCX:"Kupfer-Bergbau",NEM:"Gold-Bergbau",
  DOW:"Basis-Chemie",NUE:"Stahlproduktion (Nucor)",DD:"Spezialchemie (DuPont)",
  // Utilities
  NEE:"Stromversorger & Erneuerbare",SO:"Stromversorger (Southern Co.)",DUK:"Stromversorger (Duke Energy)",
  CEG:"Stromerzeugung (Kernkraft)",AEP:"Stromversorger",D:"Energieversorger (Dominion)",
  SRE:"Energieversorger (Sempra)",EXC:"Stromversorger (Exelon)",XEL:"Stromversorger (Xcel)",
  // Real Estate (REITs)
  PLD:"Logistik-Immobilien (REIT)",AMT:"Funkturm-Immobilien (REIT)",EQIX:"Rechenzentren (REIT)",
  WELL:"Gesundheits-Immobilien (REIT)",SPG:"Einkaufszentren (REIT)",PSA:"Self-Storage (REIT)",
  CCI:"Funkturm-Infrastruktur (REIT)",O:"Einzelhandels-Immobilien (REIT)",DLR:"Rechenzentren (REIT)"
};
function biz(t){return BIZ[t]||BIZ[t.replace(/\\./g,"-")]||BIZ[t.replace(/-/g,".")]||"";}

var SECTOR_TOP = 10; // Top N je Sektor
function renderSectors(){
  var by={};
  STOCKS.forEach(function(s){var k=s.s||"Ohne Sektor";(by[k]=by[k]||[]).push(s);});
  var names=Object.keys(by).sort(function(a,b){return a.localeCompare(b,"de");});
  var h="";
  names.forEach(function(name){
    var arr=by[name].slice().sort(function(a,b){return b.mc-a.mc;}).slice(0,SECTOR_TOP);
    var rows="";
    arr.forEach(function(s){
      var dot=s.r?('<span class="dot '+cls(s.r.a)+'"></span>'):"";
      var b=biz(s.t);
      var nm='<b>'+esc(s.n)+'</b>'+(b?'<span class="biz">'+esc(b)+'</span>':'');
      rows+='<div class="row" onclick="toggle(this,\\''+s.t+'\\')">'+
        '<span class="t">'+esc(s.t)+'</span>'+
        '<span class="nm">'+nm+'</span>'+
        '<span class="rt">'+cap(s.mc)+dot+'</span></div>';
    });
    h+='<details class="sector"><summary>'+esc(name)+' <span class="muted small">('+by[name].length+' Werte · Top '+arr.length+')</span></summary><div class="list">'+rows+'</div></details>';
  });
  document.getElementById("sectors").innerHTML=h;
}

document.getElementById("q").addEventListener("input",function(e){q=e.target.value;shown=300;renderList();});
document.getElementById("sort").addEventListener("change",function(e){sortKey=e.target.value;renderList();});
renderPortfolio();renderSectors();renderList();
`;

const html = `<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Finanzen">
<meta name="theme-color" content="#ffffff">
<title>Mein Finanz-Dashboard</title>
<style>${css}</style>
</head>
<body>
<div class="wrap">
  <header class="top">
    <h1>📊 Mein Finanz-Dashboard</h1>
    <div class="sub">Stand: ${stamp} · Quelle: Financial Modeling Prep + eigene Analysen (Claude Code)${screenInfo ? " · Letztes Screening: " + screenInfo : ""}</div>
    <div class="disclaimer">⚠️ Nur zur Information – <b>keine Anlageberatung</b>. Ampeln sind Orientierung, keine Empfehlung. Zahlen an der Primärquelle prüfen.</div>
  </header>

  <h2>⭐ Mein Kern-Portfolio</h2>
  <div id="portfolio" class="grid"></div>

  <h2>🗂️ Sektor-Überblick <span class="muted small" style="font-weight:400">· je Branche die 10 größten Unternehmen</span></h2>
  <div class="sub" style="margin-bottom:8px">Aufklappen zum Stöbern · jede Aktie antippbar für Details. Kostet keine zusätzlichen Datenabrufe.</div>
  <div id="sectors"></div>

  <h2>🇺🇸 Alle US-Aktien</h2>
  <div class="sub" style="margin-bottom:8px">${universeNote}</div>
  <div class="tools">
    <input id="q" type="search" placeholder="🔎 Ticker oder Name suchen …" autocomplete="off">
    <select id="sort">
      <option value="mc">Größte zuerst</option>
      <option value="name">Name A–Z</option>
      <option value="p">Höchster Kurs</option>
      <option value="yld">Höchste Dividende</option>
    </select>
  </div>
  <div id="count" class="count"></div>
  <div id="list" class="list"></div>

  <footer>Erstellt mit <code>scripts/build_dashboard.mjs</code> · Tippe eine Aktie an für Details · Keine Anlageberatung.</footer>
</div>
<script>
${js.replace("__STOCKS__", JSON.stringify(universe)).replace("__PORTFOLIO__", JSON.stringify(portfolio))}
</script>
</body>
</html>`;

writeFileSync(OUT, html);
console.log(`✓ Dashboard erstellt: ${OUT}`);
console.log(`  Portfolio: ${core.length} Werte · Markt-Liste: ${universe.length} US-Aktien`);
if (!MOCK && !universe.length) console.log("  Hinweis: Markt-Liste leer – FMP_API_KEY prüfen (oder --mock zum Anschauen).");
