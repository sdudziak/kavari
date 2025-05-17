from typing import Generic, Type, TypeVar

from .kafka_message import KafkaMessage

T = TypeVar("T", bound=KafkaMessage)


class KafkaMessageConsumer(Generic[T]):
    message_cls: Type[T] = None

    def handle(self, message_data: T) -> None:
        raise NotImplementedError
