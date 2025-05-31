import json
import threading
import time
from logging import Logger
from typing import Any, Callable, List, Type

from confluent_kafka import Consumer, KafkaError, Message
from dacite import from_dict

from .exceptions import MalformedMessageException, MissingHandlerException, UnknownMessageTypeException
from .kafka_message import KafkaMessage
from .kafka_message_consumer import KafkaMessageConsumer
from .message_type_registry import _message_type_registry
from .retry_policy import RetryPolicy


class KafkaConsumerManager:
    def __init__(self, consumer: Consumer, retry_policy: RetryPolicy, logger: Logger, relaxed=True):
        self.logger: Logger = logger
        self.relaxed: bool = relaxed
        self.retry_policy: RetryPolicy = retry_policy
        self.consumer_provider: Callable[[Any], KafkaMessageConsumer] | None = None
        self.threadHandle: threading.Thread | None = None
        self.consumer: Consumer = consumer
        self.topics: List[str] = _message_type_registry.get_topics()
        self.stop_event = threading.Event()
        self.consumer.subscribe(self.topics)

    @staticmethod
    def _deserialize_message(raw_value: bytes, message_cls: type[KafkaMessage]) -> KafkaMessage:
        payload_dict = json.loads(raw_value.decode("utf-8"))
        return from_dict(data_class=message_cls, data=payload_dict)

    def set_consumer_provider(self, consumer_provider: Callable[[Any], KafkaMessageConsumer]):
        self.consumer_provider = consumer_provider

    def start(self):
        def run():
            self.consumer.subscribe(self.topics)
            self.logger.info(f"[tpkm] Subscribed to kafka topics: {self.topics}")
            while not self.stop_event.is_set():
                msg: Message = self.consumer.poll(1.0)
                # sleep if the queue is empty to not overkill performance with nasty query rate
                if msg is None:
                    time.sleep(1)
                    continue
                if msg.error():
                    if msg.error().code() != KafkaError._PARTITION_EOF:
                        self.logger.error(f"Kafka Error: {msg.error()}")
                    continue

                topic = msg.topic()
                # missing msg_type which means this topic is somehow malformed.
                # if the consumer is in the relaxed mode, it will continue to the
                # message, otherwise it will raise the exception
                headers = msg.headers()
                if not headers["msg_type"] or headers["msg_type"] is None:
                    if self.relaxed:
                        self.logger.warning(f"Missing message type for topic ${topic} in message ${msg}")
                        self.consumer.commit(msg)
                        continue
                    raise MalformedMessageException.missing_message_type_header(topic, msg)

                msg_type = _message_type_registry.get_message_type_from_name(topic, headers["msg_type"])
                if msg_type is None:
                    if self.relaxed:
                        self.logger.warning(f"Missing registered message type for topic ${topic} in message ${msg}")
                        self.consumer.commit(msg)
                        continue
                    raise UnknownMessageTypeException(topic, headers["msg_type"])

                handler_cls_list: List[Type[KafkaMessageConsumer]] | None = _message_type_registry.get_handlers(topic, msg_type)

                if not handler_cls_list or handler_cls_list is None:
                    self.logger.warning(f"Kafka: No handler registered for topic: {topic}")
                    continue

                handlers_count = len(handler_cls_list)
                if handlers_count == 0:
                    if self.relaxed:
                        self.logger.info(f"Kafka: No handler registered for topic: {topic}. Proceeding to the next message")
                        self.consumer.commit(msg)
                        continue
                    raise MissingHandlerException(topic, headers["msg_type"])

                for handler_cls in handler_cls_list:
                    if handler_cls is None:
                        self.logger.warning(f"Kafka: Empty handler registered for topic: {topic}")
                        continue

                    try:
                        kafka_message: KafkaMessage = self._deserialize_message(msg.value(), msg_type)
                    except Exception as e:
                        self.logger.error(f"Kafka: Unable to deserialize message: {msg.value()}")
                        raise e

                    try:
                        # Resolve handler from  DI container
                        assert self.consumer_provider is not None  # nosec B101
                        handler = self.consumer_provider(handler_cls)
                        handler.handle(kafka_message.payload)

                        # ACK after success
                        self.consumer.commit(msg)
                    except Exception as e:
                        self.logger.error(f"Kafka: Failed to process message on topic {topic}: {e}")

        self.stop_event.clear()
        self.threadHandle = threading.Thread(target=run, daemon=True)
        self.threadHandle.start()

    def stop(self) -> None:
        self.stop_event.set()
        self.consumer.unsubscribe()
        assert self.threadHandle is not None  # nosec B101
        self.threadHandle.join()
        self.logger.info("Kafka: Consumer thread stopped.")
