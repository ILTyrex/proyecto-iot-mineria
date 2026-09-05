"""
Configuración centralizada de la aplicación.
Lee las variables de entorno (o el archivo .env) y las expone como un
único objeto "settings" para ser usado en el resto del proyecto.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "API Monitoreo de Calidad del Aire - IoT"
    APP_VERSION: str = "1.0.0"

    # Clave que el ESP32 (y cualquier cliente) debe enviar en el header
    # "X-API-Key" para poder registrar lecturas.
    API_KEY: str = "emo-vengador"

    # Datos de conexión a PostgreSQL / TimescaleDB
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "calidad_aire_db"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    # Tiger Cloud (y la mayoría de proveedores en la nube) exigen SSL.
    # En localhost/Docker se puede dejar en "disable".
    DB_SSLMODE: str = "require"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+psycopg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            f"?sslmode={self.DB_SSLMODE}"
        )


settings = Settings()
