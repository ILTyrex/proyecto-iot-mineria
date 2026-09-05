from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class LecturaCreate(BaseModel):
    """
    Cuerpo JSON que el ESP32 debe enviar por HTTP POST.
    Los rangos de validación corresponden a las hojas de datos de los
    sensores usados en el proyecto (DHT22 y MQ-135).
    """
    codigo_dispositivo: str = Field(..., description="Código único del dispositivo, ej: ESP32-G3")
    temperatura: float = Field(..., ge=-40, le=80, description="°C - rango DHT22: -40 a 80")
    humedad: float = Field(..., ge=0, le=100, description="% - rango DHT22: 0 a 100")
    co2_ppm: float = Field(..., ge=0, le=10000, description="ppm estimado - MQ-135")


class LecturaOut(BaseModel):
    id: int
    dispositivo_id: int
    temperatura: float
    humedad: float
    co2_ppm: float
    nivel_calidad: Optional[str] = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
