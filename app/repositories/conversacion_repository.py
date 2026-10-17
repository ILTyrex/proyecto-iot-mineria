from sqlalchemy.orm import Session, selectinload

from app.models.conversacion import Conversacion
from app.models.mensaje_conversacion import MensajeConversacion


class ConversacionRepository:
    def __init__(self, db: Session):
        self.db = db

    def listar(self, skip: int = 0, limit: int = 50) -> list[Conversacion]:
        return (
            self.db.query(Conversacion)
            .options(selectinload(Conversacion.mensajes))
            .order_by(Conversacion.creada_en.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def obtener(self, conversacion_id: str) -> Conversacion | None:
        conversacion = (
            self.db.query(Conversacion)
            .options(selectinload(Conversacion.mensajes))
            .filter(Conversacion.id == conversacion_id)
            .first()
        )
        if conversacion:
            conversacion.mensajes.sort(key=lambda mensaje: (mensaje.creado_en, mensaje.id))
        return conversacion

    def agregar_mensaje(self, conversacion_id: str, role: str, content: str) -> MensajeConversacion:
        conversacion = self.db.get(Conversacion, conversacion_id)
        if conversacion is None:
            conversacion = Conversacion(id=conversacion_id)
            self.db.add(conversacion)
            self.db.flush()

        mensaje = MensajeConversacion(
            conversacion_id=conversacion_id,
            role=role,
            content=content,
        )
        self.db.add(mensaje)
        self.db.commit()
        self.db.refresh(mensaje)
        return mensaje