import json
import threading
import time
from typing import Any, Callable, List

from confluent_kafka import Consumer, KafkaError, Message
from dacite import from_dict

from .kafka_message import KafkaMessage
from .kafka_message_consumer import KafkaMessageConsumer
from .module_globals import _registered_consumers


class KafkaConsumerManager:
    def __init__(self, consumer: Consumer):
        self.consumer_provider: Callable[[Any], KafkaMessageConsumer] | None = None
        self.threadHandle: threading.Thread | None = None
        self.consumer: Consumer = consumer
        self.topics: List[str] = list(_registered_consumers.keys())
        self.stop_event = threading.Event()
        self.consumer.subscribe(self.topics)

    @staticmethod
    def _deserialize_message(
        raw_value: bytes, message_cls: type[KafkaMessage]
    ) -> KafkaMessage:
        payload_dict = json.loads(raw_value.decode("utf-8"))
        return from_dict(data_class=message_cls, data=payload_dict)

    def set_consumer_provider(
        self, consumer_provider: Callable[[Any], KafkaMessageConsumer]
    ):
        self.consumer_provider = consumer_provider

    def start(self):
        def run():
            print(f"[Kafka] Subscribed to topics: {self.topics}")
            while not self.stop_event.is_set():
                msg: Message = self.consumer.poll(1.0)
                if msg is None:
                    time.sleep(
                        1
                    )  # sleep if the queue is empty to not overkill performance with nasty query rate
                    continue
                if msg.error():
                    if msg.error().code() != KafkaError._PARTITION_EOF:
                        print(f"[Kafka Error] {msg.error()}")
                    continue

                topic = msg.topic()
                handler_cls: KafkaMessageConsumer | None = _registered_consumers.get(
                    topic
                )
                if handler_cls is None:
                    print(f"[Kafka] No handler registered for topic: {topic}")
                    # sleep if the queue is empty to not overkill performance with nasty query rate
                    time.sleep(1)
                    continue

                try:
                    message_cls = handler_cls.message_cls
                    kafka_message: KafkaMessage = self._deserialize_message(
                        msg.value(), message_cls
                    )

                    # Resolve handler from  DI container
                    handler = self.consumer_provider(handler_cls)
                    handler.handle(kafka_message.payload)

                    # ACK after success
                    self.consumer.commit(msg)
                except Exception as e:
                    print(f"[Kafka] Failed to process message on topic {topic}: {e}")

        self.stop_event.clear()
        self.threadHandle = threading.Thread(target=run, daemon=True)
        self.threadHandle.start()

    def stop(self) -> None:
        self.stop_event.set()
        self.threadHandle.join()
        print("[Kafka] Consumer thread stopped.")
