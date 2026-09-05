-- ============================================================
-- Ejecutar SOLO DESPUÉS de levantar la API una vez (para que
-- SQLAlchemy haya creado las tablas con Base.metadata.create_all).
--
-- Uso:
--   docker exec -i calidad_aire_db psql -U postgres -d calidad_aire_db < init_db/02_hypertable_y_seed.sql
-- o, si corres Postgres local:
--   psql -U postgres -d calidad_aire_db -f init_db/02_hypertable_y_seed.sql
-- ============================================================

-- 1) Convertir "lecturas" en hypertable de TimescaleDB usando "timestamp"
SELECT create_hypertable('lecturas', 'timestamp', if_not_exists => TRUE, migrate_data => TRUE);

-- 2) Catálogo de niveles de calidad del aire (igual a la escala del firmware ESP32)
INSERT INTO niveles_calidad_aire (nombre, ppm_min, ppm_max, color, descripcion) VALUES
  ('Buena',     400,  1000,  '#4CAF50', 'Aire limpio, condiciones óptimas'),
  ('Moderada',  1000, 2000,  '#FFC107', 'Calidad aceptable, se recomienda ventilar'),
  ('Mala',      2000, 5000,  '#FF5722', 'Contaminación alta, ventilar de inmediato'),
  ('Peligrosa', 5000, 999999,'#B71C1C', 'Nivel peligroso, ventilar/evacuar')
ON CONFLICT (nombre) DO NOTHING;

-- 3) Catálogo de sensores usados en el proyecto
INSERT INTO sensores (nombre, tipo, unidad_medida, descripcion) VALUES
  ('DHT22',   'Temperatura/Humedad', '°C / %', 'Sensor digital de temperatura y humedad'),
  ('MQ-135',  'Calidad del aire',    'ppm',    'Sensor de gases (CO2 equivalente y otros)')
ON CONFLICT (nombre) DO NOTHING;

-- 4) Dispositivo de ejemplo (AJUSTA el código para que coincida con el
--    que envíe tu ESP32 en el campo "codigo_dispositivo")
INSERT INTO dispositivos (nombre, codigo, ubicacion) VALUES
  ('ESP32 - Estación 1', 'ESP32-G3', 'Laboratorio')
ON CONFLICT (codigo) DO NOTHING;

-- 5) Vincular los sensores al dispositivo de ejemplo, con los pines reales del circuito
INSERT INTO dispositivo_sensores (dispositivo_id, sensor_id, pin)
SELECT d.id, s.id, 'GPIO4'
FROM dispositivos d, sensores s
WHERE d.codigo = 'ESP32-G3' AND s.nombre = 'DHT22'
ON CONFLICT DO NOTHING;

INSERT INTO dispositivo_sensores (dispositivo_id, sensor_id, pin)
SELECT d.id, s.id, 'GPIO34/GPIO35'
FROM dispositivos d, sensores s
WHERE d.codigo = 'ESP32-G3' AND s.nombre = 'MQ-135'
ON CONFLICT DO NOTHING;
