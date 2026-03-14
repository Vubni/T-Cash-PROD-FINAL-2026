-- rule_id — единственный первичный ключ, отдельное поле id не нужно
CREATE TABLE IF NOT EXISTS rules (
    rule_id         UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    min_age         INT         NULL,
    max_age         INT         NULL,
    gender          TEXT        NULL,
    income          BIGINT      NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- category_id — первичный ключ
CREATE TABLE IF NOT EXISTS categories (
    category_id     UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT        NOT NULL,
    subtitle        TEXT        NOT NULL,
    icon_key        TEXT        NOT NULL,
    budget_amount   BIGINT      NOT NULL,
    target_users    INT         NOT NULL,
    avg_spend_per_user BIGINT   NOT NULL,
    audience_segments TEXT[]    NOT NULL,
    rule_id         UUID        NOT NULL REFERENCES rules(rule_id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS selections (
    selection_id    UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    category_id     UUID        NOT NULL REFERENCES categories(category_id),
    expected_benefit_amount BIGINT  NULL,
    availability_status TEXT        NULL,
    availability_reason TEXT        NULL,
    idempotency_key TEXT        NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
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

CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY
);


CREATE TABLE IF NOT EXISTS admin_users (
    admin_id   BIGSERIAL PRIMARY KEY,
    main_admin BOOLEAN   NOT NULL,
    login      TEXT      NOT NULL UNIQUE,
    password   TEXT      NOT NULL,
    approved   BOOLEAN   NOT NULL DEFAULT FALSE
);
