from datetime import datetime
from fastapi import Depends, HTTPException
from app.domain.fieldtrip.entity import FieldTrip
from app.domain.fieldtrip.repository import IFieldTripRepository
from app.domain.customer.repository import ICustomerRepository
from app.infrastructure.database.repositories import get_fieldtrip_repo, get_customer_repo


class FieldTripService:
    def __init__(self, repo: IFieldTripRepository, customer_repo: ICustomerRepository):
        self.repo = repo
        self.customer_repo = customer_repo

    def list(self, status=None):
        trips = self.repo.list(status)
        result = []
        for t in trips:
            c = self.customer_repo.get(t.customer_id)
            d = t.__dict__.copy()
            d["customer_name"] = c.name if c else "-"
            result.append(d)
        return result

    def create(self, customer_id: int, scheduled_date: str, purpose: str = None) -> dict:
        c = self.customer_repo.get(customer_id)
        if not c:
            raise HTTPException(404, "고객을 찾을 수 없습니다")
        dt = datetime.fromisoformat(scheduled_date)
        trip = self.repo.save(FieldTrip(customer_id=customer_id, scheduled_date=dt, purpose=purpose))
        d = trip.__dict__.copy()
        d["customer_name"] = c.name
        return d

    def update(self, trip_id: int, status: str = None, result: str = None) -> dict:
        trip = self.repo.get(trip_id)
        if not trip:
            raise HTTPException(404, "출장을 찾을 수 없습니다")
        if status:
            trip.status = status
        if result is not None:
            trip.result = result
        trip = self.repo.save(trip)
        c = self.customer_repo.get(trip.customer_id)
        d = trip.__dict__.copy()
        d["customer_name"] = c.name if c else "-"
        return d


def get_fieldtrip_service(
    repo: IFieldTripRepository = Depends(get_fieldtrip_repo),
    customer_repo: ICustomerRepository = Depends(get_customer_repo),
) -> FieldTripService:
    return FieldTripService(repo, customer_repo)
