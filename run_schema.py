from pathlib import Path

import psycopg

from app.core.config import settings


SCHEMA_FILE = Path(__file__).resolve().parent / "init_db" / "schema_completo.sql"
EXPECTED_TABLES = {
    "alertas",
    "dispositivo_sensores",
    "dispositivos",
    "lecturas",
    "logs_sistema",
    "niveles_calidad_aire",
    "sensores",
    "tipos_alerta",
    "ubicaciones",
    "usuarios",
}


def main() -> None:
    sql = SCHEMA_FILE.read_text(encoding="utf-8")

    with psycopg.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        dbname=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        sslmode=settings.DB_SSLMODE,
        connect_timeout=15,
    ) as connection:
        connection.execute(sql, prepare=False)

        tables = {
            row[0]
            for row in connection.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = current_schema()
                  AND table_type = 'BASE TABLE'
                """
            ).fetchall()
        }
        missing_tables = EXPECTED_TABLES - tables
        if missing_tables:
            raise RuntimeError(f"Faltan tablas en el esquema: {sorted(missing_tables)}")

        extension_installed = connection.execute(
            "SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'timescaledb')"
        ).fetchone()[0]
        hypertable_exists = connection.execute(
            """
            SELECT EXISTS (
                SELECT 1
                FROM timescaledb_information.hypertables
                WHERE hypertable_schema = current_schema()
                  AND hypertable_name = 'lecturas'
            )
            """
        ).fetchone()[0]

        if not extension_installed or not hypertable_exists:
            raise RuntimeError(
                "La extensión TimescaleDB o la hypertable 'lecturas' no quedó creada."
            )

    print("Script ejecutado correctamente.")
    print("Verificación: 10 tablas, extensión TimescaleDB y hypertable 'lecturas' presentes.")


if __name__ == "__main__":
    main()
