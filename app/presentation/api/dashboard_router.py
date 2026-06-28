from fastapi import APIRouter, Depends
from app.application.dashboard_service import DashboardService, get_dashboard_service

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats")
def get_stats(svc: DashboardService = Depends(get_dashboard_service)):
    return svc.stats()
