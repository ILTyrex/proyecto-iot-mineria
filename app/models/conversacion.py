from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Conversacion(Base):
    """Sesión de conversación identificada por un UUID (32 caracteres)."""

    __tablename__ = "conversaciones"

    id = Column(String(32), primary_key=True)
    creada_en = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    mensajes = relationship("MensajeConversacion", back_populates="conversacion")
