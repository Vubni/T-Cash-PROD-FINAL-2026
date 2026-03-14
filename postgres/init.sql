CREATE TABLE IF NOT EXISTS rules (
    rule_id         UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    min_age         INT         NULL,
    max_age         INT         NULL,
    gender          TEXT        NULL,
    income          BIGINT      NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS categories (
    category_id     UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT        NOT NULL,
    subtitle        TEXT        NOT NULL,
    icon_key        TEXT        NOT NULL,
    budget_amount   BIGINT      NOT NULL,
    audience_segments TEXT[]    NOT NULL,
    rule_id         UUID        NOT NULL REFERENCES rules(rule_id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS selections (
    selection_id    UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID        NULL REFERENCES users(user_id),
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

CREATE TABLE IF NOT EXISTS admin_users (
    admin_id   BIGSERIAL PRIMARY KEY,
    main_admin BOOLEAN   NOT NULL DEFAULT FALSE,
    login      TEXT      NOT NULL UNIQUE,
    password   TEXT      NOT NULL,
    approved   BOOLEAN   NOT NULL DEFAULT FALSE
);

-- дефолтное правило, на которое ссылаются категории при импорте из CSV
INSERT INTO rules (rule_id, min_age, max_age, gender, income)
VALUES ('a0000000-0000-0000-0000-000000000001'::uuid, NULL, NULL, NULL, NULL)
ON CONFLICT (rule_id) DO NOTHING;
