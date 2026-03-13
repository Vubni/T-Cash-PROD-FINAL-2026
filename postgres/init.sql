CREATE TABLE IF NOT EXISTS categories (
    id              BIGSERIAL PRIMARY KEY,
    category_id     TEXT UNIQUE NOT NULL,
    name            TEXT        NOT NULL,
    subtitle        TEXT        NOT NULL,
    icon_key        TEXT        NOT NULL,
    status          TEXT        NOT NULL,
    budget_amount   BIGINT      NOT NULL,
    budget_currency CHAR(3)     NOT NULL,
    target_users    INT         NOT NULL,
    avg_spend_per_user BIGINT   NOT NULL,
    audience_segments TEXT[]    NOT NULL,
    rule_personalized  BOOLEAN  NOT NULL,
    rule_budget_mode   TEXT     NOT NULL,
    rule_fallback_message TEXT  NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS selections (
    id                  BIGSERIAL   PRIMARY KEY,
    selection_id        TEXT        UNIQUE NOT NULL,
    period_id           TEXT        NOT NULL,
    category_id         TEXT        NOT NULL REFERENCES categories(category_id),
    status              TEXT        NOT NULL,
    expected_benefit_amount BIGINT  NULL,
    currency            CHAR(3)     NULL,
    availability_status TEXT        NULL,
    availability_reason TEXT        NULL,
    idempotency_key     TEXT        NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit_log (
    id           BIGSERIAL   PRIMARY KEY,
    entity_type  TEXT        NOT NULL,
    entity_id    TEXT        NOT NULL,
    action       TEXT        NOT NULL,
    actor        TEXT        NOT NULL,
    details      JSONB       NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
