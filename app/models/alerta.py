from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKeyConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Alerta(Base):
    """
    Alerta generada automáticamente cuando una lectura cae en un nivel
    de calidad de aire "Mala" o "Peligrosa". Referencia a la llave
    primaria compuesta (id, timestamp) de "lecturas".
    """
    __tablename__ = "alertas"
    __table_args__ = (
        ForeignKeyConstraint(
            ["lectura_id", "lectura_timestamp"],
            ["lecturas.id", "lecturas.timestamp"],
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    lectura_id = Column(Integer, nullable=False)
    lectura_timestamp = Column(DateTime(timezone=True), nullable=False)

    tipo_alerta = Column(String(50), nullable=False)
    mensaje = Column(String(255), nullable=False)
    atendida = Column(Boolean, default=False, nullable=False)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())

    lectura = relationship("Lectura", back_populates="alertas")
