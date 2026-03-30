"""Initial migration — alle Domain-Tabellen erstellen

Revision ID: 001
Revises:
Create Date: 2026-03-29

Tabellen:
  - assets          (Asset-Stammdaten)
  - events          (Event-Bus-Protokoll)
  - signals         (Handelssignale)
  - regime_states   (Marktregime-Verlauf)
  - recommendations (Entscheidungsempfehlungen)
  - trades          (Trading-Journal)
  - watchlist       (Beobachtungsliste)
  - alerts          (Kursalarme)
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── assets ────────────────────────────────────────────────────────────────
    op.create_table(
        "assets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column(
            "asset_type",
            sa.Enum("stock", "etf", "crypto", "forex", "commodity", "bond", "index", name="asset_type_enum"),
            nullable=False,
        ),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("exchange", sa.String(50), nullable=False),
        sa.Column("sector", sa.String(100)),
        sa.Column("industry", sa.String(100)),
        sa.Column("country", sa.String(2)),
        sa.Column("isin", sa.String(12)),
        sa.Column("last_price", sa.Float()),
        sa.Column("market_cap", sa.Float()),
        sa.Column("avg_daily_volume", sa.Integer()),
        sa.Column(
            "status",
            sa.Enum("active", "halted", "delisted", "watchlist", name="asset_status_enum"),
            nullable=False,
            server_default="active",
        ),
        sa.Column("ibkr_con_id", sa.Integer()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_assets_symbol", "assets", ["symbol"], unique=True)

    # ── events ────────────────────────────────────────────────────────────────
    op.create_table(
        "events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False, server_default="info"),
        sa.Column("symbol", sa.String(20)),
        sa.Column("payload", sa.JSON()),
        sa.Column("parent_id", sa.String(36)),
        sa.Column("correlation_id", sa.String(36)),
        sa.Column("message", sa.Text()),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_events_event_type", "events", ["event_type"])
    op.create_index("ix_events_symbol", "events", ["symbol"])
    op.create_index("ix_events_correlation_id", "events", ["correlation_id"])
    op.create_index("ix_events_occurred_at", "events", ["occurred_at"])

    # ── signals ───────────────────────────────────────────────────────────────
    op.create_table(
        "signals",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("signal_type", sa.String(20), nullable=False),
        sa.Column("strength", sa.String(20), nullable=False),
        sa.Column("confidence", sa.String(20), nullable=False),
        sa.Column("total_score", sa.Float(), nullable=False),
        sa.Column("score_breakdown", sa.JSON()),
        sa.Column("technical_levels", sa.JSON()),
        sa.Column("entry_price", sa.Float()),
        sa.Column("stop_loss", sa.Float()),
        sa.Column("take_profit", sa.Float()),
        sa.Column("reasons", sa.JSON()),
        sa.Column("catalyst", sa.Text()),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_signals_symbol", "signals", ["symbol"])
    op.create_index("ix_signals_created_at", "signals", ["created_at"])

    # ── regime_states ─────────────────────────────────────────────────────────
    op.create_table(
        "regime_states",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("regime_type", sa.String(30), nullable=False),
        sa.Column("sub_regime", sa.String(30)),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("strength", sa.Float(), nullable=False),
        sa.Column("characteristics", sa.JSON()),
        sa.Column("active_risks", sa.JSON()),
        sa.Column("position_sizing_rules", sa.JSON()),
        sa.Column("macro_snapshot", sa.JSON()),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_regime_states_regime_type", "regime_states", ["regime_type"])
    op.create_index("ix_regime_states_detected_at", "regime_states", ["detected_at"])

    # ── recommendations ───────────────────────────────────────────────────────
    op.create_table(
        "recommendations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("action", sa.String(20), nullable=False),
        sa.Column("priority", sa.String(20), nullable=False),
        sa.Column("signal_id", sa.String(36)),
        sa.Column("regime_id", sa.String(36)),
        sa.Column("total_score", sa.Float()),
        sa.Column("bias_risk", sa.JSON()),
        sa.Column("position_sizing", sa.JSON()),
        sa.Column("reasons", sa.JSON()),
        sa.Column("risks", sa.JSON()),
        sa.Column("invalidation_conditions", sa.JSON()),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_recommendations_symbol", "recommendations", ["symbol"])
    op.create_index("ix_recommendations_signal_id", "recommendations", ["signal_id"])
    op.create_index("ix_recommendations_created_at", "recommendations", ["created_at"])

    # ── trades ────────────────────────────────────────────────────────────────
    op.create_table(
        "trades",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("name", sa.String(100)),
        sa.Column("direction", sa.String(4), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("entry_price", sa.Numeric(18, 4), nullable=False),
        sa.Column("exit_price", sa.Numeric(18, 4)),
        sa.Column("stop_loss", sa.Numeric(18, 4)),
        sa.Column("take_profit", sa.Numeric(18, 4)),
        sa.Column("currency", sa.String(3), nullable=False, server_default="CHF"),
        sa.Column("status", sa.String(10), nullable=False, server_default="open"),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("closed_at", sa.DateTime(timezone=True)),
        sa.Column("pnl_chf", sa.Numeric(18, 2)),
        sa.Column("pnl_percent", sa.Numeric(8, 4)),
        sa.Column("holding_days", sa.Integer()),
        sa.Column("score_at_entry", sa.Integer()),
        sa.Column("crv_achieved", sa.Numeric(6, 2)),
        sa.Column("stamp_tax_chf", sa.Numeric(10, 4)),
        sa.Column("bias", sa.JSON()),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_trades_symbol", "trades", ["symbol"])
    op.create_index("ix_trades_status", "trades", ["status"])
    op.create_index("ix_trades_opened_at", "trades", ["opened_at"])

    # ── watchlist ─────────────────────────────────────────────────────────────
    op.create_table(
        "watchlist",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("name", sa.String(100)),
        sa.Column("target_price", sa.Numeric(18, 4)),
        sa.Column("alert_price", sa.Numeric(18, 4)),
        sa.Column("notes", sa.Text()),
        sa.Column("added_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_watchlist_symbol", "watchlist", ["symbol"], unique=True)

    # ── alerts ────────────────────────────────────────────────────────────────
    op.create_table(
        "alerts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("threshold", sa.Numeric(18, 4), nullable=False),
        sa.Column("direction", sa.String(5), nullable=False),
        sa.Column("triggered", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("triggered_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_alerts_symbol", "alerts", ["symbol"])


def downgrade() -> None:
    op.drop_table("alerts")
    op.drop_table("watchlist")
    op.drop_table("trades")
    op.drop_table("recommendations")
    op.drop_table("regime_states")
    op.drop_table("signals")
    op.drop_table("events")
    op.drop_table("assets")
    op.execute("DROP TYPE IF EXISTS asset_type_enum")
    op.execute("DROP TYPE IF EXISTS asset_status_enum")
