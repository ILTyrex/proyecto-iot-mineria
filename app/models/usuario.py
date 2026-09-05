from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func

from app.core.database import Base


class Usuario(Base):
    """Usuarios que pueden consultar la API / futuros dashboards (autenticación)."""
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    rol = Column(String(30), default="analista", nullable=False)
    activo = Column(Boolean, default=True, nullable=False)
    fecha_registro = Column(DateTime(timezone=True), server_default=func.now())
