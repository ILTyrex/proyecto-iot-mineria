# API + Base de Datos — Monitoreo de Calidad del Aire (IoT)

Este proyecto cubre la **Fase 2** del parcial integrador: API REST con
arquitectura POO + PostgreSQL/TimescaleDB con 8 tablas relacionadas.

Sensores del circuito: **DHT22** (temperatura/humedad, pin GPIO4) y
**MQ-135** (calidad del aire, pines GPIO34/35), LCD I2C (GPIO21/22).

## 1. Estructura del proyecto

```text
app/
  core/          -> configuración y conexión a la base de datos (config.py, database.py, security.py)
  models/        -> 8 tablas ORM (SQLAlchemy) y sus relaciones
  schemas/       -> validación de datos de entrada/salida (Pydantic)
  repositories/  -> acceso a datos (patrón Repository, CRUD genérico + específico)
  services/      -> lógica de negocio (clasificación de calidad de aire, alertas)
  routers/       -> endpoints HTTP (capa de presentación de la API)
  main.py        -> arranque de la aplicación FastAPI
init_db/
  01_extension.sql            -> habilita la extensión TimescaleDB (automático con Docker)
  02_hypertable_y_seed.sql    -> convierte "lecturas" en hypertable + datos iniciales
esp32_extra/
  envio_api.ino.txt           -> fragmento para que el ESP32 haga POST a la API
docker-compose.yml / Dockerfile
```

## 2. Modelo de datos (8 tablas relacionadas)

- **dispositivos**: ESP32 registrados (código, ubicación, MAC)
- **sensores**: Catálogo de sensores (DHT22, MQ-135)
- **dispositivo_sensores**: Relación N:M dispositivo↔sensor (con el pin usado)
- **niveles_calidad_aire**: Escala Buena/Moderada/Mala/Peligrosa (igual que el firmware)
- **lecturas**: Serie temporal (hypertable) con temperatura, humedad, CO2 ppm
- **alertas**: Se generan automáticamente si el nivel es Mala/Peligrosa
- **logs_sistema**: Bitácora de eventos por dispositivo
- **usuarios**: Usuarios que consultarán la API / dashboards

`lecturas` usa llave primaria compuesta `(id, timestamp)` porque TimescaleDB
exige que toda llave primaria incluya la columna de tiempo usada para
particionar. `alertas` referencia esa llave compuesta.

## 3. Cómo levantarlo (con Docker, recomendado)

Requiere Docker Desktop instalado.

```bash
cd parcial_iot_api
docker compose up -d --build
```

Esto levanta:

- `db`: PostgreSQL 15 + TimescaleDB en el puerto 5432
- `api`: la API FastAPI en el puerto 8000

La primera vez que arranca la API, se crean las tablas automáticamente
(`Base.metadata.create_all`). Después, aplica el script que crea el
hypertable y los datos iniciales (niveles de calidad, sensores, y el
dispositivo `ESP32-G3` de ejemplo):

```bash
docker exec -i calidad_aire_db psql -U postgres -d calidad_aire_db < init_db/02_hypertable_y_seed.sql
```

Verifica que quedó todo bien:

```bash
docker exec -it calidad_aire_db psql -U postgres -d calidad_aire_db -c "\dt"
docker exec -it calidad_aire_db psql -U postgres -d calidad_aire_db -c "SELECT * FROM dispositivos;"
```

Documentación interactiva (Swagger) de la API: [http://localhost:8000/docs](http://localhost:8000/docs)

## 4. Cómo levantarlo sin Docker (Postgres local ya instalado)

```bash
cd parcial_iot_api
python3 -m venv venv
source venv/bin/activate        # en Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env            # y edita los valores de conexión

# Crea la base de datos y habilita la extensión (una sola vez)
psql -U postgres -c "CREATE DATABASE calidad_aire_db;"
psql -U postgres -d calidad_aire_db -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"

uvicorn app.main:app --reload
# En otra terminal, una vez que las tablas ya existen:
psql -U postgres -d calidad_aire_db -f init_db/02_hypertable_y_seed.sql
```

> Nota: si no tienes TimescaleDB instalado localmente, puedes omitir el
> `CREATE EXTENSION` y la línea `create_hypertable(...)` del script —
> la API funciona igual sobre PostgreSQL normal, solo pierdes las
> optimizaciones de series de tiempo (compresión, particionado
> automático) que pide el enunciado.

## 5. Probar el endpoint que usará el ESP32

```bash
curl -X POST http://localhost:8000/api/lecturas/ \
  -H "Content-Type: application/json" \
  -H "X-API-Key: clave-secreta-esp32-2026" \
  -d '{"codigo_dispositivo":"ESP32-G3","temperatura":24.8,"humedad":58,"co2_ppm":1450}'
```

Consultar el histórico (lo que usarán Streamlit y Power BI):

```bash
curl "http://localhost:8000/api/lecturas/?dispositivo_codigo=ESP32-G3&limit=20"
```

## 6. Conectar el ESP32

En `esp32_extra/envio_api.ino.txt` está el fragmento de código para
agregar al sketch que ya tienen (el comentario del archivo original
decía "envío a API removido: se implementará más adelante" — esto lo
completa).

Solo deben:

1. Instalar la librería **ArduinoJson**.
2. Cambiar `API_URL` por la IP de la máquina donde corre la API
   (ej: `http://192.168.1.50:8000/api/lecturas/`) — el ESP32 y el
   servidor deben estar en la misma red WiFi (`ALEXMA`).
3. Verificar que `API_KEY` coincida con el `.env` de la API.
4. Llamar a `enviarLecturaAPI(temperatura, humedad, co2ppm)` dentro del
   `loop()`, después de `mostrarEnLCD(...)`.

## 7. Conectar Power BI

Power BI Desktop → Obtener datos → PostgreSQL → host `localhost`
(o la IP del servidor), puerto `5432`, base `calidad_aire_db`. Se
conecta directo a las tablas `lecturas`, `dispositivos`,
`niveles_calidad_aire`, `alertas`, sin pasar por la API (tal como pide
el enunciado: "conectado directamente a PostgreSQL, sin datos cargados
manualmente").

## 8. Conectar Streamlit

Desde Python, usar `psycopg2`/`SQLAlchemy` con la misma cadena de
conexión de `DATABASE_URL` en `app/core/config.py`, o consumir el
endpoint `GET /api/lecturas/` de la API con filtros de fecha y rango.

La aplicación completa de EDA está en `streamlit_app/eda_app.py`. Lee
directamente la tabla `lecturas` de PostgreSQL/TimescaleDB y permite filtrar
por fechas, dispositivo, variables y rangos de valores. También incluye
limpieza física, detección de outliers IQR, histogramas, series temporales,
correlación y dos modelos de predicción (regresión lineal y bosque aleatorio).

Para ejecutarla, configura las variables `DB_USER`, `DB_PASSWORD`, `DB_HOST`,
`DB_PORT`, `DB_NAME` y `DB_SSLMODE` en el entorno o en
`.streamlit/secrets.toml`, instala `requirements.txt` y ejecuta:

```bash
streamlit run streamlit_app/eda_app.py
```

## 9. Seguridad (nivel parcial)

El endpoint `POST /api/lecturas/` exige el header `X-API-Key` para
evitar que cualquiera inyecte datos falsos. Es una protección básica,
suficiente para el alcance del parcial; no reemplaza autenticación de
usuario (la tabla `usuarios` queda lista para eso más adelante si el
proyecto lo requiere).

## 10. Despliegue en la nube (requerido por el profesor)

### 10.1 Base de datos → Tiger Cloud (antes "Timescale Cloud")

Es la única opción gratuita que da la extensión **TimescaleDB real**
(Render/Railway/Supabase solo dan Postgres plano, sin esa extensión).

1. Crea cuenta gratis en [Timescale Cloud](https://console.cloud.timescale.com) (el
   dominio timescale.com redirige a tigerdata.com, es la misma empresa).
2. Crea un "service" nuevo (Postgres + TimescaleDB), plan gratuito.
3. Copia los datos de conexión que te da (host, puerto, usuario,
   password, nombre de la base) — reemplazan los valores de `.env`.
4. Corre localmente (una sola vez, contra esa base ya en la nube):

   ```bash
   uvicorn app.main:app --reload   # crea las tablas contra Tiger Cloud
   psql "postgresql://usuario:password@host:puerto/basededatos" -f init_db/02_hypertable_y_seed.sql
   ```

### 10.2 API → Render (plan gratuito)

1. Sube este contenido a la carpeta `api/` de tu repo de GitHub (ver
   sección 1 más abajo) y haz push a `main`.
2. En [Render dashboard](https://dashboard.render.com) → New → Blueprint → conecta tu
   repo `proyecto-iot-mineria`. Render detecta el archivo `render.yaml`
   dentro de `api/` (indícale ese "Root Directory" si te lo pregunta).
3. Cuando pida las variables de entorno (`DB_HOST`, `DB_PORT`,
   `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `API_KEY`), pon ahí los datos
   de conexión de Tiger Cloud del paso anterior.
4. Al terminar el deploy te da una URL tipo
   `https://calidad-aire-api.onrender.com`. Esa es la que va en:
   - El sketch del ESP32 (`API_URL` en `esp32_extra/envio_api.ino.txt`).
   - Power BI (conexión directa a la base de Tiger Cloud, no a esta URL).
   - Streamlit (para pedirle el histórico vía `GET /api/lecturas/`).

> Nota: el plan free de Render "duerme" el servicio tras 15 min sin
> tráfico y la primera petición después tarda 30-60 seg en responder
> (cold start). Es normal, no es un error — para la sustentación, hazle
> una petición un par de minutos antes de empezar para "despertarla".
