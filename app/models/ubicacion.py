from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class Ubicacion(Base):
    """Catálogo de lugares físicos donde se instalan los dispositivos."""
    __tablename__ = "ubicaciones"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), unique=True, nullable=False)
    descripcion = Column(String(255), nullable=True)
    zona = Column(String(50), nullable=True)

    dispositivos = relationship("Dispositivo", back_populates="ubicacion")