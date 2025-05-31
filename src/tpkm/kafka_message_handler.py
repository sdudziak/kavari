from typing import Type, get_type_hints

from .kafka_message import KafkaMessage
from .kafka_message_consumer import KafkaMessageConsumer
from .module_globals import _message_type_registry


def kafka_message_handler(message_cls: Type[KafkaMessage]):
    """
    Register handler from KafkaMessage[T] inherited class,
    ensuring that method`.handle(self, message_data: T)` uses correct T type.
    """

    def wrapper(handler_cls: Type[KafkaMessageConsumer]):
        if not issubclass(handler_cls, KafkaMessageConsumer):
            raise TypeError("Handler must inherit from KafkaMessageConsumer")

        topic = message_cls.topic
        if not topic:
            raise ValueError(f"{message_cls.__name__} must define static field 'topic'")

        # check type from `handle(self, message_data: T)` T parameter
        handle_method = getattr(handler_cls, "handle", None)
        if handle_method is None:
            raise ValueError(f"{handler_cls.__name__} must define a 'handle' method")

        hints = get_type_hints(handle_method)
        if "message_data" not in hints:
            raise ValueError(
                f"{handler_cls.__name__}.handle must define argument 'message_data' with type annotation"
            )

        expected_type = message_cls.__annotations__.get("payload")
        actual_type = hints["message_data"]
        if actual_type != expected_type:
            raise TypeError(
                f"{handler_cls.__name__}.handle expects '{actual_type.__name__}', "
                f"but KafkaMessage carries '{expected_type.__name__}'"
            )

        _message_type_registry.register_handler_for_topic(topic, message_cls, handler_cls)
        return handler_cls

    return wrapper
