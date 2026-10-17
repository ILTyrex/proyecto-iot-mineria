# API + Base de Datos — Monitoreo de Calidad del Aire (IoT)

Este proyecto cubre la **Fase 2** del parcial integrador: API REST con
arquitectura POO + PostgreSQL/TimescaleDB con 10 tablas relacionadas.

Sensores del circuito: **DHT22** (temperatura/humedad, pin GPIO4) y
**MQ-135** (calidad del aire, pines GPIO34/35), LCD I2C (GPIO21/22).

## 1. Estructura del proyecto

```text
app/
  core/          -> configuración y conexión a la base de datos (config.py, database.py, security.py)
  models/        -> tablas ORM (SQLAlchemy) y sus relaciones
  schemas/       -> validación de datos de entrada/salida (Pydantic)
  repositories/  -> acceso a datos (patrón Repository, CRUD genérico + específico)
  services/      -> lógica de negocio (clasificación de calidad de aire, alertas)
  routers/       -> endpoints HTTP (capa de presentación de la API)
  main.py        -> arranque de la aplicación FastAPI
init_db/
  schema_completo.sql         -> crea las 10 tablas, la hypertable y los datos iniciales
esp32_extra/
  envio_api.ino.txt           -> fragmento para que el ESP32 haga POST a la API
docker-compose.yml / Dockerfile
```

## 2. Modelo de datos (10 tablas relacionadas)

- **ubicaciones**: Lugares físicos asociados a los dispositivos
- **tipos_alerta**: Catálogo de tipos y severidad de las alertas
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

En una base de datos nueva, Docker ejecuta `init_db/schema_completo.sql`
automáticamente al inicializar el volumen. El script crea las tablas,
convierte `lecturas` en hypertable y carga los datos iniciales (incluido
el dispositivo `ESP32-G3` de ejemplo). Para aplicarlo manualmente:

```bash
<<<<<<< HEAD
docker exec -i calidad_aire_db psql -U postgres -d calidad_aire_db < init_db/02_hypertable_y_seed.sql
docker exec -i calidad_aire_db psql -U postgres -d calidad_aire_db < init_db/03_seed_lecturas_demo.sql
```

El script de demostración agrega lecturas sintéticas hasta completar al menos 3.000 registros, repartidas entre dos dispositivos de ejemplo; si la tabla ya supera ese mínimo, no agrega filas.
=======
docker exec -i calidad_aire_db psql -U postgres -d calidad_aire_db < init_db/schema_completo.sql
```

La inicialización automática de Docker solo se ejecuta con un volumen de
base de datos vacío. Si ya tienes uno con tablas, no ejecutes el script
sin revisar el bloque opcional para borrar tablas antiguas: contiene
comandos que eliminan datos.
>>>>>>> 162465003aaf0425ad70a6aa310faa037fc62e1f

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

# Crea la base de datos (una sola vez)
psql -U postgres -c "CREATE DATABASE calidad_aire_db;"

# Crea la extensión, las tablas, la hypertable y los datos iniciales
psql -U postgres -d calidad_aire_db -f init_db/schema_completo.sql

# Luego arranca la API
uvicorn app.main:app --reload
<<<<<<< HEAD
# En otra terminal, una vez que las tablas ya existen:
psql -U postgres -d calidad_aire_db -f init_db/02_hypertable_y_seed.sql
psql -U postgres -d calidad_aire_db -f init_db/03_seed_lecturas_demo.sql
=======
>>>>>>> 162465003aaf0425ad70a6aa310faa037fc62e1f
```

> El script requiere TimescaleDB. Si solo tienes PostgreSQL, la API puede
> funcionar sin la extensión si creas las tablas por SQLAlchemy, pero no
> puedes ejecutar este script completo ni crear la hypertable.

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

Streamlit consume el endpoint `GET /api/lecturas/` de la API; la API es la
única capa que accede a PostgreSQL/TimescaleDB.

La aplicación completa de EDA está en `streamlit_app/eda_app.py`. Consulta el
histórico a través de la API y permite filtrar
por fechas, dispositivo, variables y rangos de valores. También incluye
limpieza física, detección de outliers IQR, histogramas, series temporales,
correlación y dos modelos de predicción (regresión lineal y bosque aleatorio).

Para ejecutarla, configura `API_URL` en el entorno o en
`.streamlit/secrets.toml` (por defecto `http://localhost:8000`), instala
`requirements.txt` y ejecuta:

```bash
streamlit run streamlit_app/eda_app.py
```

## 9. Agente analítico con Langflow

El proyecto incluye Langflow en `http://localhost:7860` y una herramienta
personalizada que consulta todas las páginas de la API para calcular
estadísticas, comparaciones entre dispositivos/periodos y tendencias diarias.
El detalle de configuración del flujo, las preguntas de prueba y la conexión
con la interfaz Streamlit está en [docs/langflow_agent.md](docs/langflow_agent.md).

Para iniciar API, base de datos y Langflow:

```bash
docker compose up -d --build
```

En Langflow crea el flujo `Chat Input -> Agent -> Chat Output`, conecta el
componente `SensorAnalytics` al puerto `Tools` del Agent y configura un modelo
Groq con capacidad de uso de herramientas. El Flow ID del flujo exportado está
configurado como valor predeterminado; si usas otro flujo, define
`LANGFLOW_FLOW_ID` en `.env`. Abre la página `Agente` de Streamlit: llama a
Langflow y conserva el `session_id` para el historial del chat.

Las claves del proveedor se configuran en Langflow y nunca deben guardarse en
el flujo exportado, el repositorio ni este README. La colección Qdrant y los
embeddings no intervienen en agregaciones numéricas; las métricas se calculan
directamente sobre lecturas consultadas desde la API.

## 10. Seguridad (nivel parcial)

El endpoint `POST /api/lecturas/` exige el header `X-API-Key` para
evitar que cualquiera inyecte datos falsos. Es una protección básica,
suficiente para el alcance del parcial; no reemplaza autenticación de
usuario (la tabla `usuarios` queda lista para eso más adelante si el
proyecto lo requiere).

## 11. Despliegue en la nube (requerido por el profesor)

### 11.1 Base de datos → Tiger Cloud (antes "Timescale Cloud")

Es la única opción gratuita que da la extensión **TimescaleDB real**
(Render/Railway/Supabase solo dan Postgres plano, sin esa extensión).

1. Crea cuenta gratis en [Timescale Cloud](https://console.cloud.timescale.com) (el
   dominio timescale.com redirige a tigerdata.com, es la misma empresa).
2. Crea un "service" nuevo (Postgres + TimescaleDB), plan gratuito.
3. Copia los datos de conexión que te da (host, puerto, usuario,
   password, nombre de la base) — reemplazan los valores de `.env`.
4. Ejecuta el script una sola vez contra esa base ya en la nube para
   crear las tablas, la hypertable y los datos iniciales:

   ```bash
   # Ejecuta el script antes de arrancar la API
   psql "postgresql://usuario:password@host:puerto/basededatos" -f init_db/schema_completo.sql
   ```

<<<<<<< HEAD
### 11.2 API → Render (plan gratuito)
=======
   Después configura la conexión de la API a Tiger Cloud y arráncala.

### 10.2 API → Render (plan gratuito)
>>>>>>> 162465003aaf0425ad70a6aa310faa037fc62e1f

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
