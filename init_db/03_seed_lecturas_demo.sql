-- Completa la tabla hasta 3.000 lecturas para habilitar el agente analitico.
-- Ejecutar despues de 02_hypertable_y_seed.sql.
DO $$
DECLARE
  total_lecturas BIGINT;
  lecturas_faltantes BIGINT;
  dispositivo_demo_id INTEGER;
  dispositivo_comparativo_id INTEGER;
BEGIN
  SELECT count(*) INTO total_lecturas FROM lecturas;
  lecturas_faltantes := 3000 - total_lecturas;

  IF lecturas_faltantes <= 0 THEN
    RAISE NOTICE 'La tabla ya contiene % lecturas; no se agregaron datos.', total_lecturas;
    RETURN;
  END IF;

  SELECT id INTO dispositivo_demo_id
  FROM dispositivos
  WHERE codigo = 'ESP32-G3';

  IF dispositivo_demo_id IS NULL THEN
    RAISE EXCEPTION 'No existe ESP32-G3. Ejecuta primero 02_hypertable_y_seed.sql.';
  END IF;

  INSERT INTO dispositivos (nombre, codigo, ubicacion)
  VALUES ('ESP32 - Estacion 2', 'ESP32-G4', 'Planta de procesamiento')
  ON CONFLICT (codigo) DO NOTHING;

  SELECT id INTO dispositivo_comparativo_id
  FROM dispositivos
  WHERE codigo = 'ESP32-G4';

  INSERT INTO lecturas (
    timestamp,
    dispositivo_id,
    nivel_calidad_id,
    temperatura,
    humedad,
    co2_ppm
  )
  SELECT
    TIMESTAMPTZ '2026-01-01 00:00:00+00' + muestra.numero * INTERVAL '5 minutes',
    CASE
      WHEN muestra.numero % 2 = 0 THEN dispositivo_comparativo_id
      ELSE dispositivo_demo_id
    END,
    nivel.id,
    round((23 + 4 * sin(muestra.numero::DOUBLE PRECISION / 120)
      + 1.5 * sin(muestra.numero::DOUBLE PRECISION / 8)
      + CASE WHEN muestra.numero % 2 = 0 THEN 1.5 ELSE 0 END)::NUMERIC, 1)::DOUBLE PRECISION,
    round((50 + 16 * sin(muestra.numero::DOUBLE PRECISION / 45)
      + 5 * sin(muestra.numero::DOUBLE PRECISION / 11)
      - CASE WHEN muestra.numero % 2 = 0 THEN 4 ELSE 0 END)::NUMERIC, 1)::DOUBLE PRECISION,
    valores.co2_ppm + CASE WHEN muestra.numero % 2 = 0 THEN 220 ELSE 0 END
  FROM generate_series(1, lecturas_faltantes) AS muestra(numero)
  CROSS JOIN LATERAL (
    SELECT round((900 + muestra.numero * 0.22
      + 480 * sin(muestra.numero::DOUBLE PRECISION / 37)
      + 180 * sin(muestra.numero::DOUBLE PRECISION / 7))::NUMERIC, 1)::DOUBLE PRECISION AS co2_ppm
  ) AS valores
  LEFT JOIN LATERAL (
    SELECT id
    FROM niveles_calidad_aire
    WHERE valores.co2_ppm >= ppm_min AND valores.co2_ppm < ppm_max
    ORDER BY ppm_min DESC
    LIMIT 1
  ) AS nivel ON TRUE;
END $$;