import re

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verificar_api_key
from app.repositories.conversacion_repository import ConversacionRepository
from app.schemas.conversacion import (
    ConversacionOut,
    ConversacionResumen,
    MensajeConversacionCreate,
    MensajeConversacionOut,
)

router = APIRouter(
    prefix="/api/conversaciones",
    tags=["Conversaciones"],
    dependencies=[Depends(verificar_api_key)],
)


def _ordenar_mensajes(conversacion) -> None:
    conversacion.mensajes.sort(key=lambda mensaje: (mensaje.creado_en, mensaje.id))


@router.get("/", response_model=list[ConversacionResumen])
def listar_conversaciones(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    conversaciones = ConversacionRepository(db).listar(skip, limit)
    resumenes = []
    for conversacion in conversaciones:
        _ordenar_mensajes(conversacion)
        primer_mensaje = next(
            (mensaje.content for mensaje in conversacion.mensajes if mensaje.role == "user"),
            "Conversación nueva",
        )
        resumenes.append(
            ConversacionResumen(
                id=conversacion.id,
                creada_en=conversacion.creada_en,
                titulo=primer_mensaje[:80],
                cantidad_mensajes=len(conversacion.mensajes),
            )
        )
    return resumenes


@router.get("/{conversacion_id}", response_model=ConversacionOut)
def obtener_conversacion(conversacion_id: str, db: Session = Depends(get_db)):
    if not re.fullmatch(r"[0-9a-f]{32}", conversacion_id):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="ID de conversación inválido")

    conversacion = ConversacionRepository(db).obtener(conversacion_id)
    if conversacion is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversación no encontrada")
    return conversacion


@router.post(
    "/{conversacion_id}/mensajes",
    response_model=MensajeConversacionOut,
    status_code=status.HTTP_201_CREATED,
)
def guardar_mensaje(
    conversacion_id: str,
    mensaje: MensajeConversacionCreate,
    db: Session = Depends(get_db),
):
    if not re.fullmatch(r"[0-9a-f]{32}", conversacion_id):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="ID de conversación inválido")

    return ConversacionRepository(db).agregar_mensaje(
        conversacion_id=conversacion_id,
        role=mensaje.role,
        content=mensaje.content,
    )