import socket
from logging import Logger

from confluent_kafka import Consumer, Producer

from .kafka_client import KafkaClient
from .kafka_consumer_manager import KafkaConsumerManager
from .kafka_manager import KafkaManager
from .retry_policy import RetryPolicy


def kavari_create(
    bootstrap_servers: str,
    group_id: str,
    delivery_retry_policy: RetryPolicy,
    publishing_retry_policy: RetryPolicy,
    logger: Logger,
    auto_commit: bool = False,
    auto_offset_reset: str = "earliest",
    acks: str = "1",  # Options: "0", "1", "all"
):
    return KafkaManager(
        kafka_client=KafkaClient(
            Producer(
                {
                    "bootstrap.servers": bootstrap_servers,
                    "client.id": socket.gethostname(),
                    "acks": acks,
                    "message.timeout.ms": 30000,  # 30 seconds timeout for message delivery
                    "queue.buffering.max.messages": 100000,  # Maximum number of messages allowed in the producer queue
                }
            ),
            publishing_retry_policy,
            logger,
            dlq_suffix=".dlq",
        ),
        kafka_consumer=KafkaConsumerManager(
            Consumer(
                {
                    "bootstrap.servers": bootstrap_servers,
                    "group.id": group_id,
                    "enable.auto.commit": auto_commit,
                    "auto.offset.reset": auto_offset_reset,
                }
            ),
            relaxed=True,
            retry_policy=publishing_retry_policy,
            logger=logger,
        ),
        logger=logger,
    )
