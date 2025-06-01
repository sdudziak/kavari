from logging import Logger

from confluent_kafka import Consumer, Producer

from .kafka_client import KafkaClient
from .kafka_consumer_manager import KafkaConsumerManager
from .kafka_manager import KafkaManager
from .retry_policy import RetryPolicy


def kavari_create(
    bootstrap_servers: str,
    group_id: str,
    delivery_retry_policy: RetryPolicy,  # noqa: Vulture - this will be implemented later
    publishing_retry_policy: RetryPolicy,
    logger: Logger,
    auto_commit: bool = False,
    auto_offset_reset: str = "earliest",
):
    return KafkaManager(
        kafka_client=KafkaClient(Producer({"bootstrap.servers": bootstrap_servers}), publishing_retry_policy, logger, dlq_suffix=".dlq"),
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
