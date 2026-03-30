"""Service: AlertService — Kursalarme mit Background-Checker."""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Callable, List, Optional

from app.domain.alerts import AlertConfig, AlertCreate, AlertCondition, AlertEvent


class AlertService:
    def __init__(self) -> None:
        self._alerts: List[AlertConfig] = []
        self._history: List[AlertEvent] = []
        self._last_regime: Optional[str] = None

    async def load_from_db(self) -> None:
        try:
            from sqlalchemy import select
            from app.services.database import AsyncSessionLocal
            from app.models.alert import AlertModel

            async with AsyncSessionLocal() as session:
                rows = (await session.execute(select(AlertModel))).scalars().all()

            if rows:
                self._alerts = []
                for r in rows:
                    # Map DB columns (type, direction) → AlertCondition
                    cond_key = f"{r.type}_{r.direction}"
                    try:
                        cond = AlertCondition(cond_key)
                    except ValueError:
                        cond = AlertCondition.price_above
                    self._alerts.append(AlertConfig(
                        id=r.id, symbol=r.symbol,
                        condition=cond, threshold=float(r.threshold),
                        triggered=r.triggered,
                        triggered_at=r.triggered_at,
                        created_at=r.created_at,
                    ))
                print(f"[AlertService] {len(self._alerts)} Alerts aus DB geladen")
        except Exception as exc:
            print(f"[AlertService] DB nicht verfügbar — In-Memory: {exc}")

    def get_alerts(self) -> List[AlertConfig]:
        return sorted(self._alerts, key=lambda a: a.created_at, reverse=True)

    def get_history(self) -> List[AlertEvent]:
        return sorted(self._history, key=lambda e: e.triggered_at, reverse=True)

    async def create_alert(self, data: AlertCreate) -> AlertConfig:
        alert = AlertConfig(
            id=str(uuid.uuid4()),
            symbol=data.symbol.upper(),
            condition=data.condition,
            threshold=data.threshold,
            notes=data.notes,
            created_at=datetime.now(tz=timezone.utc),
        )
        self._alerts.append(alert)
        await self._persist(alert)
        return alert

    async def delete_alert(self, alert_id: str) -> bool:
        before = len(self._alerts)
        self._alerts = [a for a in self._alerts if a.id != alert_id]
        deleted = len(self._alerts) < before
        if deleted:
            await self._delete_from_db(alert_id)
        return deleted

    async def check_alerts(
        self,
        price_fn:  Callable[[str], float],
        score_fn:  Optional[Callable[[str], Optional[int]]] = None,
        regime:    Optional[str] = None,
    ) -> List[AlertEvent]:
        """Prüft alle aktiven Alerts. Gibt neu ausgelöste zurück."""
        triggered_now: List[AlertEvent] = []

        for alert in self._alerts:
            if not alert.active or alert.triggered:
                continue

            cond = alert.condition
            sym  = alert.symbol
            fired = False
            val   = 0.0

            if cond == AlertCondition.price_above:
                val = price_fn(sym)
                fired = val >= alert.threshold

            elif cond == AlertCondition.price_below:
                val = price_fn(sym)
                fired = val <= alert.threshold

            elif cond == AlertCondition.signal_score_above and score_fn:
                sc = score_fn(sym)
                if sc is not None:
                    val = float(sc)
                    fired = val >= alert.threshold

            elif cond == AlertCondition.signal_score_below and score_fn:
                sc = score_fn(sym)
                if sc is not None:
                    val = float(sc)
                    fired = val <= alert.threshold

            elif cond == AlertCondition.regime_change and regime:
                if self._last_regime and self._last_regime != regime:
                    val = 0.0
                    fired = True

            if fired:
                now = datetime.now(tz=timezone.utc)
                alert.triggered = True
                alert.triggered_at = now
                alert.triggered_value = val

                msg = _build_message(alert, val, regime)
                event = AlertEvent(
                    alert_id=alert.id, symbol=sym,
                    condition=cond, threshold=alert.threshold,
                    triggered_value=val, triggered_at=now, message=msg,
                )
                self._history.append(event)
                triggered_now.append(event)
                await self._update_triggered_db(alert.id, now)
                print(f"[AlertService] AUSGELÖST: {msg}")

        if regime:
            self._last_regime = regime

        return triggered_now

    async def run_background_checker(
        self,
        price_fn:  Callable[[str], float],
        score_fn:  Optional[Callable[[str], Optional[int]]] = None,
        regime_fn: Optional[Callable[[], str]] = None,
        interval:  int = 30,
    ) -> None:
        """Läuft dauerhaft als asyncio-Task."""
        print("[AlertService] Background-Checker gestartet (alle 30s)")
        while True:
            try:
                regime = regime_fn() if regime_fn else None
                await self.check_alerts(price_fn, score_fn, regime)
            except Exception as exc:
                print(f"[AlertService] Checker-Fehler: {exc}")
            await asyncio.sleep(interval)

    # ── DB ─────────────────────────────────────────────────────────────────────

    async def _persist(self, alert: AlertConfig) -> None:
        try:
            from app.services.database import AsyncSessionLocal
            from app.models.alert import AlertModel
            ctype, cdir = _condition_to_db(alert.condition)
            async with AsyncSessionLocal() as session:
                row = AlertModel(
                    id=alert.id, symbol=alert.symbol,
                    type=ctype, threshold=alert.threshold,
                    direction=cdir, triggered=False,
                    created_at=alert.created_at,
                )
                session.add(row)
                await session.commit()
        except Exception:
            pass

    async def _update_triggered_db(self, alert_id: str, ts: datetime) -> None:
        try:
            from sqlalchemy import update
            from app.services.database import AsyncSessionLocal
            from app.models.alert import AlertModel
            async with AsyncSessionLocal() as session:
                await session.execute(
                    update(AlertModel)
                    .where(AlertModel.id == alert_id)
                    .values(triggered=True, triggered_at=ts)
                )
                await session.commit()
        except Exception:
            pass

    async def _delete_from_db(self, alert_id: str) -> None:
        try:
            from sqlalchemy import delete
            from app.services.database import AsyncSessionLocal
            from app.models.alert import AlertModel
            async with AsyncSessionLocal() as session:
                await session.execute(delete(AlertModel).where(AlertModel.id == alert_id))
                await session.commit()
        except Exception:
            pass


def _condition_to_db(cond: AlertCondition):
    mapping = {
        AlertCondition.price_above:        ("price",        "above"),
        AlertCondition.price_below:        ("price",        "below"),
        AlertCondition.signal_score_above: ("signal_score", "above"),
        AlertCondition.signal_score_below: ("signal_score", "below"),
        AlertCondition.regime_change:      ("regime",       "above"),
    }
    return mapping.get(cond, ("price", "above"))


def _build_message(alert: AlertConfig, val: float, regime: Optional[str]) -> str:
    sym = alert.symbol
    thr = alert.threshold
    cond = alert.condition
    if cond == AlertCondition.price_above:
        return f"{sym} Kurs {val:.2f} übersteigt Schwelle {thr:.2f}"
    if cond == AlertCondition.price_below:
        return f"{sym} Kurs {val:.2f} unterschreitet Schwelle {thr:.2f}"
    if cond == AlertCondition.signal_score_above:
        return f"{sym} Signal-Score {val:.0f} über Schwelle {thr:.0f}"
    if cond == AlertCondition.signal_score_below:
        return f"{sym} Signal-Score {val:.0f} unter Schwelle {thr:.0f}"
    if cond == AlertCondition.regime_change:
        return f"Regimewechsel erkannt: {regime}"
    return f"Alert ausgelöst: {sym}"
