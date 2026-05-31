#!/usr/bin/env node
// build_dashboard.mjs - erzeugt aus deinen Analysen EIN in sich geschlossenes HTML-Dashboard.
//
// Liest:
//   watchlist.md                      -> Kern-Portfolio
//   research/<TICKER>/00_REPORT.md     -> Ampel, Kurs, faire Wertspanne, Pro/Contra je Aktie
//   screen_results/<strategie>_*.md    -> letztes Screening-Ergebnis
//
// Schreibt:
//   dashboard.html  (oder ein eigener Pfad als 1. Argument, z.B. dein OneDrive-Ordner)
//
// Nutzung:
//   node scripts/build_dashboard.mjs
//   node scripts/build_dashboard.mjs "C:/Users/Mathias Lepold/OneDrive/dashboard.html"
//
// Benoetigt keine externen Pakete.

import { readFileSync, writeFileSync, existsSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";

const OUT = process.argv[2] || "dashboard.html";
const ROOT = process.cwd();
const read = p => (existsSync(p) ? readFileSync(p, "utf8") : "");
const esc = s => String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

// ---------- Watchlist (Kern-Portfolio) ----------
function parseWatchlist() {
  const txt = read(join(ROOT, "watchlist.md"));
  // Abschnitt zwischen "Kern-Portfolio" und der naechsten "## "-Ueberschrift
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

  // Ampel: in der Einschaetzungs-Zeile. Vorlage enthaelt alle drei (🟢 / 🟡 / 🔴) -> dann unbekannt.
  const ampelLine = (t.match(/Ampel:[^\n]*/) || [""])[0];
  let ampel = "";
  const filledTemplate = /🟢\s*\/\s*🟡\s*\/\s*🔴/.test(ampelLine);
  if (!filledTemplate) ampel = AMPELS.find(a => ampelLine.includes(a)) || "";
  const begruendung = (ampelLine.split(/[—-]/).slice(1).join("-")).replace(/\*/g, "").trim();

  const listAfter = (heading) => {
    const idx = t.indexOf(heading);
    if (idx < 0) return [];
    const after = t.slice(idx + heading.length);
    const block = after.slice(0, after.search(/\n##?\s/) >= 0 ? after.search(/\n##?\s/) : after.length);
    return block.split("\n")
      .map(l => l.replace(/^\s*(\d+\.|[-*])\s*/, "").trim())
      .filter(l => l && l !== "…" && !/^\d+\.\s*…?$/.test(l))
      .slice(0, 3);
  };

  return {
    company: m(/Gesamt-Report:\s*(.+?)\s*\(/),
    date: m(/Analysedatum:\**\s*([0-9]{4}-[0-9]{2}-[0-9]{2})/),
    price: m(/Aktueller Kurs:\**\s*([^()\n·*]+)/),
    ampel,
    begruendung,
    fairValue: m(/Faire Wertspanne[^|]*\|\s*([^|]+?)\s*\|/),
    sector: m(/Sektor\/Branche:\**\s*([^\n]+)/).replace(/\*/g, ""),
    marketCap: m(/Marktkapitalisierung:\**\s*([^\n]+)/).replace(/\*/g, ""),
    pros: listAfter("Top-3 Pro"),
    contras: listAfter("Top-3 Contra"),
  };
}

// ---------- Letztes Screening ----------
function parseLatestScreen() {
  const dir = join(ROOT, "screen_results");
  if (!existsSync(dir)) return null;
  const files = readdirSync(dir).filter(f => f.endsWith(".md"));
  if (!files.length) return null;
  files.sort((a, b) => statSync(join(dir, b)).mtimeMs - statSync(join(dir, a)).mtimeMs);
  const txt = read(join(dir, files[0]));
  const title = (txt.match(/^#\s+(.+)/m) || [])[1] || files[0];
  const rows = [];
  for (const line of txt.split("\n")) {
    if (!line.trim().startsWith("|")) continue;
    const cells = line.split("|").slice(1, -1).map(c => c.trim());
    if (cells.length < 2) continue;
    if (/^#$/.test(cells[0]) || /^-+$/.test(cells[0])) continue;
    rows.push(cells);
  }
  return { title, rows };
}

// ---------- Hilfen fuer faire Wertspanne ----------
const firstNum = s => { const m = String(s).replace(/[.,](?=\d{3}\b)/g, "").match(/-?\d+(?:[.,]\d+)?/); return m ? parseFloat(m[0].replace(",", ".")) : NaN; };
function rangePosition(price, fair) {
  const p = firstNum(price);
  const nums = String(fair).match(/-?\d+(?:[.,]\d+)?/g);
  if (!Number.isFinite(p) || !nums || nums.length < 2) return null;
  const lo = parseFloat(nums[0].replace(",", ".")), hi = parseFloat(nums[nums.length - 1].replace(",", "."));
  if (!(hi > lo)) return null;
  const pct = Math.max(0, Math.min(100, ((p - lo) / (hi - lo)) * 100));
  const label = p < lo ? "unter der Spanne" : p > hi ? "über der Spanne" : "innerhalb der Spanne";
  return { pct, label };
}

// ---------- HTML bauen ----------
const ampelClass = a => (a === "🟢" ? "g" : a === "🟡" ? "y" : a === "🔴" ? "r" : "n");
const ampelText = a => (a === "🟢" ? "Günstig / interessant" : a === "🟡" ? "Neutral / beobachten" : a === "🔴" ? "Vorsicht / teuer" : "Noch nicht analysiert");

function card(row) {
  const rep = parseReport(row.ticker);
  const ampel = (rep && rep.ampel) || (AMPELS.includes(row.wlAmpel) ? row.wlAmpel : "");
  const cls = ampelClass(ampel);
  const analyzed = !!rep;
  const name = (rep && rep.company) || row.name || "";

  let body = "";
  if (analyzed) {
    const pos = rangePosition(rep.price, rep.fairValue);
    const bar = pos ? `<div class="bar"><span style="left:${pos.pct.toFixed(0)}%"></span></div>
        <div class="muted small">Kurs ${pos.label}</div>` : "";
    const fv = rep.fairValue ? `<div class="kv"><span>Faire Spanne</span><b>${esc(rep.fairValue)}</b></div>` : "";
    const pr = rep.price ? `<div class="kv"><span>Kurs</span><b>${esc(rep.price)}</b></div>` : "";
    const pros = rep.pros.length ? `<b>✅ Pro</b><ul>${rep.pros.map(x => `<li>${esc(x)}</li>`).join("")}</ul>` : "";
    const cons = rep.contras.length ? `<b>⛔ Contra</b><ul>${rep.contras.map(x => `<li>${esc(x)}</li>`).join("")}</ul>` : "";
    body = `
      ${rep.begruendung ? `<p class="reason">${esc(rep.begruendung)}</p>` : ""}
      ${pr}${fv}${bar}
      ${rep.date ? `<div class="kv"><span>Analysiert</span><b>${esc(rep.date)}</b></div>` : ""}
      ${(pros || cons) ? `<details><summary>Details</summary>${pros}${cons}</details>` : ""}`;
  } else {
    body = `<p class="muted">Noch nicht analysiert.${row.notiz ? " " + esc(row.notiz) : ""}</p>
      <div class="muted small">Tipp: <code>/analyze ${esc(row.ticker)}</code></div>`;
  }

  return `<article class="card ${cls}">
    <header><div><span class="ticker">${esc(row.ticker)}</span> <span class="muted">${esc(name)}</span></div>
      <span class="dot ${cls}" title="${esc(ampelText(ampel))}"></span></header>
    <div class="typ">${esc(row.typ || "")}</div>
    ${body}
  </article>`;
}

function buildScreenSection(scr) {
  if (!scr) return `<p class="muted">Noch kein Screening durchgeführt. Tipp: <code>/screen quality-growth</code></p>`;
  const head = scr.rows[0];
  const data = scr.rows.slice(1);
  return `<h3>${esc(scr.title)}</h3>
    <div class="tablewrap"><table>
      <thead><tr>${head.map(h => `<th>${esc(h)}</th>`).join("")}</tr></thead>
      <tbody>${data.map(r => `<tr>${r.map(c => `<td>${esc(c)}</td>`).join("")}</tr>`).join("")}</tbody>
    </table></div>`;
}

// ---------- Zusammenbau ----------
const core = parseWatchlist();
const reports = core.map(r => ({ r, rep: parseReport(r.ticker) }));
const count = a => reports.filter(x => ((x.rep && x.rep.ampel) || x.r.wlAmpel) === a).length;
const analyzedCount = reports.filter(x => x.rep).length;
const screen = parseLatestScreen();
const now = new Date();
const stamp = now.toISOString().slice(0, 16).replace("T", " ");

const html = `<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="Finanzen">
<meta name="theme-color" content="#ffffff">
<title>Mein Finanz-Dashboard</title>
<style>
  :root{--g:#16a34a;--y:#d97706;--r:#dc2626;--n:#9ca3af;--bg:#f7f8fa;--card:#fff;--bd:#e5e7eb;--tx:#111827;--mut:#6b7280}
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--tx);font:16px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;padding:env(safe-area-inset-top) 0 40px}
  .wrap{max-width:1100px;margin:0 auto;padding:0 16px}
  header.top{padding:24px 0 8px}
  h1{font-size:24px;margin:0 0 2px}
  .sub{color:var(--mut);font-size:14px}
  .disclaimer{background:#fff7ed;border:1px solid #fed7aa;color:#9a3412;border-radius:10px;padding:10px 14px;font-size:13px;margin:14px 0}
  .stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:10px;margin:16px 0 8px}
  .stat{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:12px 14px;text-align:center}
  .stat .num{font-size:24px;font-weight:700}
  .stat.g .num{color:var(--g)}.stat.y .num{color:var(--y)}.stat.r .num{color:var(--r)}
  .stat .lbl{font-size:12px;color:var(--mut)}
  h2{font-size:18px;margin:28px 0 12px}
  .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px}
  .card{background:var(--card);border:1px solid var(--bd);border-left:5px solid var(--n);border-radius:14px;padding:14px 16px;box-shadow:0 1px 2px rgba(0,0,0,.04)}
  .card.g{border-left-color:var(--g)}.card.y{border-left-color:var(--y)}.card.r{border-left-color:var(--r)}
  .card header{display:flex;justify-content:space-between;align-items:center;gap:8px;border:0;padding:0}
  .ticker{font-weight:700;font-size:18px}
  .typ{font-size:12px;color:var(--mut);margin:2px 0 8px}
  .dot{width:14px;height:14px;border-radius:50%;background:var(--n);flex:0 0 auto}
  .dot.g{background:var(--g)}.dot.y{background:var(--y)}.dot.r{background:var(--r)}
  .reason{font-size:14px;margin:6px 0 10px}
  .kv{display:flex;justify-content:space-between;font-size:14px;padding:3px 0;border-top:1px dashed var(--bd)}
  .kv span{color:var(--mut)}
  .bar{position:relative;height:6px;background:linear-gradient(90deg,#bbf7d0,#fde68a,#fecaca);border-radius:4px;margin:10px 0 4px}
  .bar span{position:absolute;top:-3px;width:3px;height:12px;background:#111827;transform:translateX(-50%);border-radius:2px}
  .muted{color:var(--mut)}.small{font-size:12px}
  code{background:#eef2ff;color:#3730a3;padding:1px 6px;border-radius:6px;font-size:13px}
  details{margin-top:8px}summary{cursor:pointer;font-size:14px;color:var(--mut)}
  details ul{margin:4px 0 10px;padding-left:18px;font-size:14px}
  .tablewrap{overflow-x:auto;background:var(--card);border:1px solid var(--bd);border-radius:14px}
  table{border-collapse:collapse;width:100%;font-size:14px}
  th,td{padding:8px 12px;text-align:left;border-bottom:1px solid var(--bd);white-space:nowrap}
  th{background:#f3f4f6;color:var(--mut);font-weight:600}
  tr:last-child td{border-bottom:0}
  footer{margin-top:32px;color:var(--mut);font-size:12px;text-align:center}
</style>
</head>
<body>
<div class="wrap">
  <header class="top">
    <h1>📊 Mein Finanz-Dashboard</h1>
    <div class="sub">Stand: ${stamp} · Quelle: eigene Analysen (Claude Code) + Financial Modeling Prep</div>
    <div class="disclaimer">⚠️ Nur zur Information – <b>keine Anlageberatung</b>. Die Ampel ist eine Orientierung, keine Empfehlung. Zahlen an der Primärquelle prüfen.</div>
  </header>

  <div class="stats">
    <div class="stat"><div class="num">${core.length}</div><div class="lbl">Kern-Werte</div></div>
    <div class="stat g"><div class="num">${count("🟢")}</div><div class="lbl">🟢 Günstig</div></div>
    <div class="stat y"><div class="num">${count("🟡")}</div><div class="lbl">🟡 Neutral</div></div>
    <div class="stat r"><div class="num">${count("🔴")}</div><div class="lbl">🔴 Vorsicht</div></div>
    <div class="stat"><div class="num">${analyzedCount}/${core.length}</div><div class="lbl">analysiert</div></div>
  </div>

  <h2>⭐ Kern-Portfolio</h2>
  <div class="grid">${core.map(card).join("")}</div>

  <h2>🔎 Letztes Screening</h2>
  ${buildScreenSection(screen)}

  <footer>Automatisch erstellt mit <code>scripts/build_dashboard.mjs</code> · Keine Anlageberatung.</footer>
</div>
</body>
</html>`;

writeFileSync(OUT, html);
console.log(`✓ Dashboard erstellt: ${OUT}`);
console.log(`  ${core.length} Kern-Werte, davon ${analyzedCount} analysiert (🟢${count("🟢")} 🟡${count("🟡")} 🔴${count("🔴")})`);
console.log(`  Auf dem PC: Datei doppelklicken. Fürs iPhone: in deinen OneDrive-Ordner kopieren.`);
