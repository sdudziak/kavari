import json
from dataclasses import dataclass
from typing import Any

import pytest

from kavari.kafka_message import KafkaMessage
from kavari.kafka_message_deserializer import KafkaMessageDeserializer


# --- Test message classes ---
class BaseExampleKafkaMessage(KafkaMessage):
    topic: str = "test_topic"

    def get_partition_key(self) -> str:
        return "1"


# Primitive payload message classes
class IntPayloadMessage(BaseExampleKafkaMessage):
    payload: int

    def __init__(self, payload: int) -> None:
        super().__init__()
        self.payload = payload


class StrPayloadMessage(BaseExampleKafkaMessage):
    payload: str

    def __init__(self, payload: str) -> None:
        super().__init__()
        self.payload = payload


# Complex payload message class
@dataclass()
class ComplexPayload:
    field1: str
    field2: int


class ComplexPayloadMessage(BaseExampleKafkaMessage):
    payload: ComplexPayload

    def __init__(self, payload: ComplexPayload) -> None:
        super().__init__()
        self.payload = payload


# --- Test cases ---
deserializer = KafkaMessageDeserializer()


def test_deserialize_int_payload():
    # The raw value should be a JSON object with a primitive payload
    raw = IntPayloadMessage(123).to_json().encode("utf-8")
    msg = deserializer.deserialize(raw, IntPayloadMessage)
    assert isinstance(msg, int)
    assert msg == 123


def test_deserialize_str_payload():
    raw = StrPayloadMessage("hello").to_json().encode("utf-8")
    msg = deserializer.deserialize(raw, StrPayloadMessage)
    assert isinstance(msg, str)
    assert msg == "hello"


def test_deserialize_complex_payload():
    raw = ComplexPayloadMessage(ComplexPayload("abc", 42)).to_json().encode("utf-8")
    msg = deserializer.deserialize(raw, ComplexPayloadMessage)
    assert isinstance(msg, ComplexPayload)
    assert msg.field1 == "abc"
    assert msg.field2 == 42


def test_deserialize_invalid_json():
    # Not a valid JSON
    raw = b"not a json"
    with pytest.raises(Exception):
        deserializer.deserialize(raw, IntPayloadMessage)


def test_deserialize_empty_payload():
    raw = b""
    with pytest.raises(Exception):
        deserializer.deserialize(raw, IntPayloadMessage)


# Edge case: extra fields in payload (should be ignored by dataclasses)
def test_deserialize_complex_payload_extra_fields():
    complex_payload = ComplexPayload("abc", 42)
    complex_payload.ignored = True
    raw = ComplexPayloadMessage(complex_payload).to_json().encode("utf-8")
    msg = deserializer.deserialize(raw, ComplexPayloadMessage)
    assert isinstance(msg, ComplexPayload)
    assert msg.field1 == "abc"
    assert msg.field2 == 42
    assert not hasattr(msg, "ignored")
