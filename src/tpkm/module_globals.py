from typing import Dict, Type

from .kafka_message_consumer import KafkaMessageConsumer

# === registry of topics linked to the consumers ===
_registered_consumers: Dict[str, Type[KafkaMessageConsumer]] = {}
