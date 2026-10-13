package shop.events;

import static java.nio.charset.StandardCharsets.UTF_8;

import java.time.Duration;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;
import org.apache.kafka.clients.consumer.*;
import org.apache.kafka.common.errors.WakeupException;
import org.apache.kafka.common.serialization.StringDeserializer;

/**
 * Kafka delivers at least once: an event can arrive twice.
 * This consumer is idempotent - each event id is applied once.
 */
public class OrderEventConsumer implements AutoCloseable {
  private final KafkaConsumer<String, String> consumer;
  private final Set<String> applied =
      ConcurrentHashMap.newKeySet();
  private final AtomicInteger received = new AtomicInteger();
  private final Thread loop;

  public OrderEventConsumer(String servers, String topic) {
    consumer = new KafkaConsumer<>(Map.of(
        ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, servers,
        ConsumerConfig.GROUP_ID_CONFIG, "order-projection",
        ConsumerConfig.AUTO_OFFSET_RESET_CONFIG, "earliest"),
        new StringDeserializer(), new StringDeserializer());
    consumer.subscribe(List.of(topic));
    loop = Thread.ofPlatform().name("order-events")
        .start(this::run);
  }

  private void run() {
    try {
      while (true) {
        var records = consumer.poll(Duration.ofMillis(200));
        for (var record : records) {
          received.incrementAndGet();
          var id = record.headers().lastHeader("event-id");
          applied.add(new String(id.value(), UTF_8));
          // adding an id that is already there changes nothing
        }
      }
    } catch (WakeupException stopping) {
      // close() was called
    } finally {
      consumer.close();
    }
  }

  public int received() { return received.get(); }
  public int applied() { return applied.size(); }

  @Override public void close() throws InterruptedException {
    consumer.wakeup();
    loop.join();
  }
}
