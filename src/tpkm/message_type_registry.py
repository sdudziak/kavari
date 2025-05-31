import importlib
from typing import Any, Dict, List, Type

from .kafka_message import KafkaMessage
from .kafka_message_consumer import KafkaMessageConsumer


class MessageTypeRegistryEntry:
    msg_type_path: str | None = None
    msg_type: type | None = None
    _consumers: List[Type[KafkaMessageConsumer]] = []

    def __init__(self, msg_type: Type[KafkaMessage], consumer_type: Type[KafkaMessageConsumer]):
        self.msg_type_path = f"{msg_type.__module__}.{msg_type.__name__}"
        self.msg_type = self.__load_msg_type(self.msg_type_path)
        self._consumers = [consumer_type]

    def register_consumer(self, consumer: Type[KafkaMessageConsumer]):
        if consumer not in self._consumers:
            self._consumers.append(consumer)

    def get_consumers(self) -> List[Type[KafkaMessageConsumer]]:
        return self._consumers

    def purge(self):
        self.msg_type = None
        self._consumers.clear()

    @staticmethod
    def __load_msg_type(msg_type_path: str) -> type:
        module_path, class_name = msg_type_path.rsplit(".", 1)
        module = importlib.import_module(module_path)  # nosemgrep: non-literal-import - loading only child classes of KafkaMessage
        msg_type: type = getattr(module, class_name)
        if not issubclass(msg_type, KafkaMessage):
            raise TypeError(f"{msg_type} is not a subclass of KafkaMessage")
        return msg_type


class MessageTypeRegistry:
    _registry: Dict[str, MessageTypeRegistryEntry] = {}

    def register_message_handler(self, msg_type: Type[KafkaMessage], consumer: Type[KafkaMessageConsumer]):
        msg_type_name = msg_type.__name__
        if self._registry.get(msg_type_name) is None:
            self._registry[msg_type_name] = MessageTypeRegistryEntry(msg_type, consumer)
        else:
            self._registry[msg_type_name].register_consumer(consumer)
        pass

    def get_message_type_from_name(self, msg_type_name):
        if self._registry.get(msg_type_name) is None:
            return None
        return self._registry[msg_type_name].msg_type

    def get_handlers_for_msg_type_name(self, msg_type_name) -> List[Type[KafkaMessageConsumer]] | None:
        if self._registry.get(msg_type_name) is None:
            return None
        return self._registry[msg_type_name].get_consumers()

    def clear(self) -> None:
        for v in self._registry.values():
            v.purge()
        self._registry.clear()


class TopicMessageTypeRegistry:
    _registry: Dict[str, MessageTypeRegistry] = {}

    def register_handler_for_topic(self, topic, message_cls: Type[KafkaMessage], handler_cls: Type[KafkaMessageConsumer]):
        if self._registry.get(topic) is None:
            self._registry[topic] = MessageTypeRegistry()
        self._registry[topic].register_message_handler(message_cls, handler_cls)

    def get_topics(self) -> List[str]:
        return list(self._registry.keys())

    def get_message_type_from_name(self, topic: str, msg_type_name: str) -> Type[KafkaMessage] | None:
        if self._registry.get(topic) is None:
            return None
        return self._registry[topic].get_message_type_from_name(msg_type_name)

    def get_handlers(self, topic, msg_type) -> List[Type[KafkaMessageConsumer[Any]]] | None:
        if self._registry.get(topic) is None:
            return None
        msg_type_name = msg_type.__name__
        return self._registry[topic].get_handlers_for_msg_type_name(msg_type_name)

    def purge(self):
        for v in self._registry.values():
            v.clear()
        self._registry.clear()


_message_type_registry: TopicMessageTypeRegistry = TopicMessageTypeRegistry()
