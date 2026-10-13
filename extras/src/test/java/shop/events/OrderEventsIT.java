package shop.events;

import static org.assertj.core.api.Assertions.assertThat;
import static org.awaitility.Awaitility.await;

import java.time.Duration;
import org.junit.jupiter.api.Test;
import org.testcontainers.kafka.KafkaContainer;

class OrderEventsIT {
  static final KafkaContainer KAFKA =
      new KafkaContainer("apache/kafka-native:4.3.1");
  static { KAFKA.start(); }            // singleton per test JVM

  @Test
  void redeliveredEventIsAppliedOnlyOnce() throws Exception {
    String kafka = KAFKA.getBootstrapServers();
    try (var publisher = new OrderEventPublisher(kafka, "orders");
         var consumer = new OrderEventConsumer(kafka, "orders")) {

      publisher.publish("evt-1", "ord-1", "{\"status\":\"PAID\"}");
      publisher.publish("evt-1", "ord-1", "{\"status\":\"PAID\"}");
      publisher.publish("evt-2", "ord-2", "{\"status\":\"PAID\"}");

      await().atMost(Duration.ofSeconds(30))     // no Thread.sleep
          .untilAsserted(() -> {
            assertThat(consumer.received()).isEqualTo(3);
            assertThat(consumer.applied()).isEqualTo(2);
          });
    }
  }
}
