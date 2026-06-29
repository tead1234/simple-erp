from abc import ABC, abstractmethod
from typing import Optional, List
from .entity import Sale


class ISaleRepository(ABC):
    @abstractmethod
    def get(self, id: int) -> Optional[Sale]: ...
    @abstractmethod
    def list(self, machine_category: Optional[str] = None) -> List[Sale]: ...
    @abstractmethod
    def save(self, sale: Sale) -> Sale: ...
