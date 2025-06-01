import json
import sys
import threading
import time
from dataclasses import asdict, dataclass
from logging import Logger
from unittest import TestCase
from unittest.mock import MagicMock

from confluent_kafka import Consumer, KafkaError, Message

from kavari import FibonacciRetryPolicy, KafkaMessage
from kavari.kafka_consumer_manager import KafkaConsumerManager
from kavari.kafka_message_consumer import KafkaMessageConsumer
from kavari.kafka_message_handler import kafka_message_handler
from kavari.message_type_registry import _message_type_registry


class SampleKafkaMessage(KafkaMessage):
    topic = "test_topic"
    payload: str

    def get_partition_key(self) -> str:
        return "1"

    def __init__(self, payload: str, topic: str = None, _error: KafkaError | None = None):
        super().__init__()
        self.payload = payload


@kafka_message_handler(message_cls=SampleKafkaMessage)
class SampleKafkaMessageConsumer(KafkaMessageConsumer):

    def __init__(self):
        self.received_message: str | None = None
        self.done = threading.Event()

    def handle(self, message_data: str) -> None:
        self.received_message = message_data
        self.done.set()


class TestKafkaConsumerManager(TestCase):

    def setUp(self):
        self.consumer: MagicMock[Consumer] = MagicMock(spec=Consumer)
        self.sut: KafkaConsumerManager = KafkaConsumerManager(self.consumer, FibonacciRetryPolicy(1), MagicMock(spec=Logger))
        self.test_kafka_message_consumer: SampleKafkaMessageConsumer = SampleKafkaMessageConsumer()
        self.sut.set_consumer_provider(lambda key: self.test_kafka_message_consumer)

        _message_type_registry.register_handler_for_topic(SampleKafkaMessage.topic, SampleKafkaMessage, SampleKafkaMessageConsumer)

    def test_will_consume_message_from_specified_topic(self):
        # given
        kafka_msg: MagicMock[Message] = MagicMock(spec=Message)
        msg = SampleKafkaMessage("Say hello!")
        serialized_msg = json.dumps(asdict(msg)).encode("utf-8")
        kafka_msg.value.return_value = serialized_msg
        kafka_msg.headers.return_value = {"msg_type": msg.__class__.__name__}
        kafka_msg.error.return_value = None
        kafka_msg.topic.return_value = msg.topic
        self.consumer.poll.return_value = kafka_msg

        # when
        self.sut.start()
        self.test_kafka_message_consumer.done.wait(timeout=0.2)
        self.sut.stop()

        self.assertEqual(msg.payload, self.test_kafka_message_consumer.received_message)

    def test_should_continue_when_poll_returns_none(self):
        self.consumer.poll.return_value = None
        self.sut.start()
        self.test_kafka_message_consumer.done.wait(timeout=0.2)
        self.sut.stop()
        self.assertIsNone(self.test_kafka_message_consumer.received_message)

    def test_should_ignore_poll_with_error(self):
        msg = MagicMock(spec=Message)
        error = MagicMock()
        error.code.return_value = KafkaError.UNKNOWN
        msg.error.return_value = error
        self.consumer.poll.return_value = msg

        self.sut.start()
        self.test_kafka_message_consumer.done.wait(timeout=0.2)
        self.sut.stop()

        self.assertIsNone(self.test_kafka_message_consumer.received_message)

    def test_should_log_when_no_handler_registered(self):
        msg = MagicMock(spec=Message)
        msg.error.return_value = None
        msg.topic.return_value = "unhandled_topic"
        msg.value.return_value = b"{}"
        self.consumer.poll.return_value = msg

        self.sut.start()
        self.test_kafka_message_consumer.done.wait(timeout=0.2)
        self.sut.stop()

        self.assertIsNone(self.test_kafka_message_consumer.received_message)

    def test_should_not_commit_on_handler_exception(self):
        class FailingHandler(KafkaMessageConsumer):
            def handle(self, payload):
                raise RuntimeError("fail")

        _message_type_registry.purge()
        _message_type_registry.register_handler_for_topic(SampleKafkaMessage.topic, SampleKafkaMessage, FailingHandler)
        self.sut.set_consumer_provider(lambda cls: FailingHandler())

        msg = SampleKafkaMessage("fail")
        kafka_msg = MagicMock(spec=Message)
        kafka_msg.headers.return_value = {"msg_type": SampleKafkaMessage.__name__}
        kafka_msg.topic.return_value = msg.topic
        kafka_msg.value.return_value = json.dumps(asdict(msg)).encode()
        kafka_msg.error.return_value = None
        self.consumer.poll.return_value = kafka_msg

        self.sut.start()
        self.test_kafka_message_consumer.done.wait(timeout=0.2)
        self.sut.stop()

        self.consumer.commit.assert_not_called()

    def tearDown(self):
        # clean up
        _message_type_registry.purge()
        self.consumer.reset_mock()
