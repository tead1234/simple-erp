from abc import ABC, abstractmethod
from typing import Optional, List
from .entity import FieldTrip


class IFieldTripRepository(ABC):
    @abstractmethod
    def list(self, status: Optional[str] = None) -> List[FieldTrip]: ...
    @abstractmethod
    def get(self, id: int) -> Optional[FieldTrip]: ...
    @abstractmethod
    def save(self, fieldtrip: FieldTrip) -> FieldTrip: ...
