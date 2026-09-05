from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class SensorOut(BaseModel):
    id: int
    nombre: str
    tipo: str
    unidad_medida: str
    descripcion: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class DispositivoSensorCreate(BaseModel):
    dispositivo_codigo: str = Field(..., description="Código del dispositivo, ej: ESP32-G3")
    sensor_nombre: str = Field(..., description="Nombre del sensor, ej: DHT22")
    pin: Optional[str] = Field(None, description="Pin(es) usado(s), ej: GPIO4")
