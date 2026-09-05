"""
Punto de entrada de la API.
Arquitectura: routers -> services -> repositories -> models (ORM)
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, engine
from app.models import *  # noqa: F401,F403  (registra todos los modelos en Base.metadata)
from app.routers import dispositivos, sensores, lecturas, alertas

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dispositivos.router)
app.include_router(sensores.router)
app.include_router(lecturas.router)
app.include_router(alertas.router)


@app.on_event("startup")
def crear_tablas():
    # Crea las tablas si no existen (el hypertable/seed se aplica con el script SQL)
    Base.metadata.create_all(bind=engine)


@app.get("/", tags=["Estado"])
def estado():
    return {"servicio": settings.APP_NAME, "version": settings.APP_VERSION, "estado": "activo"}
