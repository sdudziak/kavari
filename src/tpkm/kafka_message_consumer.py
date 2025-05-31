from typing import Generic, TypeVar

from .kafka_message import KafkaMessage

T = TypeVar("T", bound=KafkaMessage)


class KafkaMessageConsumer(Generic[T]):
    def handle(self, message_data: T) -> None:  # noqa: Vulture
        raise NotImplementedError
