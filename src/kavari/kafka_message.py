import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Type

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
        """
        The message key in the produce method is important for determining how messages are
        distributed across partitions in a Kafka topic. By using a key, all messages with the same
        key will go to the same partition, which helps maintain the order of messages that are related.

        :return: str
        """
        pass

    def to_json(self) -> str:
        """Serialize the value payload to JSON."""
        payload_type: Type | None = self.__annotations__.get("payload", None)
        if payload_type in {int, float, str, bool, bytes}:
            return f"{self.payload}"
        else:
            return json.dumps(self.payload.__dict__)

    def error(self) -> KafkaError | object | None:
        return self._error

    def set_error(self, error: KafkaError | None) -> None:
        self._error = error
