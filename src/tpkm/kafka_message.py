import json
from abc import ABC, abstractmethod
from dataclasses import dataclass

from confluent_kafka import KafkaError


@dataclass
class KafkaMessage(ABC):
    topic: str
    payload: object  # to be precised in the inherited class
    _error: KafkaError | None

    def __init__(self) -> None:
        self._error = None

    @abstractmethod
    def get_partition_key(self) -> str:
        """Must return a string key used for Kafka partitioning."""
        pass

    def to_json(self) -> str:
        """Serialize the value payload to JSON."""
        return json.dumps(self.payload.__dict__)

    def error(self) -> KafkaError | object | None:
        return self._error

    def set_error(self, error: KafkaError | None) -> None:
        self._error = error

    def to_bytes(self) -> bytes:
        if isinstance(self, (str, int, float, bool, type(None))):
            return json.dumps(self).encode("utf-8")
        elif hasattr(self, "to_dict"):
            return json.dumps(self.to_dict()).encode("utf-8")
        elif hasattr(self, "model_dump"):  # Pydantic v2
            return json.dumps(self.model_dump()).encode("utf-8")
        else:
            raise TypeError(f"Cannot serialize object of type {type(self)}")
