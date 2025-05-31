from typing import Any


class MalformedMessageException(Exception):
    @staticmethod
    def missing_message_type_header(topic: str, msg: Any) -> Exception:
        return MalformedMessageException(f"Missing message type header on {topic} for message {msg}")


class MissingMessageTypeException(Exception):
    @staticmethod
    def missing_message_type_header(topic: str, msg: Any) -> Exception:
        return MissingMessageTypeException(f"Missing registered message type on {topic} for message {msg}")


class MissingHandlerException(Exception):
    def __init__(self, topic: str, msg_type_name: str):
        super().__init__(f"Missing handler for {msg_type_name} on topic {topic}")


class UnknownMessageTypeException(Exception):
    def __init__(self, topic: str, msg_type_name: str):
        super().__init__(f"Unknown message type {msg_type_name} on topic {topic}")


class IncompatibleMessageTypeException(Exception):
    def __init__(self, topic: str, expected: Any | None, actual: Any | None):
        super().__init__(f"Incompatible message type on topic {topic}: expected {expected}, got {actual}")
