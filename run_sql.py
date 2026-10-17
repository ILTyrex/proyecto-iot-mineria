import sys
from pathlib import Path

import psycopg

from app.core.config import settings


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Uso: python run_sql.py <archivo.sql>")

    sql_file = Path(sys.argv[1])
    sql = sql_file.read_text(encoding="utf-8")

    with psycopg.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        dbname=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        sslmode=settings.DB_SSLMODE,
    ) as connection:
        connection.execute(sql, prepare=False)

    print("Script ejecutado correctamente")


if __name__ == "__main__":
    main()
