from datetime import datetime
from typing import Optional, List
from fastapi import Depends, HTTPException
from app.domain.sale.entity import Sale, SaleItem
from app.domain.sale.repository import ISaleRepository
from app.domain.customer.repository import ICustomerRepository
from app.infrastructure.database.repositories import get_sale_repo, get_customer_repo
from app.application.customer_service import CustomerService


class SaleService:
    def __init__(self, sale_repo: ISaleRepository, customer_repo: ICustomerRepository):
        self._sale_repo = sale_repo
        self._customer_svc = CustomerService(customer_repo)

    def list(self, machine_category: Optional[str] = None) -> list:
        sales = self._sale_repo.list(machine_category)
        result = []
        for s in sales:
            total = sum(i.total_amount for i in s.items)
            self_pay = sum(i.self_pay_amount for i in s.items)
            summary = ", ".join(i.product_name for i in s.items if i.product_name)
            result.append({
                "id": s.id,
                "sale_date": s.sale_date.isoformat() if s.sale_date else None,
                "customer_name": self._get_customer_name(s.customer_id),
                "items_summary": summary[:30] + ("…" if len(summary) > 30 else ""),
                "total_amount": total,
                "self_pay_amount": self_pay,
                "machine_category": s.machine_category,
                "memo": s.memo,
            })
        return result

    def get(self, sale_id: int) -> dict:
        sale = self._sale_repo.get(sale_id)
        if not sale:
            raise HTTPException(404, "판매 내역을 찾을 수 없습니다")
        customer = self._customer_svc._repo.get(sale.customer_id)
        return {
            "id": sale.id,
            "sale_date": sale.sale_date.isoformat() if sale.sale_date else None,
            "customer_name": customer.name if customer else "-",
            "customer_phone": customer.phone if customer else None,
            "memo": sale.memo,
            "items": [
                {
                    "product_name": i.product_name, "model_name": i.model_name,
                    "product_code": i.product_code, "total_amount": i.total_amount,
                    "loan_amount": i.loan_amount, "self_pay_amount": i.self_pay_amount,
                    "loan_code": i.loan_code, "memo": i.memo,
                }
                for i in sale.items
            ],
        }

    def create(self, sale_date: str, customer_name: str, customer_id: Optional[int],
               memo: Optional[str], machine_category: Optional[str], items: list) -> dict:
        cid = self._customer_svc.get_or_create(customer_name, customer_id)
        sale_items = []
        for item in items:
            self_pay = round(item["total_amount"] - item["loan_amount"], 2)
            sale_items.append(SaleItem(
                product_name=item["product_name"],
                model_name=item.get("model_name"),
                product_code=item.get("product_code"),
                total_amount=item["total_amount"],
                loan_amount=item["loan_amount"],
                self_pay_amount=self_pay,
                loan_code=item.get("loan_code"),
                memo=item.get("memo"),
            ))

        sale = self._sale_repo.save(Sale(
            sale_date=datetime.fromisoformat(sale_date),
            customer_id=cid,
            memo=memo,
            machine_category=machine_category,
            items=sale_items,
        ))
        return {"id": sale.id}

    def _get_customer_name(self, customer_id: int) -> str:
        c = self._customer_svc._repo.get(customer_id)
        return c.name if c else "-"


def get_sale_service(
    sale_repo: ISaleRepository = Depends(get_sale_repo),
    customer_repo: ICustomerRepository = Depends(get_customer_repo),
) -> SaleService:
    return SaleService(sale_repo, customer_repo)
