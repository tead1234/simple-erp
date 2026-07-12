from datetime import datetime
from fastapi import APIRouter, Depends, Query
from app.application.dashboard_service import DashboardService, get_dashboard_service

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats")
def get_stats(svc: DashboardService = Depends(get_dashboard_service)):
    return svc.stats()


@router.get("/revenue-detail")
def get_revenue_detail(
    year: int = Query(None),
    month: int = Query(None),
    svc: DashboardService = Depends(get_dashboard_service),
):
    now = datetime.now()
    return svc.revenue_detail(year or now.year, month or now.month)
