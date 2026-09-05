from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class DispositivoCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    codigo: str = Field(..., min_length=2, max_length=50, description="Código único, ej: ESP32-G3")
    ubicacion: Optional[str] = Field(None, max_length=150)
    mac_address: Optional[str] = Field(None, max_length=50)


class DispositivoOut(BaseModel):
    id: int
    nombre: str
    codigo: str
    ubicacion: Optional[str]
    activo: bool
    fecha_registro: datetime

    model_config = ConfigDict(from_attributes=True)
