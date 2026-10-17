from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class TipoAlerta(Base):
    """Catálogo de tipos de alerta (ej. Calidad Mala, Calidad Peligrosa)."""
    __tablename__ = "tipos_alerta"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, nullable=False)
    descripcion = Column(String(255), nullable=True)
    severidad = Column(String(20), nullable=False)  # ej. media, alta, critica

    alertas = relationship("Alerta", back_populates="tipo")