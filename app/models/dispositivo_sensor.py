from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


class DispositivoSensor(Base):
    """Tabla intermedia: qué sensor está conectado a qué dispositivo y en qué pin."""
    __tablename__ = "dispositivo_sensores"
    __table_args__ = (UniqueConstraint("dispositivo_id", "sensor_id", name="uq_dispositivo_sensor"),)

    id = Column(Integer, primary_key=True, index=True)
    dispositivo_id = Column(Integer, ForeignKey("dispositivos.id"), nullable=False)
    sensor_id = Column(Integer, ForeignKey("sensores.id"), nullable=False)
    pin = Column(String(30), nullable=True)

    dispositivo = relationship("Dispositivo", back_populates="dispositivo_sensores")
    sensor = relationship("Sensor", back_populates="dispositivo_sensores")
