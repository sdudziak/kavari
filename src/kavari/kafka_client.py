import time
from logging import Logger
from typing import Callable

from confluent_kafka import Message, Producer

from .kafka_message import KafkaMessage
from .retry_policy import RetryPolicy


class KafkaClient:
    def __init__(self, producer: Producer, retry_policy: RetryPolicy, logger: Logger, dlq_suffix: str = ".dlq"):
        self.logger: Logger = logger
        self.dlq_suffix: str = dlq_suffix
        self.producer: Producer = producer
        self.retry_policy: RetryPolicy = retry_policy

    def send(
        self,
        message: KafkaMessage,
        on_complete: Callable[[Message, Exception | None], None],
    ):
        partition = message.get_partition_key()
        value = message.to_json()
        topic = message.topic
        msg_type = message.__class__.__name__

        def delivery_callback(err, msg):
            if err:
                self._handle_retry(message, on_complete, err)
            else:
                on_complete(msg, None)

        self.producer.produce(
            topic=topic,
            value=value,
            partition=partition,
            on_delivery=delivery_callback,
            headers={"msg_type": msg_type},
        )
        self.producer.flush()

    def _handle_retry(
        self,
        message: KafkaMessage,
        on_complete: Callable[[Message, Exception | None], None],
        original_error: Exception,
    ):
        delays = self.retry_policy.delays()
        key = message.get_partition_key()
        value = message.to_json()

        for delay in delays:
            time.sleep(delay)
            try:
                self.producer.produce(
                    topic=message.topic,
                    key=key,
                    value=value,
                    callback=lambda err, msg: (on_complete(msg, None) if not err else None),
                )
                self.producer.flush()
                return
            except Exception as e:
                self.logger.warning(f"Unable to send message {message} because of {e}")
                continue

        dlq_topic = f"{message.topic}{self.dlq_suffix}"
        self.producer.produce(
            topic=dlq_topic,
            key=key,
            value=value,
            callback=lambda err, msg: on_complete(msg, err or original_error),
        )
        self.producer.flush()
