import os
from pathlib import Path
from urllib.parse import quote_plus

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error


st.set_page_config(page_title="EDA | Calidad de aire", page_icon="🌬️", layout="wide")

NUMERIC_COLUMNS = ["temperatura", "humedad", "co2_ppm"]
VARIABLE_LABELS = {
    "temperatura": "Temperatura (°C)",
    "humedad": "Humedad (%)",
    "co2_ppm": "CO₂ (ppm)",
}

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def setting(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value:
        return value
    try:
        return st.secrets.get(name, default)
    except (FileNotFoundError, KeyError):
        return default


def database_url() -> str:
    service_url = setting("TIMESCALE_SERVICE_URL")
    if service_url:
        if service_url.startswith("postgres://"):
            return "postgresql+psycopg://" + service_url.removeprefix("postgres://")
        if service_url.startswith("postgresql://"):
            return "postgresql+psycopg://" + service_url.removeprefix("postgresql://")
        return service_url

    user = setting("DB_USER", "postgres")
    password = setting("DB_PASSWORD", "postgres")
    host = setting("DB_HOST", "localhost")
    port = setting("DB_PORT", "5432")
    name = setting("DB_NAME", "calidad_aire_db")
    sslmode = setting("DB_SSLMODE", "prefer")
    return (
        f"postgresql+psycopg://{quote_plus(str(user))}:{quote_plus(str(password))}"
        f"@{host}:{port}/{name}?sslmode={sslmode}"
    )


@st.cache_data(ttl=60, show_spinner=False)
def load_data() -> pd.DataFrame:
    query = text(
        """
        SELECT l.timestamp, l.temperatura, l.humedad, l.co2_ppm,
               COALESCE(n.nombre, 'Sin clasificar') AS nivel_calidad,
               d.codigo AS dispositivo, d.ubicacion
        FROM lecturas AS l
        LEFT JOIN niveles_calidad_aire AS n ON n.id = l.nivel_calidad_id
        LEFT JOIN dispositivos AS d ON d.id = l.dispositivo_id
        ORDER BY l.timestamp
        """
    )
    engine = create_engine(database_url(), pool_pre_ping=True)
    try:
        data = pd.read_sql(query, engine)
    finally:
        engine.dispose()
    data["timestamp"] = pd.to_datetime(data["timestamp"], errors="coerce", utc=True)
    for column in NUMERIC_COLUMNS:
        data[column] = pd.to_numeric(data[column], errors="coerce")
    return data.dropna(subset=["timestamp"])


def clean_data(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    cleaned = data.dropna(subset=NUMERIC_COLUMNS).copy()
    physical_mask = (
        cleaned["humedad"].between(0, 100)
        & cleaned["temperatura"].between(-50, 80)
        & cleaned["co2_ppm"].ge(0)
    )
    cleaned = cleaned.loc[physical_mask].copy()
    outlier_flags = pd.DataFrame(index=cleaned.index)
    for column in NUMERIC_COLUMNS:
        q1, q3 = cleaned[column].quantile([0.25, 0.75])
        iqr = q3 - q1
        outlier_flags[f"{column}_outlier"] = ~cleaned[column].between(q1 - 1.5 * iqr, q3 + 1.5 * iqr)
    outlier_flags["es_outlier"] = outlier_flags.any(axis=1)
    return cleaned, outlier_flags


def plot_distribution(data: pd.DataFrame, columns: list[str]) -> None:
    figure, axes = plt.subplots(1, len(columns), figsize=(5 * len(columns), 3.8))
    axes = [axes] if len(columns) == 1 else axes
    for axis, column in zip(axes, columns):
        sns.histplot(data[column], kde=True, ax=axis, color="#167d8d")
        axis.set_title(f"Distribución de {VARIABLE_LABELS[column]}")
        axis.set_xlabel(VARIABLE_LABELS[column])
        axis.set_ylabel("Frecuencia")
    figure.tight_layout()
    st.pyplot(figure, use_container_width=True)
    plt.close(figure)


def plot_time_series(data: pd.DataFrame, columns: list[str]) -> None:
    figure, axis = plt.subplots(figsize=(12, 4.5))
    for column in columns:
        axis.plot(data["timestamp"], data[column], label=VARIABLE_LABELS[column], linewidth=1.4)
    axis.set_xlabel("Fecha y hora")
    axis.set_ylabel("Valor")
    axis.legend()
    axis.grid(alpha=0.25)
    figure.tight_layout()
    st.pyplot(figure, use_container_width=True)
    plt.close(figure)


def train_models(data: pd.DataFrame, target: str) -> None:
    feature_columns = [column for column in NUMERIC_COLUMNS if column != target]
    model_data = data[["timestamp", target, *feature_columns]].dropna().copy()
    model_data["hora"] = model_data["timestamp"].dt.hour
    model_data["dia_semana"] = model_data["timestamp"].dt.dayofweek
    model_data["dia_del_anio"] = model_data["timestamp"].dt.dayofyear
    features = [*feature_columns, "hora", "dia_semana", "dia_del_anio"]
    if len(model_data) < 20:
        st.info("Se necesitan al menos 20 lecturas filtradas para entrenar los modelos.")
        return
    split_index = max(int(len(model_data) * 0.8), 1)
    x_train, x_test = model_data[features].iloc[:split_index], model_data[features].iloc[split_index:]
    y_train, y_test = model_data[target].iloc[:split_index], model_data[target].iloc[split_index:]
    if x_test.empty:
        st.info("No hay suficientes lecturas para separar entrenamiento y prueba.")
        return
    models = {
        "Regresión lineal": LinearRegression(),
        "Bosque aleatorio": RandomForestRegressor(n_estimators=150, random_state=42, n_jobs=-1),
    }
    results = []
    predictions = pd.DataFrame({"Real": y_test.to_numpy()}, index=y_test.index)
    for name, model in models.items():
        model.fit(x_train, y_train)
        prediction = model.predict(x_test)
        predictions[name] = prediction
        results.append({
            "Modelo": name,
            "MAE": mean_absolute_error(y_test, prediction),
            "RMSE": root_mean_squared_error(y_test, prediction),
            "R²": r2_score(y_test, prediction),
        })
    st.dataframe(
        pd.DataFrame(results).style.format({"MAE": "%.2f", "RMSE": "%.2f", "R²": "%.3f"}),
        use_container_width=True,
    )
    st.caption(f"Objetivo: {VARIABLE_LABELS[target]}. División temporal: {len(x_train)} entrenamiento / {len(x_test)} prueba.")
    st.line_chart(predictions, y_label=VARIABLE_LABELS[target], x_label="Índice de prueba")


st.title("Análisis Exploratorio | Calidad de aire y humedad")
st.caption("Histórico de sensores IoT conectado directamente a PostgreSQL/TimescaleDB")

try:
    raw_data = load_data()
except Exception as error:
    st.error("No fue posible consultar PostgreSQL. Revisa las variables DB_* y que la base esté disponible.")
    st.exception(error)
    st.stop()

st.success(f"Consulta exitosa: {len(raw_data):,} lecturas recibidas.")
if raw_data.empty:
    st.warning("La consulta no devolvió lecturas.")
    st.stop()

cleaned_data, outlier_flags = clean_data(raw_data)
with st.expander("Limpieza y calidad de datos", expanded=False):
    quality = pd.DataFrame({
        "Indicador": ["Filas recibidas", "Nulos en variables", "Filas físicamente imposibles", "Outliers IQR detectados", "Filas utilizables"],
        "Cantidad": [
            len(raw_data),
            int(raw_data[NUMERIC_COLUMNS].isna().sum().sum()),
            len(raw_data.dropna(subset=NUMERIC_COLUMNS)) - len(cleaned_data),
            int(outlier_flags["es_outlier"].sum()),
            len(cleaned_data),
        ],
    })
    st.dataframe(quality, hide_index=True, use_container_width=True)
    st.caption("Se eliminan nulos de variables y valores fuera de rangos físicos; los outliers IQR se identifican para inspección.")

if cleaned_data.empty:
    st.error("No quedaron datos utilizables después de la limpieza.")
    st.stop()

min_date = cleaned_data["timestamp"].min().date()
max_date = cleaned_data["timestamp"].max().date()
with st.sidebar:
    st.header("Filtros dinámicos")
    selected_dates = st.date_input("Periodo", value=(min_date, max_date), min_value=min_date, max_value=max_date)
    devices = sorted(cleaned_data["dispositivo"].dropna().unique().tolist())
    selected_devices = st.multiselect("Dispositivos", devices, default=devices)
    selected_variables = st.multiselect("Variables a visualizar", NUMERIC_COLUMNS, default=NUMERIC_COLUMNS)
    remove_outliers = st.checkbox("Excluir outliers IQR", value=False)
    if not selected_variables:
        st.warning("Selecciona al menos una variable.")
        st.stop()
    selected_ranges: dict[str, tuple[float, float]] = {}
    for column in selected_variables:
        minimum, maximum = float(cleaned_data[column].min()), float(cleaned_data[column].max())
        if minimum == maximum:
            st.caption(f"{VARIABLE_LABELS[column]}: {minimum:g} (sin variación en el histórico)")
            selected_ranges[column] = (minimum, maximum)
        else:
            selected_ranges[column] = st.slider(
                f"Rango: {VARIABLE_LABELS[column]}",
                min_value=minimum,
                max_value=maximum,
                value=(minimum, maximum),
            )

if isinstance(selected_dates, tuple):
    if len(selected_dates) == 2:
        start_date, end_date = selected_dates
    elif len(selected_dates) == 1:
        start_date = end_date = selected_dates[0]
    else:
        start_date, end_date = min_date, max_date
else:
    start_date = end_date = selected_dates
filtered_data = cleaned_data[
    cleaned_data["timestamp"].dt.date.between(start_date, end_date)
    & cleaned_data["dispositivo"].isin(selected_devices)
].copy()
if remove_outliers:
    filtered_data = filtered_data.loc[~outlier_flags.loc[filtered_data.index, "es_outlier"]]
for column, (minimum, maximum) in selected_ranges.items():
    filtered_data = filtered_data[filtered_data[column].between(minimum, maximum)]

st.subheader("Resumen del histórico filtrado")
metric_columns = st.columns(4)
metric_columns[0].metric("Lecturas", f"{len(filtered_data):,}")
metric_columns[1].metric("Dispositivos", filtered_data["dispositivo"].nunique())
metric_columns[2].metric("Desde", filtered_data["timestamp"].min().strftime("%d/%m/%Y") if not filtered_data.empty else "-")
metric_columns[3].metric("Hasta", filtered_data["timestamp"].max().strftime("%d/%m/%Y") if not filtered_data.empty else "-")

if filtered_data.empty:
    st.warning("No hay lecturas con los filtros actuales.")
    st.stop()

tab_eda, tab_correlation, tab_ml, tab_data = st.tabs(["EDA", "Correlación", "Predicción ML", "Datos"])
with tab_eda:
    st.subheader("Estadísticas descriptivas")
    st.dataframe(filtered_data[NUMERIC_COLUMNS].describe().T, use_container_width=True)
    st.subheader("Distribución de variables")
    plot_distribution(filtered_data, selected_variables)
    st.subheader("Evolución temporal")
    plot_time_series(filtered_data, selected_variables)

with tab_correlation:
    st.subheader("Matriz de correlación")
    correlation = filtered_data[NUMERIC_COLUMNS].corr()
    figure, axis = plt.subplots(figsize=(7, 5))
    sns.heatmap(correlation, annot=True, fmt=".2f", cmap="coolwarm", vmin=-1, vmax=1, square=True, ax=axis)
    axis.set_title("Correlación entre variables de sensores")
    st.pyplot(figure, use_container_width=True)
    plt.close(figure)
    st.dataframe(correlation.style.format("%.3f"), use_container_width=True)

with tab_ml:
    st.subheader("Predicción de variables")
    target_variable = st.selectbox("Variable objetivo", NUMERIC_COLUMNS, format_func=lambda value: VARIABLE_LABELS[value])
    st.caption("Los modelos usan las otras variables del sensor y componentes de fecha. El último 20% del histórico se reserva para evaluar.")
    train_models(filtered_data, target_variable)

with tab_data:
    st.subheader("Lecturas filtradas")
    st.dataframe(filtered_data.sort_values("timestamp", ascending=False), use_container_width=True, hide_index=True)