from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class Sensor(Base):
    """Catálogo de tipos de sensores soportados (DHT22, MQ-135, etc.)."""
    __tablename__ = "sensores"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, nullable=False)
    tipo = Column(String(50), nullable=False)
    unidad_medida = Column(String(20), nullable=False)
    descripcion = Column(String(255), nullable=True)

    dispositivo_sensores = relationship("DispositivoSensor", back_populates="sensor")
