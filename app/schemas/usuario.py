from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UsuarioCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    rol: str = Field(default="analista", max_length=30)


class UsuarioOut(BaseModel):
    id: int
    nombre: str
    email: EmailStr
    rol: str
    activo: bool
    fecha_registro: datetime

    model_config = ConfigDict(from_attributes=True)
