from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.repositories.dispositivo_repository import DispositivoRepository


class DispositivoService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = DispositivoRepository(db)

    def crear_dispositivo(self, data: dict):
        existente = self.repo.get_by_codigo(data["codigo"])
        if existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ya existe un dispositivo con el código '{data['codigo']}'",
            )
        return self.repo.create(data)

    def listar(self, skip: int = 0, limit: int = 100):
        return self.repo.get_all(skip, limit)
