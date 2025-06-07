Kavari
---
### Easy, automated Kafka publish/subscription with strong types

---
This tool is to make usage of kafka super easy and safe, 
utilizing best practices and power given by [`confluent_kafka`](https://github.com/confluentinc/confluent-kafka-python)

While it may be fast & fun to use weak types in Python for rapid development, that when it comes to expose any data outside the app, 
it is very reasonable to structure the message in predictable manner - providing stable contract of exposed data structure for external 
consumers.
Also, because modern applications usually are hosted in a cloud - there is a necessity to implement additional readiness for host 
migration/failover scenarios, when pod manager can move host from one physical place to another. That results with specific situations when:
* kafka might not achievable temporarily 
* consumers might be taken down in the middle of processing a message(s)
* rebalancing partitions

All of these adds a lot of code for the basic implementation for the final product.

This small library covers these, additionally providing some simplicity flavor on top.

## Publishing message

Create a message type, that defines the payload (our strong typed message format)
```python

class TestKafkaMessage(KafkaMessage):
    topic = "test_topic"

    def __init__(self, payload: str):
        super().__init__()
        self.payload: str = payload

    def get_partition_key(self) -> str:
        return "1"
```

And then publish it on the topic, just by calling:
```python
msg: TestKafkaMessage = TestKafkaMessage("test_message")
kafka_manager.publish_message(msg, lambda msg, ex:  print("Message published"))
```
Easy? I hope so! Now let's consume this message

## Consuming message

Define the handler class 
```python
@kafka_message_handler(message_cls=TestKafkaMessage)
class TestKafkaMessageConsumer(KafkaMessageConsumer):

    def __init__(self):
        self.received_message: str | None = None

    def handle(self, message_data: str) -> None:
        self.received_message = message_data
```

That's (almost) it! 
Once consumer become available via provider (any DI for example) each message is handled out of the box in **separated thread**, to isolate
background kafka messaging processing from other part of the application (e.g. REST API)

I hope you like the concept!

To achieve full power of this lib, you need to configure it

## Configuration

Install it via:   
* PIP: `pip install kavari`
* Poetry: `poetry add kavari`

Create a `kafka_manager` (example below is for a DI container, but you can use it without it)

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

There are 3 necessary steps to finish the configuration:
1. Configure message consumers provider:   
   Provider is a method that will deliver initialized instance of message consumer when specific key is given.   
   The example manual consumer provider will look like follows:   
   ```python
    def consumer_provider(key: typing.Any) -> kavari.KafkaMessageConsumer:
        if key == MyFirstMessageConsumer.__class__:
            return MyFirstMessageConsumer()
   ```
   This interface is prepared to be compatible with `dependency_injector.Container.resolve` method.
1. Start the message consumers loop when application starts.
1. Stop the message consumers loop just before the application go down.

For instance (`FastAPI` + `dependency_injector`):
```python

@asynccontextmanager
async def lifespan(app: FastAPI):
    # this part is called on application start
    container.logger().info("Initiating startup & background jobs")
    # consumer provider is called to get particular type of the consumer, making 
    # the autoresolve feature working out of the box
    container.kafka_manager().set_consumer_provider(container.resolve) 
    container.kafka_manager().start_consumer_loop()
    yield
    # this part is called when application is tearing down
    container.logger().info("Stopping background jobs")
    container.kafka_manager().stop_consumer_loop()
```

---