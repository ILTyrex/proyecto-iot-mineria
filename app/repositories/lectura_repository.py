from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload

from app.models.lectura import Lectura
from app.models.dispositivo import Dispositivo
from app.repositories.base_repository import BaseRepository


class LecturaRepository(BaseRepository[Lectura]):
    def __init__(self, db: Session):
        super().__init__(Lectura, db)

    def create(self, obj_in: dict) -> Lectura:
        # Sobrescribe create() para siempre traer la relación nivel_calidad cargada
        lectura = super().create(obj_in)
        return lectura

    def filtrar(
        self,
        dispositivo_codigo: Optional[str] = None,
        fecha_inicio: Optional[datetime] = None,
        fecha_fin: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Lectura]:
        query = (
            self.db.query(Lectura)
            .options(joinedload(Lectura.nivel_calidad))
            .join(Dispositivo, Lectura.dispositivo_id == Dispositivo.id)
        )

        if dispositivo_codigo:
            query = query.filter(Dispositivo.codigo == dispositivo_codigo)
        if fecha_inicio:
            query = query.filter(Lectura.timestamp >= fecha_inicio)
        if fecha_fin:
            query = query.filter(Lectura.timestamp <= fecha_fin)

        return (
            query.order_by(Lectura.timestamp.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
