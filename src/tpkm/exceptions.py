
class MalformedMessageException(Exception):
    @staticmethod
    def missing_message_type_header(topic: str, msg: any) -> Exception:
        return MalformedMessageException(f"Missing message type header on ${topic} for message ${msg}")

class MissingMessageTypeException(Exception):
    @staticmethod
    def missing_message_type_header(topic: str, msg: any) -> Exception:
        return MissingMessageTypeException(f"Missing registered message type on ${topic} for message ${msg}")

class MissingHandlerException(Exception):
    def __init__(self, topic: str, msg_type_name: str):
        super().__init__(f"Missing handler for ${msg_type_name} on topic ${topic}")

class UnknownMessageTypeException(Exception):
    def __init__(self, topic: str, msg_type_name: str):
        super().__init__(f"Unknown message type ${msg_type_name} on topic ${topic}")