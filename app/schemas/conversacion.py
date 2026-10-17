from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class MensajeConversacionCreate(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1)


class MensajeConversacionOut(BaseModel):
    id: int
    role: Literal["user", "assistant"]
    content: str
    creado_en: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversacionOut(BaseModel):
    id: str
    creada_en: datetime
    mensajes: list[MensajeConversacionOut]

    model_config = ConfigDict(from_attributes=True)


class ConversacionResumen(BaseModel):
    id: str
    creada_en: datetime
    titulo: str
    cantidad_mensajes: int