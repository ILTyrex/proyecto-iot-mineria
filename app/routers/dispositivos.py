from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.dispositivo import DispositivoCreate, DispositivoOut
from app.services.dispositivo_service import DispositivoService

router = APIRouter(prefix="/api/dispositivos", tags=["Dispositivos"])


@router.post("/", response_model=DispositivoOut, status_code=201)
def crear_dispositivo(data: DispositivoCreate, db: Session = Depends(get_db)):
    service = DispositivoService(db)
    return service.crear_dispositivo(data.model_dump())


@router.get("/", response_model=List[DispositivoOut])
def listar_dispositivos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    service = DispositivoService(db)
    return service.listar(skip, limit)
