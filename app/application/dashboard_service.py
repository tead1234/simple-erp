from fastapi import Depends
from app.infrastructure.database.repositories import DashboardQuery, get_dashboard_query


class DashboardService:
    def __init__(self, query: DashboardQuery):
        self._query = query

    def stats(self) -> dict:
        return self._query.stats()

    def revenue_detail(self, year: int, month: int) -> dict:
        return self._query.revenue_detail(year, month)


def get_dashboard_service(query: DashboardQuery = Depends(get_dashboard_query)) -> DashboardService:
    return DashboardService(query)
