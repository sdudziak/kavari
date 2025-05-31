from abc import ABC, abstractmethod
from typing import List


class RetryPolicy(ABC):
    @abstractmethod
    def delays(self) -> List[int]:
        pass