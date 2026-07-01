from fastapi import Depends, HTTPException
from app.domain.equipment.entity import Equipment
from app.domain.equipment.repository import IEquipmentRepository
from app.infrastructure.database.repositories import get_equipment_repo
from datetime import datetime
from typing import Optional


class EquipmentService:
    def __init__(self, repo: IEquipmentRepository):
        self.repo = repo

    def list(self) -> list:
        return [self._to_dict(e) for e in self.repo.list()]

    def get(self, id: int) -> dict:
        e = self.repo.get(id)
        if not e:
            raise HTTPException(404, "장비를 찾을 수 없습니다")
        return self._to_dict(e)

    def create(self, customer_id: Optional[int], chassis_number: Optional[str],
               machine_type: Optional[str], model_name: Optional[str],
               purchase_date: Optional[str], memo: Optional[str]) -> dict:
        pd = datetime.fromisoformat(purchase_date) if purchase_date else None
        e = self.repo.save(Equipment(
            customer_id=customer_id, chassis_number=chassis_number,
            machine_type=machine_type, model_name=model_name,
            purchase_date=pd, memo=memo,
        ))
        return self._to_dict(e)

    def update(self, id: int, **kwargs) -> dict:
        e = self.repo.get(id)
        if not e:
            raise HTTPException(404, "장비를 찾을 수 없습니다")
        if "purchase_date" in kwargs and kwargs["purchase_date"]:
            kwargs["purchase_date"] = datetime.fromisoformat(kwargs["purchase_date"])
        for k, v in kwargs.items():
            if hasattr(e, k):
                setattr(e, k, v)
        e = self.repo.save(e)
        return self._to_dict(e)

    def delete(self, id: int) -> None:
        e = self.repo.get(id)
        if not e:
            raise HTTPException(404, "장비를 찾을 수 없습니다")
        self.repo.delete(id)

    def find_by_customer(self, customer_id: int) -> list:
        return [self._to_dict(e) for e in self.repo.find_by_customer(customer_id)]

    def _to_dict(self, e: Equipment) -> dict:
        return {
            "id": e.id,
            "customer_id": e.customer_id,
            "chassis_number": e.chassis_number,
            "machine_type": e.machine_type,
            "model_name": e.model_name,
            "purchase_date": e.purchase_date.isoformat() if e.purchase_date else None,
            "memo": e.memo,
        }


def get_equipment_service(repo: IEquipmentRepository = Depends(get_equipment_repo)) -> EquipmentService:
    return EquipmentService(repo)
