"""
Configuración de la conexión a la base de datos con SQLAlchemy.
Expone:
  - engine: motor de conexión a PostgreSQL/TimescaleDB
  - SessionLocal: fábrica de sesiones
  - Base: clase base para los modelos ORM
  - get_db: dependencia de FastAPI para inyectar una sesión por request
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependencia de FastAPI: entrega una sesión y la cierra al finalizar."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
