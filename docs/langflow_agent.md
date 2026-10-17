# Agente analitico de sensores

## Arquitectura

- **Datos:** API `GET /api/lecturas/`, consultada en paginas de hasta 1.000 filas.
- **Herramienta:** componente personalizado `SensorAnalytics`; calcula estadisticas descriptivas, promedios por dispositivo, niveles de calidad, comparacion cronologica y tendencia diaria. El modelo no calcula valores a partir de texto libre.
- **Modelo:** proveedor Groq configurado dentro de Langflow con un modelo que admita llamadas a herramientas.
- **Chat:** Playground de Langflow en `http://localhost:7860`.
- **Aplicativo web:** pagina `Agente` de Streamlit; invoca el endpoint `/api/v1/run/{FLOW_ID}` y mantiene una sesion de conversacion.
- **Persistencia:** Streamlit guarda cada mensaje en `mensajes_conversacion`, agrupado por el ID de `conversaciones`; los chats guardados se pueden volver a abrir desde la barra lateral.

## Preparacion

1. En la raiz del proyecto ejecuta `docker compose up -d --build`.
2. Inicializa las tablas y catalogos siguiendo el README. Luego ejecuta `init_db/03_seed_lecturas_demo.sql`; el script completa la tabla hasta 3.000 lecturas.
3. Abre Langflow en `http://localhost:7860` y configura Groq en **Settings > Model Providers**. Guarda la clave como credencial de Langflow, no dentro del flujo ni del repositorio.
4. Crea un flujo en blanco con `Chat Input`, `Agent` y `Chat Output`; conecta los componentes de chat al Agent y su respuesta al Chat Output.
5. En el menu de componentes de datos/herramientas agrega `Sensor Analytics` y conecta su salida de herramienta al puerto `Tools` del Agent.
6. En las instrucciones del Agent pega el texto de abajo. Prueba el flujo en el Playground. El Flow ID incluido en el JSON de `Agente simple` ya está configurado como predeterminado en Streamlit.
7. Si usas otro flujo, define `LANGFLOW_FLOW_ID=<id-del-flujo>` en `.env`. Si tu instancia exige autenticacion, crea una clave nueva y configura `LANGFLOW_API_KEY=<clave-de-langflow>` localmente.
8. Configura un unico `API_KEY` en `.env`; Compose lo usa para proteger la API y Streamlit lo envia al guardar/leer conversaciones.
9. Ejecuta `streamlit run streamlit_app/eda_app.py`; la navegacion incluye las paginas EDA y Agente.

Si cambias el codigo de la API, reconstruye el servicio con `docker compose up -d --build api`. Los mensajes se guardan al enviar cada turno, incluso si una solicitud posterior a Langflow falla.

## Instrucciones del Agent

```text
Eres un agente analitico de lecturas de sensores IoT de calidad del aire.
Responde en espanol, con claridad y unidades. Para cualquier afirmacion sobre
los datos llama a Sensor Analytics; no inventes cifras, dispositivos ni fechas.
Separa descripcion, comparacion y tendencia cuando corresponda. Aclara que la
comparacion temporal divide cronologicamente el historico en dos partes y que
la tendencia diaria usa hasta los ultimos 60 dias disponibles. Si faltan datos
para una conclusion, dilo. Distingue correlacion de causalidad.
```

## Preguntas de comprobacion

- Descriptiva: `Resume las lecturas y dime el promedio, minimo y maximo de CO2.`
- Comparativa: `Compara los promedios de temperatura y CO2 entre dispositivos.`
- Comparativa temporal: `Compara el primer y segundo periodo del historico.`
- Tendencia: `Describe la tendencia diaria de humedad y CO2.`
- Conteo: `Cuantas lecturas hay y entre que fechas?`

El componente se ejecuta dentro del contenedor Langflow y usa `SENSOR_API_URL=http://api:8000` en Docker Compose. Si ejecutas Langflow fuera de Docker, configura `SENSOR_API_URL=http://localhost:8000` en su entorno.

Qdrant y embeddings no se usan para calcular estas respuestas: una busqueda vectorial no sustituye agregaciones ni tendencias numericas. Se pueden agregar como herramienta complementaria para buscar documentacion, pero las metricas deben seguir proviniendo de la API.