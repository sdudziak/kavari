from logging import Logger
from typing import Any, Callable

from confluent_kafka import Message

from .kafka_client import KafkaClient
from .kafka_consumer_manager import KafkaConsumerManager
from .kafka_message import KafkaMessage
from .kafka_message_consumer import KafkaMessageConsumer


class KafkaManager:

    def __init__(
        self,
        kafka_client: KafkaClient,
        kafka_consumer: KafkaConsumerManager,
        logger: Logger,
    ):
        self.kafka_client = kafka_client
        self.kafka_msg_consumer = kafka_consumer
        self.logger = logger

    def set_consumer_provider(self, consumer_provider: Callable[[Any], KafkaMessageConsumer]):
        self.kafka_msg_consumer.set_consumer_provider(consumer_provider)

    def publish_message(
        self,
        message: KafkaMessage,
        on_complete: Callable[[Message, Exception | None], None] = lambda m, e: None,  # noqa: Vulture
    ) -> None:
        return self.kafka_client.send(message, on_complete)

    def start_consumer_loop(self):
        self.logger.info("Starting consumer loop")
        self.kafka_msg_consumer.start()

    def stop_consumer_loop(self):
        self.logger.info("Stopping consumer loop")
        self.kafka_msg_consumer.stop()
