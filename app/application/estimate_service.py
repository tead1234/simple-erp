from datetime import datetime
from typing import Optional
from fastapi import Depends, HTTPException
from app.domain.estimate.entity import Estimate, EstimateItem
from app.domain.estimate.repository import IEstimateRepository
from app.domain.customer.repository import ICustomerRepository
from app.domain.maintenance.repository import IMaintenanceRepository
from app.infrastructure.database.repositories import get_estimate_repo, get_customer_repo, get_maintenance_repo
from app.application.customer_service import CustomerService


class EstimateService:
    def __init__(self, repo: IEstimateRepository, customer_repo: ICustomerRepository,
                 maintenance_repo: IMaintenanceRepository):
        self._repo = repo
        self._customer_svc = CustomerService(customer_repo)
        self._maintenance_repo = maintenance_repo

    def list(self) -> list:
        return [
            {
                "id": e.id,
                "estimate_date": e.estimate_date.isoformat() if e.estimate_date else None,
                "contractor_name": e.contractor_name,
                "total_amount": e.total_amount,
                "status": e.status,
                "item_count": len(e.items),
            }
            for e in self._repo.list()
        ]

    def get(self, estimate_id: int) -> dict:
        e = self._repo.get(estimate_id)
        if not e:
            raise HTTPException(404, "견적서를 찾을 수 없습니다")
        return {
            "id": e.id,
            "estimate_date": e.estimate_date.isoformat() if e.estimate_date else None,
            "contractor_name": e.contractor_name,
            "customer_id": e.customer_id,
            "subtotal": e.subtotal,
            "vat_amount": e.vat_amount,
            "total_amount": e.total_amount,
            "memo": e.memo,
            "status": e.status,
            "items": [
                {
                    "id": i.id, "item_number": i.item_number,
                    "region": i.region, "model_name": i.model_name,
                    "spec": i.spec, "quantity": i.quantity,
                    "unit_price": i.unit_price, "amount": i.amount, "vat": i.vat,
                }
                for i in e.items
            ],
        }

    def create(self, contractor_name: str, customer_name: Optional[str],
               customer_id: Optional[int], estimate_date: str,
               memo: Optional[str], items: list) -> dict:
        cid = None
        if customer_name:
            cid = self._customer_svc.get_or_create(customer_name, customer_id)

        est_items, subtotal, vat_total = [], 0, 0
        for item in items:
            amount = round(item["quantity"] * item["unit_price"], 2)
            vat = round(amount * 0.1, 2)
            subtotal += amount
            vat_total += vat
            est_items.append(EstimateItem(
                region=item.get("region"), model_name=item["model_name"],
                spec=item.get("spec"), quantity=item["quantity"],
                unit_price=item["unit_price"], amount=amount, vat=vat,
            ))

        e = self._repo.save(Estimate(
            contractor_name=contractor_name, customer_id=cid,
            estimate_date=datetime.fromisoformat(estimate_date),
            subtotal=round(subtotal, 2), vat_amount=round(vat_total, 2),
            total_amount=round(subtotal + vat_total, 2),
            memo=memo, items=est_items,
        ))
        return {"id": e.id}

    def update(self, estimate_id: int, contractor_name: str, customer_name: Optional[str],
               customer_id: Optional[int], estimate_date: str,
               memo: Optional[str], items: list) -> dict:
        e = self._repo.get(estimate_id)
        if not e:
            raise HTTPException(404, "견적서를 찾을 수 없습니다")
        if e.status != "작성":
            raise HTTPException(400, "작성 상태의 견적서만 수정할 수 있습니다")

        cid = None
        if customer_name:
            cid = self._customer_svc.get_or_create(customer_name, customer_id)

        est_items, subtotal, vat_total = [], 0, 0
        for item in items:
            amount = round(item["quantity"] * item["unit_price"], 2)
            vat = round(amount * 0.1, 2)
            subtotal += amount
            vat_total += vat
            est_items.append(EstimateItem(
                region=item.get("region"), model_name=item["model_name"],
                spec=item.get("spec"), quantity=item["quantity"],
                unit_price=item["unit_price"], amount=amount, vat=vat,
            ))

        e.contractor_name = contractor_name
        e.customer_id = cid or e.customer_id
        e.estimate_date = datetime.fromisoformat(estimate_date)
        e.subtotal = round(subtotal, 2)
        e.vat_amount = round(vat_total, 2)
        e.total_amount = round(subtotal + vat_total, 2)
        e.memo = memo
        e.items = est_items

        self._repo.update(e)

        linked = self._maintenance_repo.find_by_estimate_id(estimate_id)
        if linked:
            parts = [
                {"part_name": i.model_name, "quantity": i.quantity, "unit_price": i.unit_price}
                for i in est_items
            ]
            self._maintenance_repo.replace_parts(linked.id, parts)

        return {"id": e.id}

    def delete(self, estimate_id: int) -> None:
        e = self._repo.get(estimate_id)
        if not e:
            raise HTTPException(404, "견적서를 찾을 수 없습니다")
        self._repo.delete(estimate_id)

    def confirm(self, estimate_id: int) -> dict:
        e = self._repo.get(estimate_id)
        if not e:
            raise HTTPException(404, "견적서를 찾을 수 없습니다")
        try:
            e.confirm()
        except ValueError as ex:
            raise HTTPException(400, str(ex))
        self._repo.save(e)
        return {"id": e.id, "status": e.status}

    def cancel(self, estimate_id: int) -> dict:
        e = self._repo.get(estimate_id)
        if not e:
            raise HTTPException(404, "견적서를 찾을 수 없습니다")
        try:
            e.cancel()
        except ValueError as ex:
            raise HTTPException(400, str(ex))
        self._repo.save(e)
        return {"id": e.id, "status": e.status}


def get_estimate_service(
    repo: IEstimateRepository = Depends(get_estimate_repo),
    customer_repo: ICustomerRepository = Depends(get_customer_repo),
    maintenance_repo: IMaintenanceRepository = Depends(get_maintenance_repo),
) -> EstimateService:
    return EstimateService(repo, customer_repo, maintenance_repo)
