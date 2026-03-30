"""Portfolio-Tabellen hinzufügen

Revision ID: 002
Revises: 001
Create Date: 2026-03-30

Tabellen:
  - portfolio_trades  (Kauf/Verkauf-Trades für Portfolio-Verwaltung)
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "portfolio_trades",
        sa.Column("id",         sa.String(36),  primary_key=True),
        sa.Column("symbol",     sa.String(20),  nullable=False),
        sa.Column("action",     sa.String(4),   nullable=False),   # buy | sell
        sa.Column("quantity",   sa.Numeric(18, 4), nullable=False),
        sa.Column("price",      sa.Numeric(18, 4), nullable=False),
        sa.Column("fees",       sa.Numeric(10, 4), nullable=False, server_default="0"),
        sa.Column("currency",   sa.String(3),   nullable=False, server_default="CHF"),
        sa.Column("notes",      sa.Text,        nullable=True),
        sa.Column("timestamp",  sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_portfolio_trades_symbol",    "portfolio_trades", ["symbol"])
    op.create_index("ix_portfolio_trades_timestamp", "portfolio_trades", ["timestamp"])


def downgrade() -> None:
    op.drop_index("ix_portfolio_trades_timestamp", table_name="portfolio_trades")
    op.drop_index("ix_portfolio_trades_symbol",    table_name="portfolio_trades")
    op.drop_table("portfolio_trades")
