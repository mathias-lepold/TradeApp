"""
PortfolioAnalyzer — analysiert Klumpenrisiken, Regionen, Sektoren,
Währungsrisiken und liefert je Position eine vollständige, schrittweise
hergeleitete Handlungsempfehlung.

Herleitung pro Position:
  1. Fundamentaldaten
  2. Marktumfeld / Regime
  3. Geopolitik
  4. Psychologie
  5. Liquidität
  6. Einpreisung (technisch)
  7. Finale Empfehlung

Mögliche Aktionen: buy | accumulate | hold | reduce | sell | watch
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel


# ── Schemas ───────────────────────────────────────────────────────────────────

class DerivationStep(BaseModel):
    step: int
    label: str             # z.B. "Fundamentaldaten"
    finding: str           # Was wurde gefunden
    signal: str            # "bullish" | "bearish" | "neutral"


class PositionAnalysis(BaseModel):
    symbol: str
    name: str
    action: str            # buy | accumulate | hold | reduce | sell | watch
    conviction: str        # high | medium | low
    score: float           # 0–100
    derivation: List[DerivationStep]
    summary: str           # Kurzfassung der Empfehlung
    key_risk: str
    price_target: Optional[float] = None
    stop_loss: Optional[float] = None


class ClusterRisk(BaseModel):
    type: str              # "sector" | "region" | "currency"
    label: str
    weight_pct: float
    symbols: List[str]
    risk_level: str        # "low" | "medium" | "high"
    comment: str


class PortfolioAnalysisResult(BaseModel):
    overall_score: float          # 0–100 (Portfolio-Qualität)
    diversification_score: float  # 0–100
    region_weights: Dict[str, float]     # {"USA": 68.2, "Schweiz": 31.8}
    sector_weights: Dict[str, float]     # {"Technology": 55.0, ...}
    currency_weights: Dict[str, float]   # {"USD": 62.0, "CHF": 38.0}
    cluster_risks: List[ClusterRisk]
    position_analyses: List[PositionAnalysis]
    portfolio_comment: str


# ── Region / Sektor / Währungs-Mapping ───────────────────────────────────────

_REGION_MAP: Dict[str, str] = {
    "MSFT":  "USA",
    "NVDA":  "USA",
    "AAPL":  "USA",
    "NOVN":  "Schweiz",
    "ZGLD":  "Schweiz",
    "TSLA":  "USA",
    "AMZN":  "USA",
    "GOOGL": "USA",
}

_SECTOR_MAP: Dict[str, str] = {
    "MSFT":  "Technology",
    "NVDA":  "Technology",
    "AAPL":  "Technology",
    "NOVN":  "Healthcare",
    "ZGLD":  "Commodities",
}

_ACTION_LABELS: Dict[str, str] = {
    "buy":        "Kaufen",
    "accumulate": "Nachkaufen",
    "hold":       "Halten",
    "reduce":     "Reduzieren",
    "sell":       "Verkaufen",
    "watch":      "Beobachten",
}


# ── Analyzer ──────────────────────────────────────────────────────────────────

class PortfolioAnalyzer:

    def analyze(
        self,
        positions: List[Dict],
        price_cache: Dict[str, float],
        price_histories: Dict[str, List[float]],
        fund_scores: Dict[str, Dict[str, int]],
        regime_type: str = "bull_market",
        vix: float = 20.0,
        fear_greed: float = 50.0,
        fed_rate: float = 3.5,
        usd_chf: float = 0.90,
    ) -> PortfolioAnalysisResult:
        """Vollständige Portfolio-Analyse."""

        # ── Gewichte berechnen ──
        total_value = sum(
            price_cache.get(p["symbol"], p.get("avg_price", 100))
            * p["quantity"]
            * (usd_chf if p.get("currency") == "USD" else 1.0)
            for p in positions
        )
        if total_value == 0:
            total_value = 1.0

        # ── Regionen / Sektoren / Währungen ──
        region_w: Dict[str, float] = {}
        sector_w: Dict[str, float] = {}
        ccy_w:    Dict[str, float] = {}

        for p in positions:
            sym     = p["symbol"]
            price   = price_cache.get(sym, p.get("avg_price", 100))
            fx      = usd_chf if p.get("currency") == "USD" else 1.0
            val     = price * p["quantity"] * fx
            weight  = val / total_value * 100

            region = _REGION_MAP.get(sym, "Andere")
            sector = _SECTOR_MAP.get(sym, p.get("sector", "Andere"))
            ccy    = p.get("currency", "USD")

            region_w[region] = round(region_w.get(region, 0) + weight, 1)
            sector_w[sector] = round(sector_w.get(sector, 0) + weight, 1)
            ccy_w[ccy]       = round(ccy_w.get(ccy, 0) + weight, 1)

        # ── Klumpenrisiken ──
        cluster_risks = self._detect_cluster_risks(region_w, sector_w, ccy_w)

        # ── Diversifikations-Score ──
        div_score = self._diversification_score(region_w, sector_w, ccy_w, len(positions))

        # ── Positions-Einzelanalysen ──
        position_analyses: List[PositionAnalysis] = []
        for p in positions:
            pa = self._analyze_position(
                p, price_cache, price_histories, fund_scores,
                regime_type, vix, fear_greed, fed_rate, total_value
            )
            position_analyses.append(pa)

        # ── Overall Score ──
        avg_pos_score = (
            sum(pa.score for pa in position_analyses) / len(position_analyses)
            if position_analyses else 50
        )
        overall_score = round(avg_pos_score * 0.6 + div_score * 0.4, 1)

        # ── Portfolio-Kommentar ──
        comment = self._portfolio_comment(
            overall_score, div_score, region_w, sector_w,
            regime_type, vix, fear_greed, cluster_risks
        )

        return PortfolioAnalysisResult(
            overall_score=overall_score,
            diversification_score=div_score,
            region_weights=region_w,
            sector_weights=sector_w,
            currency_weights=ccy_w,
            cluster_risks=cluster_risks,
            position_analyses=position_analyses,
            portfolio_comment=comment,
        )

    # ── Positions-Analyse ──────────────────────────────────────────────────────

    def _analyze_position(
        self,
        pos: Dict,
        price_cache: Dict[str, float],
        price_histories: Dict[str, List[float]],
        fund_scores: Dict[str, Dict[str, int]],
        regime_type: str,
        vix: float,
        fear_greed: float,
        fed_rate: float,
        total_value: float,
    ) -> PositionAnalysis:
        sym    = pos["symbol"]
        name   = pos.get("name", sym)
        price  = price_cache.get(sym, pos.get("avg_price", 100))
        avg    = pos.get("avg_price", price)
        fund   = fund_scores.get(sym, {})
        hist   = price_histories.get(sym, [])

        fund_val   = fund.get("fundamental",  70)
        mgmt_val   = fund.get("management",   75)
        geo_val    = fund.get("geopolitical", 60)
        macro_val  = fund.get("macro",        65)

        derivation: List[DerivationStep] = []
        score_acc  = 0.0

        # ── Schritt 1: Fundamentaldaten ──
        fund_signal = "bullish" if fund_val >= 75 else ("bearish" if fund_val < 55 else "neutral")
        derivation.append(DerivationStep(
            step=1, label="Fundamentaldaten",
            finding=f"Fund-Score {fund_val}/100, Management {mgmt_val}/100",
            signal=fund_signal,
        ))
        score_acc += fund_val * 0.25

        # ── Schritt 2: Marktumfeld / Regime ──
        regime_signal, regime_note = self._regime_signal(regime_type, vix)
        derivation.append(DerivationStep(
            step=2, label="Marktumfeld (Regime)",
            finding=regime_note,
            signal=regime_signal,
        ))
        regime_boost = 5 if regime_signal == "bullish" else (-5 if regime_signal == "bearish" else 0)
        score_acc += (fund_val + regime_boost) * 0.20

        # ── Schritt 3: Geopolitik ──
        geo_signal = "bullish" if geo_val >= 75 else ("bearish" if geo_val < 50 else "neutral")
        derivation.append(DerivationStep(
            step=3, label="Geopolitik",
            finding=f"Geopolitischer Score {geo_val}/100, Makro {macro_val}/100",
            signal=geo_signal,
        ))
        score_acc += geo_val * 0.15

        # ── Schritt 4: Psychologie ──
        psych_signal, psych_note = self._psych_signal(fear_greed)
        derivation.append(DerivationStep(
            step=4, label="Psychologie (Fear & Greed)",
            finding=psych_note,
            signal=psych_signal,
        ))
        psych_score = 50 + (50 - abs(fear_greed - 50)) * 0.5
        score_acc += psych_score * 0.15

        # ── Schritt 5: Liquidität ──
        liq_signal, liq_note = self._liquidity_signal(vix, fed_rate)
        derivation.append(DerivationStep(
            step=5, label="Liquidität",
            finding=liq_note,
            signal=liq_signal,
        ))
        liq_score = 70 if liq_signal == "bullish" else (45 if liq_signal == "bearish" else 58)
        score_acc += liq_score * 0.10

        # ── Schritt 6: Einpreisung (technisch) ──
        tech_signal, tech_note, price_target, stop_loss = self._technical_signal(hist, price, avg)
        derivation.append(DerivationStep(
            step=6, label="Einpreisung / Technisch",
            finding=tech_note,
            signal=tech_signal,
        ))
        tech_score = 70 if tech_signal == "bullish" else (40 if tech_signal == "bearish" else 55)
        score_acc += tech_score * 0.15

        # ── Schritt 7: Finale Empfehlung ──
        final_score = round(score_acc, 1)
        action = self._derive_action(
            final_score, tech_signal, regime_signal, geo_signal, fund_val, fear_greed
        )
        conviction = "high" if final_score >= 70 else ("medium" if final_score >= 55 else "low")

        summary = self._build_summary(sym, name, action, final_score, derivation, regime_type)
        key_risk = self._key_risk(sym, regime_type, vix, geo_val, liq_signal)

        derivation.append(DerivationStep(
            step=7, label="Finale Empfehlung",
            finding=f"Gesamt-Score {final_score:.0f}/100 → {_ACTION_LABELS.get(action, action)} (Conviction: {conviction})",
            signal="bullish" if action in ("buy", "accumulate") else (
                "bearish" if action in ("sell", "reduce") else "neutral"
            ),
        ))

        return PositionAnalysis(
            symbol=sym,
            name=name,
            action=action,
            conviction=conviction,
            score=final_score,
            derivation=derivation,
            summary=summary,
            key_risk=key_risk,
            price_target=price_target,
            stop_loss=stop_loss,
        )

    # ── Helper-Methoden ────────────────────────────────────────────────────────

    def _regime_signal(self, regime_type: str, vix: float) -> Tuple[str, str]:
        if "crisis" in regime_type:
            return "bearish", f"Krisenregime aktiv, VIX {vix:.0f} — Risk-Off"
        if "bear" in regime_type:
            return "bearish", f"Bear Market, VIX {vix:.0f} — defensive Positionierung"
        if "bull" in regime_type:
            return "bullish", f"Bull Market, VIX {vix:.0f} — risikofreundliches Umfeld"
        return "neutral", f"Sideways/Recovery-Regime, VIX {vix:.0f}"

    def _psych_signal(self, fear_greed: float) -> Tuple[str, str]:
        if fear_greed < 25:
            return "bullish", f"Extreme Angst (F&G {fear_greed:.0f}) — konträr bullish"
        if fear_greed > 75:
            return "bearish", f"Extreme Gier (F&G {fear_greed:.0f}) — Überhitzungsrisiko"
        if fear_greed < 40:
            return "neutral", f"Angst-Modus (F&G {fear_greed:.0f}) — erhöhte Vorsicht"
        return "neutral", f"Neutrale Stimmung (F&G {fear_greed:.0f})"

    def _liquidity_signal(self, vix: float, fed_rate: float) -> Tuple[str, str]:
        if vix > 35 or fed_rate > 5:
            return "bearish", f"Liquiditätsstress: VIX {vix:.0f}, Fed {fed_rate:.2f}%"
        if vix > 25 or fed_rate > 4:
            return "neutral", f"Moderate Liquiditätsspannung: VIX {vix:.0f}, Fed {fed_rate:.2f}%"
        return "bullish", f"Gute Liquidität: VIX {vix:.0f}, Fed {fed_rate:.2f}%"

    def _technical_signal(
        self, hist: List[float], price: float, avg_entry: float
    ) -> Tuple[str, str, Optional[float], Optional[float]]:
        if len(hist) < 10:
            return "neutral", "Zu wenig Preisdaten für techn. Analyse", None, None

        ma20  = sum(hist[-20:]) / min(len(hist), 20)
        ma50  = sum(hist[-50:]) / min(len(hist), 50)
        pnl   = (price - avg_entry) / avg_entry * 100

        # Einfaches RSI-Proxy aus letzten 14 Perioden
        gains  = [max(0, hist[i] - hist[i-1]) for i in range(max(1, len(hist)-14), len(hist))]
        losses = [max(0, hist[i-1] - hist[i]) for i in range(max(1, len(hist)-14), len(hist))]
        avg_g  = sum(gains)  / 14 if gains  else 0
        avg_l  = sum(losses) / 14 if losses else 0.001
        rsi    = 100 - 100 / (1 + avg_g / avg_l)

        price_target = round(price * 1.15, 2)
        stop_loss    = round(price * 0.92, 2)

        if price > ma20 > ma50 and rsi < 70:
            signal = "bullish"
            note = f"Preis über MA20/MA50, RSI {rsi:.0f}, PnL {pnl:+.1f}%"
        elif price < ma20 < ma50 or rsi > 75:
            signal = "bearish"
            note = f"Preis unter MA20/MA50 oder überkauft (RSI {rsi:.0f}), PnL {pnl:+.1f}%"
        else:
            signal = "neutral"
            note = f"Gemischtes Bild: RSI {rsi:.0f}, PnL {pnl:+.1f}%, MA20 {ma20:.0f}"

        return signal, note, price_target, stop_loss

    def _derive_action(
        self,
        score: float,
        tech: str,
        regime: str,
        geo: str,
        fund_val: int,
        fear_greed: float,
    ) -> str:
        if score >= 72 and tech != "bearish" and regime != "bearish":
            return "buy" if fear_greed < 60 else "accumulate"
        if score >= 60 and regime != "bearish":
            return "accumulate" if tech == "bullish" else "hold"
        if score >= 50:
            return "hold"
        if score >= 40:
            return "reduce" if regime == "bearish" else "watch"
        return "sell"

    def _build_summary(
        self,
        sym: str,
        name: str,
        action: str,
        score: float,
        derivation: List[DerivationStep],
        regime_type: str,
    ) -> str:
        signals = [d.signal for d in derivation[:6]]
        bull = signals.count("bullish")
        bear = signals.count("bearish")
        action_label = _ACTION_LABELS.get(action, action)
        return (
            f"{name} ({sym}): {action_label} — Score {score:.0f}/100. "
            f"{bull} von 6 Faktoren bullish, {bear} bearish. "
            f"Regime: {regime_type.replace('_', ' ').title()}."
        )

    def _key_risk(
        self, sym: str, regime_type: str, vix: float, geo_val: int, liq_signal: str
    ) -> str:
        risks = []
        if "crisis" in regime_type:
            risks.append("Krisenregime — erhöhter Drawdown-Risk")
        if vix > 30:
            risks.append(f"Hoher VIX ({vix:.0f}) — Volatilitätsrisiko")
        if geo_val < 55:
            risks.append("Geopolitische Unsicherheit")
        if liq_signal == "bearish":
            risks.append("Liquiditätsstress")
        if sym in ("NVDA", "MSFT", "AAPL"):
            risks.append("Tech-Sektorkonzentration")
        return " | ".join(risks) if risks else "Kein dominantes Risiko identifiziert"

    # ── Cluster-Risiken ────────────────────────────────────────────────────────

    def _detect_cluster_risks(
        self,
        region_w: Dict[str, float],
        sector_w: Dict[str, float],
        ccy_w:    Dict[str, float],
    ) -> List[ClusterRisk]:
        risks: List[ClusterRisk] = []

        # Regionen
        for region, w in region_w.items():
            if w >= 60:
                risks.append(ClusterRisk(
                    type="region", label=f"Region: {region}",
                    weight_pct=w,
                    symbols=[s for s, r in _REGION_MAP.items() if r == region],
                    risk_level="high" if w >= 75 else "medium",
                    comment=f"{w:.1f}% des Portfolios in {region} — Klumpenrisiko"
                        if w >= 75 else f"{w:.1f}% in {region}",
                ))

        # Sektoren
        for sector, w in sector_w.items():
            if w >= 50:
                risks.append(ClusterRisk(
                    type="sector", label=f"Sektor: {sector}",
                    weight_pct=w,
                    symbols=[s for s, sec in _SECTOR_MAP.items() if sec == sector],
                    risk_level="high" if w >= 65 else "medium",
                    comment=f"{w:.1f}% in {sector} — Sektorkonzentration"
                        if w >= 65 else f"{w:.1f}% in {sector}",
                ))

        # Währungen
        for ccy, w in ccy_w.items():
            if w >= 55:
                risks.append(ClusterRisk(
                    type="currency", label=f"Währung: {ccy}",
                    weight_pct=w,
                    symbols=[],
                    risk_level="medium",
                    comment=f"{w:.1f}% in {ccy} — Währungsrisiko beachten",
                ))

        return risks

    # ── Diversifikations-Score ─────────────────────────────────────────────────

    def _diversification_score(
        self,
        region_w: Dict[str, float],
        sector_w: Dict[str, float],
        ccy_w:    Dict[str, float],
        n_positions: int,
    ) -> float:
        """Herfindahl-ähnlicher Score: je gleichmäßiger verteilt, desto höher."""
        def hhi_score(weights: Dict[str, float]) -> float:
            total = sum(weights.values()) or 1
            hhi = sum((w / total) ** 2 for w in weights.values())
            # HHI 1.0 = vollständige Konzentration → Score 0
            # HHI 1/n = perfekte Verteilung → Score 100
            n = len(weights) or 1
            min_hhi = 1 / n
            return max(0, min(100, (1 - hhi) / (1 - min_hhi) * 100)) if n > 1 else 30

        region_score  = hhi_score(region_w)
        sector_score  = hhi_score(sector_w)
        ccy_score     = hhi_score(ccy_w)
        n_score       = min(100, n_positions * 20)  # 5+ Positionen = 100

        return round(
            region_score * 0.35 + sector_score * 0.35 + ccy_score * 0.15 + n_score * 0.15,
            1
        )

    # ── Portfolio-Kommentar ────────────────────────────────────────────────────

    def _portfolio_comment(
        self,
        overall: float,
        div: float,
        region_w: Dict[str, float],
        sector_w: Dict[str, float],
        regime_type: str,
        vix: float,
        fear_greed: float,
        cluster_risks: List[ClusterRisk],
    ) -> str:
        parts = []

        if overall >= 70:
            parts.append("Portfolio gut positioniert")
        elif overall >= 55:
            parts.append("Portfolio moderat aufgestellt")
        else:
            parts.append("Portfolio mit erhöhtem Risiko")

        if div < 50:
            parts.append("Diversifikation unzureichend — Klumpenrisiken reduzieren")
        elif div < 70:
            parts.append("Diversifikation verbesserungswürdig")

        high_risks = [r for r in cluster_risks if r.risk_level == "high"]
        if high_risks:
            labels = [r.label for r in high_risks[:2]]
            parts.append(f"Kritische Konzentration: {', '.join(labels)}")

        if "crisis" in regime_type:
            parts.append("Krisenregime: Cash-Buffer und Hedges empfohlen")
        elif "bull" in regime_type and fear_greed > 70:
            parts.append("Bull Market mit hoher Gier — Gewinne absichern")

        if vix > 30:
            parts.append(f"VIX {vix:.0f}: Volatilitätsschutz prüfen")

        return " | ".join(parts) + "."
