package shop.events;

import java.nio.charset.StandardCharsets;
import java.util.Map;
import org.apache.kafka.clients.producer.*;
import org.apache.kafka.common.serialization.StringSerializer;

/** Publishes order events; the event id travels as a header. */
public class OrderEventPublisher implements AutoCloseable {
  private final KafkaProducer<String, String> producer;
  private final String topic;

  public OrderEventPublisher(String bootstrapServers, String topic) {
    this.topic = topic;
    this.producer = new KafkaProducer<>(Map.of(
        ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrapServers,
        ProducerConfig.ACKS_CONFIG, "all"),
        new StringSerializer(), new StringSerializer());
  }

  public void publish(String eventId, String orderId, String json)
      throws Exception {
    var record = new ProducerRecord<>(topic, orderId, json);
    record.headers().add("event-id",
        eventId.getBytes(StandardCharsets.UTF_8));
    producer.send(record).get();          // wait for the broker's ack
  }

  @Override public void close() { producer.close(); }
}
