CREATE TABLE IF NOT EXISTS conversaciones (
    id         VARCHAR(32) PRIMARY KEY,
    creada_en  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS mensajes_conversacion (
    id               SERIAL PRIMARY KEY,
    conversacion_id  VARCHAR(32) NOT NULL REFERENCES conversaciones(id),
    role             VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
    content          TEXT NOT NULL,
    creado_en        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_mensajes_conversacion_conversacion_id
    ON mensajes_conversacion (conversacion_id);
