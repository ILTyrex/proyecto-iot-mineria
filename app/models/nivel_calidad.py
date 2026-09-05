from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import relationship

from app.core.database import Base


class NivelCalidadAire(Base):
    """
    Catálogo de niveles de calidad del aire según rango de CO2 (ppm),
    replica la escala usada en el firmware del ESP32.
    """
    __tablename__ = "niveles_calidad_aire"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(30), unique=True, nullable=False)
    ppm_min = Column(Float, nullable=False)
    ppm_max = Column(Float, nullable=False)
    color = Column(String(20), nullable=True)
    descripcion = Column(String(255), nullable=True)

    lecturas = relationship("Lectura", back_populates="nivel_calidad")
