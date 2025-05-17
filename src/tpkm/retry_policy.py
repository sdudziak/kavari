from abc import ABC, abstractmethod
from typing import List


class RetryPolicy(ABC):
    @abstractmethod
    def delays(self) -> List[int]:
        pass


class FibonacciRetryPolicy(RetryPolicy):
    def __init__(self, max_attempts: int, dlq_suffix: str = ".dlq"):
        self.max_attempts = max_attempts
        self.dlq_suffix = dlq_suffix

    def delays(self) -> list[int]:
        delays = [1, 2]
        while len(delays) < self.max_attempts:
            delays.append(delays[-1] + delays[-2])
        return delays[: self.max_attempts]
