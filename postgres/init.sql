CREATE TABLE IF NOT EXISTS rules (
    rule_id         UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    min_age         INT         NULL CHECK (min_age IS NULL OR min_age >= 0),
    max_age         INT         NULL CHECK (max_age IS NULL OR max_age >= 0),
    gender          VARCHAR(20) NULL CHECK (gender IS NULL OR gender IN ('male', 'female', 'other')),
    income          INT         NULL CHECK (income IS NULL OR income >= 0),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS categories (
    category_id     UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(500) NOT NULL CHECK (char_length(name) >= 1 AND char_length(name) <= 500),
    subtitle        VARCHAR(500) NOT NULL CHECK (char_length(subtitle) >= 1 AND char_length(subtitle) <= 500),
    budget_amount   BIGINT   NOT NULL CHECK (budget_amount >= 0),
    rate_min        INT         NOT NULL CHECK (rate_min >= 0 AND rate_min <= 100) DEFAULT 1,
    rate_max        INT         NOT NULL CHECK (rate_max >= 0 AND rate_max <= 100 AND rate_max >= rate_min) DEFAULT 17,
    rule_id         UUID        NULL REFERENCES rules(rule_id),
    icon_path       VARCHAR(255) NULL,
    status          VARCHAR(20) NOT NULL DEFAULT 'running' CHECK (status IN ('running', 'paused', 'archived')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    age INT NOT NULL CHECK (age >= 0 AND age <= 100),
    gender VARCHAR(20) NOT NULL CHECK (gender IN ('male', 'female', 'other')),
    income INT NOT NULL CHECK (income >= 0)
);

CREATE TABLE IF NOT EXISTS selections (
    selection_id    UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         BIGINT      NULL REFERENCES users(user_id),
    category_id     UUID        NOT NULL REFERENCES categories(category_id),
    cashback        INT         NULL,
    estimated_spend BIGINT      NULL,
    idempotency_key VARCHAR(128) NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, category_id)
);

CREATE TABLE IF NOT EXISTS selection_idempotency_requests (
    user_id         BIGINT       NOT NULL REFERENCES users(user_id),
    idempotency_key VARCHAR(128) NOT NULL,
    request_hash    VARCHAR(64)  NOT NULL,
    response_body   JSONB        NOT NULL,
    status_code     INT          NOT NULL,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, idempotency_key)
);

CREATE TABLE IF NOT EXISTS audit_log (
    id           SERIAL      PRIMARY KEY,
    entity_type  VARCHAR(50) NOT NULL CHECK (char_length(entity_type) >= 1 AND char_length(entity_type) <= 50),
    entity_id    VARCHAR(64) NOT NULL CHECK (char_length(entity_id) >= 1 AND char_length(entity_id) <= 64),
    action       VARCHAR(50) NOT NULL CHECK (char_length(action) >= 1 AND char_length(action) <= 50),
    actor        VARCHAR(255) NOT NULL CHECK (char_length(actor) >= 1 AND char_length(actor) <= 255),
    details      JSONB       NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS admin_users (
    admin_id   SERIAL PRIMARY KEY,
    main_admin BOOLEAN   NOT NULL DEFAULT FALSE,
    login      VARCHAR(255) NOT NULL UNIQUE CHECK (char_length(login) >= 1 AND char_length(login) <= 255),
    password   VARCHAR(255) NOT NULL CHECK (char_length(password) >= 1),
    approved   BOOLEAN   NOT NULL DEFAULT FALSE
);

INSERT INTO rules (rule_id, min_age, max_age, gender, income)
VALUES ('a0000000-0000-0000-0000-000000000001'::uuid, NULL, NULL, NULL, NULL)
ON CONFLICT (rule_id) DO NOTHING;
