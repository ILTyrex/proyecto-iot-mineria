from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verificar_api_key
from app.schemas.lectura import LecturaCreate, LecturaOut
from app.services.lectura_service import LecturaService
from app.repositories.lectura_repository import LecturaRepository

router = APIRouter(prefix="/api/lecturas", tags=["Lecturas"])


def _a_schema(lectura) -> LecturaOut:
    return LecturaOut(
        id=lectura.id,
        dispositivo_id=lectura.dispositivo_id,
        temperatura=lectura.temperatura,
        humedad=lectura.humedad,
        co2_ppm=lectura.co2_ppm,
        nivel_calidad=lectura.nivel_calidad.nombre if lectura.nivel_calidad else None,
        timestamp=lectura.timestamp,
    )


@router.post(
    "/",
    response_model=LecturaOut,
    status_code=201,
    dependencies=[Depends(verificar_api_key)],
    summary="Endpoint que usa el ESP32 para enviar cada lectura (POST + header X-API-Key)",
)
def crear_lectura(data: LecturaCreate, db: Session = Depends(get_db)):
    service = LecturaService(db)
    lectura = service.registrar_lectura(
        codigo_dispositivo=data.codigo_dispositivo,
        temperatura=data.temperatura,
        humedad=data.humedad,
        co2_ppm=data.co2_ppm,
    )
    return _a_schema(lectura)


@router.get("/", response_model=List[LecturaOut], summary="Consulta histórica (usada por Streamlit / Power BI)")
def listar_lecturas(
    dispositivo_codigo: Optional[str] = None,
    fecha_inicio: Optional[datetime] = None,
    fecha_fin: Optional[datetime] = None,
    skip: int = 0,
    limit: int = Query(default=100, le=1000),
    db: Session = Depends(get_db),
):
    repo = LecturaRepository(db)
    lecturas = repo.filtrar(dispositivo_codigo, fecha_inicio, fecha_fin, skip, limit)
    return [_a_schema(l) for l in lecturas]
