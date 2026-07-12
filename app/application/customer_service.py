from typing import Optional, List
from fastapi import Depends, HTTPException
from app.domain.customer.entity import Customer
from app.domain.customer.repository import ICustomerRepository
from app.infrastructure.database.repositories import get_customer_repo


class CustomerService:
    def __init__(self, repo: ICustomerRepository):
        self._repo = repo

    def list(self, q: str = "") -> List[Customer]:
        return self._repo.search(q.strip())

    def create(self, name: str, phone=None, address=None, memo=None) -> Customer:
        return self._repo.save(Customer(name=name.strip(), phone=phone, address=address, memo=memo))

    def update(self, customer_id: int, name: str, phone=None, address=None, memo=None) -> Customer:
        c = self._repo.get(customer_id)
        if not c:
            raise HTTPException(404, "고객을 찾을 수 없습니다")
        c.name = name.strip()
        c.phone = phone
        c.address = address
        c.memo = memo
        return self._repo.save(c)

    def update_receivable_memo(self, customer_id: int, memo: Optional[str]) -> Customer:
        c = self._repo.get(customer_id)
        if not c:
            raise HTTPException(404, "고객을 찾을 수 없습니다")
        c.receivable_memo = memo
        return self._repo.save(c)

    def delete(self, customer_id: int) -> None:
        if not self._repo.get(customer_id):
            raise HTTPException(404, "고객을 찾을 수 없습니다")
        self._repo.delete(customer_id)

    def get_or_create(self, name: str, customer_id: Optional[int] = None) -> int:
        name = name.strip()
        if not name:
            raise HTTPException(400, "고객명을 입력하세요")
        if customer_id:
            if not self._repo.get(customer_id):
                raise HTTPException(400, f"존재하지 않는 고객 ID: {customer_id}")
            return customer_id
        existing = self._repo.find_by_name(name)
        if existing:
            return existing.id
        return self._repo.save(Customer(name=name)).id


def get_customer_service(repo: ICustomerRepository = Depends(get_customer_repo)) -> CustomerService:
    return CustomerService(repo)
