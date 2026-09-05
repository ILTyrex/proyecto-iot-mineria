from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.alerta import AlertaOut
from app.services.alerta_service import AlertaService
from app.repositories.alerta_repository import AlertaRepository

router = APIRouter(prefix="/api/alertas", tags=["Alertas"])


@router.get("/", response_model=List[AlertaOut])
def listar_alertas_pendientes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    repo = AlertaRepository(db)
    return repo.listar_no_atendidas(skip, limit)


@router.patch("/{alerta_id}/atender", response_model=AlertaOut)
def atender_alerta(alerta_id: int, db: Session = Depends(get_db)):
    service = AlertaService(db)
    return service.marcar_atendida(alerta_id)
