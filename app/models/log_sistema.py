from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class LogSistema(Base):
    """Bitácora de eventos: lecturas recibidas, reconexiones WiFi, errores, etc."""
    __tablename__ = "logs_sistema"

    id = Column(Integer, primary_key=True, index=True)
    dispositivo_id = Column(Integer, ForeignKey("dispositivos.id"), nullable=True)
    evento = Column(String(50), nullable=False)
    detalle = Column(String(255), nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    dispositivo = relationship("Dispositivo", back_populates="logs")
