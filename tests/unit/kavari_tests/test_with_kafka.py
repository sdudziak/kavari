import json
import logging
import threading
import time
import unittest

import kavari


class Flag:
    def __init__(self):
        self.value = False


class SampleKafkaMessage2(kavari.KafkaMessage):
    topic: str = "test_topic"
    payload: int = 0

    def __init__(self, payload: int):
        super().__init__()
        self.payload: int = payload

    def get_partition_key(self) -> str:
        return "1"


@kavari.kafka_message_handler(message_cls=SampleKafkaMessage2)
class SampleKafkaMessageConsumer(kavari.KafkaMessageConsumer):

    sum: int = 0

    def __init__(self):
        self.done = threading.Event()

    def handle(self, message_data: int) -> None:
        self.sum += message_data
        self.done.set()


@unittest.skip("Disabled - use it only if you have kafka instantiated on localhost/docker")
class TestKafkaManagerWithKafka(unittest.TestCase):
    def setUp(self):
        self.sample_message_consumer = SampleKafkaMessageConsumer()
        self.kafka_manager = kavari.kavari_create(
            bootstrap_servers="localhost:9092",
            group_id="test_group",
            delivery_retry_policy=kavari.FibonacciRetryPolicy(3),
            publishing_retry_policy=kavari.FibonacciRetryPolicy(3),
            logger=logging.Logger("test_logger"),
            auto_commit=False,
            auto_offset_reset="earliest",
        )
        self.kafka_manager.set_consumer_provider(lambda x: self.sample_message_consumer)
        self.kafka_manager.start_consumer_loop()

    def tearDown(self):
        self.kafka_manager.stop_consumer_loop()

    def test_consumer_using_kafka(self):
        # publish
        for i in range(10):
            self.kafka_manager.publish_message(SampleKafkaMessage2(i))
        time.sleep(30)

        # check
        self.assertEqual(10, self.sample_message_consumer.sum)
