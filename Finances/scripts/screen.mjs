#!/usr/bin/env node
// screen.mjs - US-Aktien/ETF-Screener fuer das Finances-Projekt.
//
// Filtert die US-Boerse nach einer Strategie und schreibt eine Shortlist.
// Datenquelle: Financial Modeling Prep (FMP) - kostenloser API-Key noetig.
// Benoetigt Node 18+ (nutzt global fetch, KEINE externen Pakete).
//
// Nutzung:
//   FMP_API_KEY=dein_key node scripts/screen.mjs <strategie> [--etf] [--limit N] [--top N]
//
//   <strategie>:  quality-growth | value | dividend | momentum   (Standard: quality-growth)
//   --etf         ETFs/Fonds statt Einzelaktien screenen
//   --limit N     Wie viele Kandidaten angereichert/bewertet werden (Standard 30, schont API-Limit)
//   --top N       Wie viele in die Shortlist kommen (Standard 10)
//
// Ergebnis:
//   screen_results/<strategie>_<datum>.md      (lesbarer Report)
//   screen_results/latest_shortlist.txt        (ein Ticker pro Zeile - fuer die Automatisierung)

import { writeFileSync, mkdirSync } from "node:fs";

const API = "https://financialmodelingprep.com/api/v3";
const KEY = process.env.FMP_API_KEY;
if (!KEY) {
  console.error("FEHLER: Umgebungsvariable FMP_API_KEY ist nicht gesetzt.");
  console.error("Hol dir einen kostenlosen Key auf https://site.financialmodelingprep.com/developer/docs");
  console.error('Dann z.B.:  export FMP_API_KEY="dein_key"   (Git Bash)  oder in .env eintragen.');
  process.exit(1);
}

// ---- Argumente ----
const args = process.argv.slice(2);
const strategy = (args.find(a => !a.startsWith("--")) || "quality-growth").toLowerCase();
const isEtf = args.includes("--etf");
const enrichLimit = Number(getFlag("--limit")) || 30;
const topN = Number(getFlag("--top")) || 10;
function getFlag(name) { const i = args.indexOf(name); return i >= 0 ? args[i + 1] : null; }

const STRATEGIES = ["quality-growth", "value", "dividend", "momentum"];
if (!STRATEGIES.includes(strategy)) {
  console.error(`Unbekannte Strategie '${strategy}'. Erlaubt: ${STRATEGIES.join(", ")}`);
  process.exit(1);
}

async function getJSON(url) {
  const sep = url.includes("?") ? "&" : "?";
  const res = await fetch(`${url}${sep}apikey=${KEY}`);
  if (!res.ok) throw new Error(`HTTP ${res.status} bei ${url.split("?")[0]}`);
  return res.json();
}

// ---- Schritt 1: Basis-Universum vom Screener holen (1 API-Call) ----
async function baseUniverse() {
  const p = new URLSearchParams({
    country: "US",
    exchange: "NASDAQ,NYSE",
    isActivelyTrading: "true",
    isEtf: String(isEtf),
    limit: "3000",
  });
  // Strategie-spezifische harte Filter, die der Screener direkt kann:
  if (strategy === "dividend") p.set("dividendMoreThan", "0.5"); // zahlt ueberhaupt Dividende
  if (!isEtf) p.set("marketCapMoreThan", "2000000000");          // > 2 Mrd. (keine Micro-Caps)
  else p.set("marketCapMoreThan", "500000000");                 // ETFs: > 500 Mio. AUM
  const data = await getJSON(`${API}/stock-screener?${p.toString()}`);
  return Array.isArray(data) ? data : [];
}

// ---- Schritt 2: Top-Kandidaten anreichern + bewerten ----
async function enrichAndScore(candidates) {
  // Vorsortierung, damit wir nur die relevantesten anreichern (spart API-Calls):
  let pre = candidates;
  if (strategy === "dividend") {
    pre = candidates.sort((a, b) => (b.lastAnnualDividend / b.price || 0) - (a.lastAnnualDividend / a.price || 0));
  } else {
    pre = candidates.sort((a, b) => (b.marketCap || 0) - (a.marketCap || 0)); // Blue Chips zuerst
  }
  pre = pre.slice(0, enrichLimit);

  const scored = [];
  for (const c of pre) {
    try {
      const row = { symbol: c.symbol, name: c.companyName, price: c.price, marketCap: c.marketCap, sector: c.sector };
      if (strategy === "momentum" || isEtf) {
        const ch = (await getJSON(`${API}/stock-price-change/${c.symbol}`))[0] || {};
        row.m3 = ch["3M"]; row.m6 = ch["6M"]; row.y1 = ch["1Y"];
        row.score = (num(ch["3M"]) * 0.4 + num(ch["6M"]) * 0.4 + num(ch["1Y"]) * 0.2);
        if (num(ch["6M"]) <= 0) row.score -= 50; // negativer Trend wird abgestraft
      } else if (strategy === "dividend") {
        const r = (await getJSON(`${API}/ratios-ttm/${c.symbol}`))[0] || {};
        const yld = pct(r.dividendYielTTM ?? r.dividendYieldTTM);
        const payout = pct(r.payoutRatioTTM);
        row.yield = yld; row.payout = payout;
        row.score = yld - (payout > 80 ? (payout - 80) : 0); // hohe Rendite, aber Ausschuettung tragfaehig
        if (yld < 1.5 || yld > 12) row.score -= 100;        // zu niedrig / Dividenden-Falle
      } else if (strategy === "value") {
        const r = (await getJSON(`${API}/ratios-ttm/${c.symbol}`))[0] || {};
        row.pe = r.peRatioTTM; row.pb = r.priceToBookRatioTTM; row.roe = pct(r.returnOnEquityTTM);
        const pe = num(r.peRatioTTM), pb = num(r.priceToBookRatioTTM);
        row.score = (pe > 0 ? 1000 / pe : -50) + (pb > 0 ? 100 / pb : 0) + row.roe * 0.5;
        if (pe <= 0) row.score -= 100; // keine Gewinne -> kein Value
      } else { // quality-growth
        const r = (await getJSON(`${API}/ratios-ttm/${c.symbol}`))[0] || {};
        const g = (await getJSON(`${API}/financial-growth/${c.symbol}?period=annual&limit=1`))[0] || {};
        const growth = pct(g.revenueGrowth), roe = pct(r.returnOnEquityTTM), nm = pct(r.netProfitMarginTTM);
        row.growth = growth; row.roe = roe; row.netMargin = nm;
        row.score = growth * 1.2 + roe * 0.6 + nm * 0.6;
        if (growth < 5) row.score -= 50; // zu wenig Wachstum
      }
      if (Number.isFinite(row.score)) scored.push(row);
    } catch (e) {
      // einzelne Fehlschlaege ignorieren, weitermachen
    }
  }
  return scored.sort((a, b) => b.score - a.score);
}

const num = v => (Number.isFinite(Number(v)) ? Number(v) : 0);
const pct = v => num(v) * (Math.abs(num(v)) < 3 ? 100 : 1); // FMP gibt teils 0.18 statt 18%

function fmtRow(r, i) {
  const cap = r.marketCap ? `$${(r.marketCap / 1e9).toFixed(1)} Mrd.` : "-";
  let extra = "";
  if ("growth" in r) extra = `Wachstum ${r.growth?.toFixed(0)}% · ROE ${r.roe?.toFixed(0)}% · Marge ${r.netMargin?.toFixed(0)}%`;
  else if ("pe" in r) extra = `KGV ${num(r.pe).toFixed(1)} · KBV ${num(r.pb).toFixed(1)} · ROE ${r.roe?.toFixed(0)}%`;
  else if ("yield" in r) extra = `Div.-Rendite ${r.yield?.toFixed(1)}% · Ausschuettung ${r.payout?.toFixed(0)}%`;
  else if ("m6" in r) extra = `3M ${fmtP(r.m3)} · 6M ${fmtP(r.m6)} · 1J ${fmtP(r.y1)}`;
  return `| ${i + 1} | ${r.symbol} | ${trunc(r.name)} | ${cap} | ${extra} |`;
}
const fmtP = v => (v == null ? "-" : `${num(v) > 0 ? "+" : ""}${num(v).toFixed(0)}%`);
const trunc = s => (s && s.length > 28 ? s.slice(0, 27) + "…" : s || "-");

(async () => {
  console.error(`Screener: Strategie='${strategy}'${isEtf ? " (ETFs)" : ""}, top ${topN}…`);
  const universe = await baseUniverse();
  console.error(`  Basis-Universum: ${universe.length} Werte`);
  const ranked = await enrichAndScore(universe);
  const top = ranked.slice(0, topN);

  const date = new Date().toISOString().slice(0, 10);
  mkdirSync("screen_results", { recursive: true });

  const header = `| # | Ticker | Name | Marktkap. | Kennzahlen |\n|---|--------|------|-----------|------------|`;
  const md = `# Screening-Ergebnis: ${strategy}${isEtf ? " (ETFs)" : ""} — ${date}

> Automatisch erstellt von \`scripts/screen.mjs\` · Datenquelle: Financial Modeling Prep.
> ⚠️ Schnelle Vorauswahl anhand harter Kennzahlen — **keine** Tiefenanalyse, **keine** Anlageberatung.
> Die Top-Kandidaten sollten anschließend mit \`/analyze <TICKER>\` geprüft werden.

**Strategie:** ${strategy} · **Universum durchsucht:** ${universe.length} · **angereichert:** ${Math.min(enrichLimit, universe.length)}

${header}
${top.map(fmtRow).join("\n")}
`;
  writeFileSync(`screen_results/${strategy}_${date}.md`, md);
  writeFileSync("screen_results/latest_shortlist.txt", top.map(r => r.symbol).join("\n") + "\n");

  console.log(md);
  console.error(`\nGespeichert: screen_results/${strategy}_${date}.md  und  screen_results/latest_shortlist.txt`);
})().catch(e => { console.error("Screener-Fehler:", e.message); process.exit(1); });
