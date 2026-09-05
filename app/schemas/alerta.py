from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AlertaOut(BaseModel):
    id: int
    lectura_id: int
    tipo_alerta: str
    mensaje: str
    atendida: bool
    fecha_creacion: datetime

    model_config = ConfigDict(from_attributes=True)
