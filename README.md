# Kavari
### Easy, automated Kafka publish/subscribe with strong typing

---

This tool aims to make Kafka usage extremely simple and safe,  
leveraging best practices and the power of [`confluent_kafka`](https://github.com/confluentinc/confluent-kafka-python).

While using weak typing in Python may be quick and fun for rapid development, exposing any data outside your app requires a predictable and structured format. Providing a stable contract for external consumers ensures maintainability and safety.

Additionally, since modern applications are usually hosted in the cloud, there’s often a need to handle scenarios like host migration or failover. For instance:

- Kafka may become temporarily unavailable  
- Consumers may shut down in the middle of message processing  
- Partition rebalancing may occur  

These situations typically require a lot of extra code in a production-ready setup.

This small library handles those concerns for you — while also simplifying the developer experience.

## 📨 Publishing messages

Create a message type that defines the payload (our strongly typed message format):

```python
class TestKafkaMessage(KafkaMessage):
    topic = "test_topic"

    def __init__(self, payload: str):
        super().__init__()
        self.payload: str = payload

    def get_partition_key(self) -> str:
        """
        The message key in the produce method is important for determining how messages are
        distributed across partitions in a Kafka topic. By using a key, all messages with the same
        key will go to the same partition and kafka will ensure the order of them. Think about it in 
        terms of aggregate ID 

        :return: str
        """
        return "1"
```

Then publish it to the topic simply by calling:

```python
msg = TestKafkaMessage("test_message")
kafka_manager.publish_message(msg, lambda msg, ex: print("Message published"))
```

## 📥 Consuming messages

Define the handler class:

```python
@kafka_message_handler(message_cls=TestKafkaMessage)
class TestKafkaMessageConsumer(KafkaMessageConsumer):

    def __init__(self):
        self.received_message: str | None = None

    def handle(self, message_data: str) -> None:
        self.received_message = message_data
```

Once the consumer is available via a provider (e.g. a DI container), each message will be handled **in a separate thread**,  
which keeps Kafka background processing isolated from other parts of your app (e.g. REST API).

## ⚙️ Configuration

Install using:

- **pip**: `pip install kavari`  
- **Poetry**: `poetry add kavari`

Create a `kafka_manager` (example below uses a DI container, but Kavari works without one as well):

```python
from kavari import kavari_create, FibonacciRetryPolicy, KafkaManager

class Container(DeclarativeContainer):
    kafka_manager: Singleton[KafkaManager] = Singleton(
        lambda: kavari_create(
            bootstrap_servers="bootstrap_location:2973",
            group_id="unique_group_identifier",
            publishing_retry_policy=FibonacciRetryPolicy(max_attempts=10),
            logger=logger,
            auto_commit=False,
            auto_offset_reset="earliest"
        )
    )
```

### ✅ Configuration steps

1. **Configure the message consumer provider:**

```python
def consumer_provider(key: typing.Any) -> kavari.KafkaMessageConsumer:
    if key == MyFirstMessageConsumer.__class__:
        return MyFirstMessageConsumer()
```

2. **Start the consumer loop** at application startup.  
3. **Stop the consumer loop** during application shutdown.

### Example (FastAPI + Dependency Injector)

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    container.logger().info("Starting background jobs...")
    container.kafka_manager().set_consumer_provider(container.resolve)
    container.kafka_manager().start_consumer_loop()
    yield
    container.logger().info("Stopping background jobs...")
    container.kafka_manager().stop_consumer_loop()
```

---

## 🔍 Want to contribute?

Contributions, issues and feature requests are welcome!  
Feel free to check [issues page](https://github.com/sdudziak/kavari/issues).

If you love this project, leave a ⭐ on [GitHub](https://github.com/sdudziak/kavari)!

---

## 📃 License

This project is licensed under the [Apache 2.0 License](https://opensource.org/licenses/Apache-2.0).