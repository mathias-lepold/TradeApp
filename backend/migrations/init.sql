-- TradeApp — PostgreSQL Schema

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ── Trades / Journal ──────────────────────────────────
CREATE TABLE IF NOT EXISTS trades (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol          VARCHAR(20) NOT NULL,
    name            VARCHAR(100),
    direction       VARCHAR(4) NOT NULL CHECK (direction IN ('buy', 'sell')),
    quantity        DECIMAL(18, 4) NOT NULL,
    entry_price     DECIMAL(18, 4) NOT NULL,
    exit_price      DECIMAL(18, 4),
    stop_loss       DECIMAL(18, 4),
    take_profit     DECIMAL(18, 4),
    currency        VARCHAR(3) NOT NULL DEFAULT 'CHF',
    status          VARCHAR(10) NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'closed')),
    opened_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    closed_at       TIMESTAMPTZ,
    pnl_chf         DECIMAL(18, 2),
    pnl_percent     DECIMAL(8, 4),
    holding_days    INTEGER,
    score_at_entry  INTEGER,
    crv_achieved    DECIMAL(6, 2),
    stamp_tax_chf   DECIMAL(10, 4),
    bias            TEXT[],
    notes           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Watchlist ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS watchlist (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol       VARCHAR(20) NOT NULL UNIQUE,
    name         VARCHAR(100),
    target_price DECIMAL(18, 4),
    alert_price  DECIMAL(18, 4),
    notes        TEXT,
    added_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Alerts ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS alerts (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol       VARCHAR(20) NOT NULL,
    type         VARCHAR(20) NOT NULL,
    threshold    DECIMAL(18, 4) NOT NULL,
    direction    VARCHAR(5) NOT NULL CHECK (direction IN ('above', 'below')),
    triggered    BOOLEAN DEFAULT FALSE,
    triggered_at TIMESTAMPTZ,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Indexes ───────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol);
CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status);
CREATE INDEX IF NOT EXISTS idx_trades_opened_at ON trades(opened_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_symbol ON alerts(symbol);
