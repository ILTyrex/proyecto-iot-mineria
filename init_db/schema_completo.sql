-- ============================================================
-- Taller 1 - Componente 1: PostgreSQL + TimescaleDB
-- Base de datos de monitoreo de calidad del aire (IoT)
-- ============================================================

-- Si ya tienen tablas viejas, descomenten esto para empezar limpio
-- (BORRA TODOS LOS DATOS):
-- DROP TABLE IF EXISTS alertas, logs_sistema, lecturas, dispositivo_sensores,
--   dispositivos, sensores, niveles_calidad_aire, tipos_alerta, ubicaciones,
--   usuarios, mensajes_conversacion, conversaciones CASCADE;

-- 1) Extensión
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- 2) Catálogos
CREATE TABLE ubicaciones (
    id           SERIAL PRIMARY KEY,
    nombre       VARCHAR(100) NOT NULL UNIQUE,
    descripcion  VARCHAR(255),
    zona         VARCHAR(50)
);

CREATE TABLE tipos_alerta (
    id           SERIAL PRIMARY KEY,
    nombre       VARCHAR(50) NOT NULL UNIQUE,
    descripcion  VARCHAR(255),
    severidad    VARCHAR(20) NOT NULL
);

CREATE TABLE sensores (
    id             SERIAL PRIMARY KEY,
    nombre         VARCHAR(50) NOT NULL UNIQUE,
    tipo           VARCHAR(50) NOT NULL,
    unidad_medida  VARCHAR(20) NOT NULL,
    descripcion    VARCHAR(255)
);

CREATE TABLE niveles_calidad_aire (
    id           SERIAL PRIMARY KEY,
    nombre       VARCHAR(30) NOT NULL UNIQUE,
    ppm_min      DOUBLE PRECISION NOT NULL,
    ppm_max      DOUBLE PRECISION NOT NULL,
    color        VARCHAR(20),
    descripcion  VARCHAR(255)
);

CREATE TABLE usuarios (
    id             SERIAL PRIMARY KEY,
    nombre         VARCHAR(100) NOT NULL,
    email          VARCHAR(120) NOT NULL UNIQUE,
    password_hash  VARCHAR(255) NOT NULL,
    rol            VARCHAR(30) NOT NULL DEFAULT 'analista',
    activo         BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_registro TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE conversaciones (
    id         VARCHAR(32) PRIMARY KEY,
    creada_en  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE mensajes_conversacion (
    id              SERIAL PRIMARY KEY,
    conversacion_id VARCHAR(32) NOT NULL REFERENCES conversaciones(id),
    role            VARCHAR(20) NOT NULL,
    content         TEXT NOT NULL,
    creado_en       TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_mensajes_conversacion_role CHECK (role IN ('user', 'assistant'))
);
CREATE INDEX ix_mensajes_conversacion_conversacion_id
    ON mensajes_conversacion (conversacion_id);

-- 3) Dispositivos y su relación con sensores
CREATE TABLE dispositivos (
    id             SERIAL PRIMARY KEY,
    nombre         VARCHAR(100) NOT NULL,
    codigo         VARCHAR(50) NOT NULL UNIQUE,
    ubicacion_id   INTEGER REFERENCES ubicaciones(id),
    mac_address    VARCHAR(50) UNIQUE,
    activo         BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_registro TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE dispositivo_sensores (
    id              SERIAL PRIMARY KEY,
    dispositivo_id  INTEGER NOT NULL REFERENCES dispositivos(id),
    sensor_id       INTEGER NOT NULL REFERENCES sensores(id),
    pin             VARCHAR(30),
    CONSTRAINT uq_dispositivo_sensor UNIQUE (dispositivo_id, sensor_id)
);

CREATE TABLE logs_sistema (
    id              SERIAL PRIMARY KEY,
    dispositivo_id  INTEGER REFERENCES dispositivos(id),
    evento          VARCHAR(50) NOT NULL,
    detalle         VARCHAR(255),
    timestamp       TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX ix_logs_sistema_timestamp ON logs_sistema (timestamp);

-- 4) Serie temporal: lecturas (hypertable)
CREATE TABLE lecturas (
    id                SERIAL,
    timestamp         TIMESTAMPTZ NOT NULL DEFAULT now(),
    dispositivo_id    INTEGER NOT NULL REFERENCES dispositivos(id),
    nivel_calidad_id  INTEGER REFERENCES niveles_calidad_aire(id),
    temperatura       DOUBLE PRECISION NOT NULL,
    humedad           DOUBLE PRECISION NOT NULL,
    co2_ppm           DOUBLE PRECISION NOT NULL,
    PRIMARY KEY (id, timestamp)
);

-- Chunk de 1 día (justificación en el informe)
SELECT create_hypertable('lecturas', 'timestamp',
                         chunk_time_interval => INTERVAL '1 day');

CREATE INDEX ix_lecturas_dispositivo_ts ON lecturas (dispositivo_id, timestamp DESC);

-- 5) Alertas (referencian lecturas por id + timestamp)
CREATE TABLE alertas (
    id                 SERIAL PRIMARY KEY,
    lectura_id         INTEGER NOT NULL,
    lectura_timestamp  TIMESTAMPTZ NOT NULL,
    tipo_alerta_id     INTEGER NOT NULL REFERENCES tipos_alerta(id),
    mensaje            VARCHAR(255) NOT NULL,
    atendida           BOOLEAN NOT NULL DEFAULT FALSE,
    fecha_creacion     TIMESTAMPTZ DEFAULT now()
);

-- Intento de FK hacia la hypertable (puede no estar soportada)
DO $$
BEGIN
    ALTER TABLE alertas
        ADD CONSTRAINT fk_alertas_lectura
        FOREIGN KEY (lectura_id, lectura_timestamp)
        REFERENCES lecturas (id, timestamp);
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'No se pudo crear la FK alertas -> lecturas: %', SQLERRM;
END $$;

-- 6) Datos iniciales
INSERT INTO ubicaciones (nombre, descripcion, zona) VALUES
  ('Laboratorio', 'Laboratorio donde está instalada la estación', 'Interior');

INSERT INTO tipos_alerta (nombre, descripcion, severidad) VALUES
  ('Calidad Mala',      'CO2 entre 2000 y 5000 ppm',  'alta'),
  ('Calidad Peligrosa', 'CO2 por encima de 5000 ppm', 'critica');

INSERT INTO niveles_calidad_aire (nombre, ppm_min, ppm_max, color, descripcion) VALUES
  ('Buena',     400,  1000,   '#4CAF50', 'Aire limpio, condiciones óptimas'),
  ('Moderada',  1000, 2000,   '#FFC107', 'Calidad aceptable, se recomienda ventilar'),
  ('Mala',      2000, 5000,   '#FF5722', 'Contaminación alta, ventilar de inmediato'),
  ('Peligrosa', 5000, 999999, '#B71C1C', 'Nivel peligroso, ventilar/evacuar');

INSERT INTO sensores (nombre, tipo, unidad_medida, descripcion) VALUES
  ('DHT22',  'Temperatura/Humedad', '°C / %', 'Sensor digital de temperatura y humedad'),
  ('MQ-135', 'Calidad del aire',    'ppm',    'Sensor de gases (CO2 equivalente y otros)');

INSERT INTO dispositivos (nombre, codigo, ubicacion_id)
SELECT 'ESP32 - Estación 1', 'ESP32-G3', u.id
FROM ubicaciones u WHERE u.nombre = 'Laboratorio';

INSERT INTO dispositivo_sensores (dispositivo_id, sensor_id, pin)
SELECT d.id, s.id, 'GPIO4'
FROM dispositivos d, sensores s WHERE d.codigo = 'ESP32-G3' AND s.nombre = 'DHT22';

INSERT INTO dispositivo_sensores (dispositivo_id, sensor_id, pin)
SELECT d.id, s.id, 'GPIO34/GPIO35'
FROM dispositivos d, sensores s WHERE d.codigo = 'ESP32-G3' AND s.nombre = 'MQ-135';
