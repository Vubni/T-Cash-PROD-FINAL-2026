-- Этот файл выполняется при первом старте контейнера Postgres.
-- Здесь можно создать схему, таблицы, начальные данные и т.п.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Пример: создайте свои таблицы ниже
-- CREATE TABLE example (
--     id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
--     created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
-- );

