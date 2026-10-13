package shop.events;

import static org.assertj.core.api.Assertions.assertThat;
import static org.awaitility.Awaitility.await;

import java.time.Duration;
import org.junit.jupiter.api.Test;
import org.testcontainers.kafka.KafkaContainer;

class OrderEventsIT {
  static final KafkaContainer KAFKA =
      new KafkaContainer("apache/kafka-native:4.3.1");
  static { KAFKA.start(); }      // singleton per test JVM

  @Test
  void redeliveredEventIsAppliedOnlyOnce() throws Exception {
    String kafka = KAFKA.getBootstrapServers();
    String paid = "{\"status\":\"PAID\"}";
    try (var out = new OrderEventPublisher(kafka, "orders");
         var in = new OrderEventConsumer(kafka, "orders")) {

      out.publish("evt-1", "ord-1", paid);
      out.publish("evt-1", "ord-1", paid);    // redelivered
      out.publish("evt-2", "ord-2", paid);

      await().atMost(Duration.ofSeconds(30))  // no sleep
          .untilAsserted(() -> {
            assertThat(in.received()).isEqualTo(3);
            assertThat(in.applied()).isEqualTo(2);
          });
    }
  }
}
