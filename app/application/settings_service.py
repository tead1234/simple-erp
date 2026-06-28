from typing import Optional
from fastapi import Depends
from app.domain.settings.entity import CompanySettings
from app.domain.settings.repository import ISettingsRepository
from app.infrastructure.database.repositories import get_settings_repo


class SettingsService:
    def __init__(self, repo: ISettingsRepository):
        self._repo = repo

    def get(self) -> dict:
        s = self._repo.get()
        if not s:
            return {}
        return {
            "registration_number": s.registration_number, "company_name": s.company_name,
            "owner_name": s.owner_name, "address": s.address,
            "business_type": s.business_type, "business_category": s.business_category,
            "phone": s.phone, "mobile": s.mobile, "email": s.email,
            "bank_account": s.bank_account,
        }

    def save(self, **kwargs) -> None:
        self._repo.save(CompanySettings(**kwargs))


def get_settings_service(repo: ISettingsRepository = Depends(get_settings_repo)) -> SettingsService:
    return SettingsService(repo)
