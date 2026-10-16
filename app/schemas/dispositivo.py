from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class DispositivoCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    codigo: str = Field(..., min_length=2, max_length=50, description="Código único, ej: ESP32-G3")
    ubicacion_id: Optional[int] = Field(None, description="ID de la ubicación (tabla ubicaciones)")
    mac_address: Optional[str] = Field(None, max_length=50)


class DispositivoOut(BaseModel):
    id: int
    nombre: str
    codigo: str
    ubicacion_id: Optional[int] = None
    ubicacion_nombre: Optional[str] = None
    activo: bool
    fecha_registro: datetime

    model_config = ConfigDict(from_attributes=True)