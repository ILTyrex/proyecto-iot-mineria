from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, expression
from app.core.database import Base


class Dispositivo(Base):
    """Representa un dispositivo ESP32 físico registrado en el sistema."""

    __tablename__ = "dispositivos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    codigo = Column(String(50), unique=True, nullable=False, index=True)
    ubicacion_id = Column(Integer, ForeignKey("ubicaciones.id"), nullable=True)
    mac_address = Column(String(50), unique=True, nullable=True)
    activo = Column(Boolean, server_default=expression.true(), nullable=False)
    fecha_registro = Column(DateTime(timezone=True), server_default=func.now())

    ubicacion = relationship("Ubicacion", back_populates="dispositivos")
    dispositivo_sensores = relationship(
        "DispositivoSensor", back_populates="dispositivo"
    )
    lecturas = relationship("Lectura", back_populates="dispositivo")
    logs = relationship("LogSistema", back_populates="dispositivo")