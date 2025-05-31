from typing import Generic, Type, TypeVar

from .kafka_message import KafkaMessage

T = TypeVar("T", bound=KafkaMessage)


class KafkaMessageConsumer(Generic[T]):
    def handle(self, message_data: T) -> None:
        raise NotImplementedError
