from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class AlertaOut(BaseModel):
    id: int
    lectura_id: int
    tipo_alerta_id: int
    tipo_alerta: Optional[str] = None
    mensaje: str
    atendida: bool
    fecha_creacion: datetime

    model_config = ConfigDict(from_attributes=True)