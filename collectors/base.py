from abc import ABC, abstractmethod

from models.evidence import Evidence


class BaseCollector(ABC):

    @abstractmethod
    def collect(self) -> list[Evidence]:
        """Collect and return normalized evidence."""
        raise NotImplementedError
