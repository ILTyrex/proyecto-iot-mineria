from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Lectura(Base):
    """
    Lectura periódica enviada por el ESP32 (DHT22 + MQ-135).
    Esta tabla se convierte en "hypertable" de TimescaleDB usando la
    columna "timestamp" como columna de particionamiento (ver
    init_db/02_hypertable_y_seed.sql). Por eso la llave primaria es
    compuesta (id, timestamp): TimescaleDB exige que toda llave
    primaria/única incluya la columna de tiempo.
    """
    __tablename__ = "lecturas"

    id = Column(Integer, autoincrement=True, primary_key=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), primary_key=True, index=True)

    dispositivo_id = Column(Integer, ForeignKey("dispositivos.id"), nullable=False, index=True)
    nivel_calidad_id = Column(Integer, ForeignKey("niveles_calidad_aire.id"), nullable=True)

    temperatura = Column(Float, nullable=False)   # °C  (DHT22)
    humedad = Column(Float, nullable=False)        # %   (DHT22)
    co2_ppm = Column(Float, nullable=False)         # ppm (MQ-135, estimado)

    dispositivo = relationship("Dispositivo", back_populates="lecturas")
    nivel_calidad = relationship("NivelCalidadAire", back_populates="lecturas")
    alertas = relationship("Alerta", back_populates="lectura")
