from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
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

    id = Column(Integer, primary_key=True, index=True)
    lectura_id = Column(Integer, nullable=False)
    lectura_timestamp = Column(DateTime(timezone=True), nullable=False)
    tipo_alerta_id = Column(Integer, ForeignKey("tipos_alerta.id"), nullable=False)

    mensaje = Column(String(255), nullable=False)
    atendida = Column(Boolean, default=False, nullable=False)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())

    lectura = relationship(
        "Lectura",
        primaryjoin="and_(Alerta.lectura_id == Lectura.id, Alerta.lectura_timestamp == Lectura.timestamp)",
        foreign_keys="[Alerta.lectura_id, Alerta.lectura_timestamp]",
        back_populates="alertas",
    )
    tipo = relationship("TipoAlerta", back_populates="alertas")