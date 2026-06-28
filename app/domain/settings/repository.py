from abc import ABC, abstractmethod
from typing import Optional
from .entity import CompanySettings


class ISettingsRepository(ABC):
    @abstractmethod
    def get(self) -> Optional[CompanySettings]: ...
    @abstractmethod
    def save(self, settings: CompanySettings) -> None: ...
