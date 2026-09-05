"""
Repositorio genérico: implementa operaciones CRUD reutilizables.
Cada repositorio concreto hereda de esta clase (Programación Orientada
a Objetos: herencia + genéricos con TypeVar).
"""
from typing import TypeVar, Generic, Type, List, Optional
from sqlalchemy.orm import Session

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db

    def get(self, id: int) -> Optional[ModelType]:
        return self.db.query(self.model).filter(self.model.id == id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        return self.db.query(self.model).offset(skip).limit(limit).all()

    def create(self, obj_in: dict) -> ModelType:
        obj = self.model(**obj_in)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, id: int) -> bool:
        obj = self.get(id)
        if not obj:
            return False
        self.db.delete(obj)
        self.db.commit()
        return True
