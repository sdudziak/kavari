import json
from typing import Any, Type

from dacite import from_dict

from .kafka_message import KafkaMessage


class KafkaMessageDeserializer:
    def deserialize(self, raw_value: bytes, message_cls: Type[KafkaMessage]) -> Any | None:
        payload_type: Type | None = message_cls.__annotations__.get("payload", None)  # Get expected payload type

        # Check if the payload type is a primitive type
        if payload_type in {int, float, bool, bytes}:
            return payload_type(raw_value)
        if payload_type is str:
            return raw_value.decode("utf-8")  # strings

        # Otherwise, deserialize as JSON
        payload_dict = json.loads(raw_value.decode("utf-8"))
        return from_dict(data_class=payload_type, data=payload_dict)  # type: ignore[arg-type]
