import time
from logging import Logger
from typing import Callable, Any

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
        on_complete: Callable[[Message, Any | str | Exception | None], None],
    ):
        value = message.to_json()
        topic = message.topic
        msg_type = message.__class__.__name__
        retry_delays = self.retry_policy.delays()
        delivery_success = False

        def delivery_callback(err, msg):
            nonlocal delivery_success
            if err:
                self.logger.error(f"[kavari] Producer error: {err}")
            else:
                self.logger.info(f"[kavari] Successfully delivered message to {topic}")
                delivery_success = True
                on_complete(msg, None)

        self.logger.info(f"[kavari] Attempting to produce message to topic: {topic}")
        self.logger.debug(f"[kavari] Message value: {value}")

        original_error: str | Exception | None = None
        for retry_delay in retry_delays:
            try:
                self.producer.produce(
                    topic=topic,
                    value=value,
                    key=message.get_partition_key(),
                    on_delivery=delivery_callback,
                    headers={"msg_type": msg_type},
                )

                # Poll in a loop with a shorter timeout to check delivery status
                poll_start = time.time()
                while time.time() - poll_start < 30:  # 30 second total timeout
                    self.producer.poll(timeout=1.0)
                    if delivery_success:
                        self.logger.info("[kavari] Message delivered successfully")
                        return
                    time.sleep(0.1)

                if delivery_success:
                    self.logger.info("[kavari] Successfully flushed all messages")
                    return
                else:
                    original_error = "[kavari] Message delivery timeout"
                    self.logger.error(original_error)
                    time.sleep(retry_delay)
                    continue  # retry attempt
            except Exception as e:
                self.logger.warning(f"Unable to send message {message} because of {e}")
                original_error = e
                time.sleep(retry_delay)
                continue

        self.logger.error(f"[kavari] All retry attempts failed for topic {topic}. Moving to DLQ.")
        dlq_topic = f"{message.topic}{self.dlq_suffix}"
        self.producer.produce(
            topic=dlq_topic,
            value=value,
            key=message.get_partition_key(),
            headers={"msg_type": msg_type, "original_error": str(original_error)},
            on_delivery=lambda err, msg: on_complete(msg, err or original_error),
        )
        self.producer.flush()

    def stop(self):
        self.logger.info("[kavari] Flushing produced messages, with timeout 30s")
        self.producer.flush(timeout=30)
