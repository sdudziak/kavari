from logging import Logger
from typing import Any, Callable
from unittest import TestCase
from unittest.mock import MagicMock

from kavari.kafka_client import KafkaClient
from kavari.kafka_consumer_manager import KafkaConsumerManager
from kavari.kafka_manager import KafkaManager
from kavari.kafka_message import KafkaMessage
from kavari.kafka_message_consumer import KafkaMessageConsumer


class Flag:
    def __init__(self):
        self.value = False


class SampleKafkaMessage(KafkaMessage):
    topic = "test_topic"

    def __init__(self, payload: str):
        super().__init__()
        self.payload: str = payload

    def get_partition_key(self) -> str:
        return "1"


class TestKafkaManager(TestCase):

    def setUp(self):
        self.kafka_client = MagicMock(spec=KafkaClient)
        self.kafka_consumer_manager = MagicMock(spec=KafkaConsumerManager)
        self.logger = MagicMock(spec=Logger)
        self.sut = KafkaManager(self.kafka_client, self.kafka_consumer_manager, self.logger)

    def tearDown(self):
        self.kafka_client.reset_mock()
        self.kafka_consumer_manager.reset_mock()
        self.logger.reset_mock()

    def test_sending_message(self):
        msg: SampleKafkaMessage = SampleKafkaMessage("test_message")
        is_completed = Flag()
        dummy_callback = lambda _, __: setattr(is_completed, "value", True)
        self.sut.publish_message(msg, dummy_callback)

        self.kafka_client.send.assert_called_once_with(msg, dummy_callback)

    def test_starting_consumer_loop_is_starting_the_consumer_manager(self):
        # when
        self.sut.start_consumer_loop()
        # then
        self.kafka_consumer_manager.start.assert_called_once()

    def test_stop_consumer_loop_is_stopping_the_consumer_manager(self):
        # when
        self.sut.stop_consumer_loop()
        # then
        self.kafka_consumer_manager.stop.assert_called_once()

    def test_setting_kafka_consumer_provider_is_setting_the_consumer_provider_in_correct_place(
        self,
    ):
        # given
        dummy_consumer_provider: Callable[[Any], KafkaMessageConsumer | None] = lambda _: None
        # when
        self.sut.set_consumer_provider(dummy_consumer_provider)
        # then
        self.kafka_consumer_manager.set_consumer_provider.assert_called_once_with(dummy_consumer_provider)
