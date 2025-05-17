from confluent_kafka import Message# tpkm: Typed Python Kafka Manager 
---

This tool is to make usage of kafka super easy and safe, 
utilizing best practices and power given by [`confluent_kafka`](https://github.com/confluentinc/confluent-kafka-python)

### Publishing message

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

### Consuming message

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
Once consumer become available via provider (any DI for example) each message is handled out of the box

I hope you like the concept!

To achieve full power of this lib, you need to configure it

### Configuration

The example one, compatible with DI container:

```python
class Container(containers.DeclarativeContainer):
    kafka_manager: Singleton[KafkaManager] = Singleton(
        lambda: KafkaManager(
            kafka_client=KafkaClient(
                Producer({"bootstrap.servers": config.kafka_broker_url}),
                FibonacciRetryPolicy(10),
            ),
            kafka_consumer=KafkaConsumerManager(
                Consumer(
                    {
                        "bootstrap.servers": config.kafka_broker_url,
                        "group.id": config.kafka_group_id,
                        "enable.auto.commit": False,
                        "auto.offset.reset": "earliest",
                    }
                )
            ),
            logger=logger,
        )
    )
```

Then in the bootstrap of the project add (here, with the FastAPI):
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

