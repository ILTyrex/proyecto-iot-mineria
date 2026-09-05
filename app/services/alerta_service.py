from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.repositories.alerta_repository import AlertaRepository


class AlertaService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AlertaRepository(db)

    def marcar_atendida(self, alerta_id: int):
        alerta = self.repo.get(alerta_id)
        if not alerta:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alerta no encontrada")
        alerta.atendida = True
        self.db.commit()
        self.db.refresh(alerta)
        return alerta
