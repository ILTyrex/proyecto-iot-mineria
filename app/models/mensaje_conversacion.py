from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class MensajeConversacion(Base):
    """Mensaje de una conversación; role es 'user' o 'assistant'."""

    __tablename__ = "mensajes_conversacion"
    __table_args__ = (
        CheckConstraint("role IN ('user', 'assistant')", name="ck_mensajes_conversacion_role"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversacion_id = Column(String(32), ForeignKey("conversaciones.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    creado_en = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    conversacion = relationship("Conversacion", back_populates="mensajes")
