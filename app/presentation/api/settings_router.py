from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from app.application.settings_service import SettingsService, get_settings_service
from app.infrastructure.database.session import get_db

router = APIRouter(prefix="/api/settings", tags=["settings"])


class SettingsIn(BaseModel):
    registration_number: Optional[str] = None
    company_name: Optional[str] = None
    owner_name: Optional[str] = None
    address: Optional[str] = None
    business_type: Optional[str] = None
    business_category: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    email: Optional[str] = None
    bank_account: Optional[str] = None


@router.get("")
def get_settings(svc: SettingsService = Depends(get_settings_service)):
    return svc.get()


@router.post("")
def save_settings(data: SettingsIn, svc: SettingsService = Depends(get_settings_service), db: Session = Depends(get_db)):
    svc.save(**data.model_dump())
    db.commit()
    return {"ok": True}
