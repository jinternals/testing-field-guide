package deep.kafka;

import deep.Stats;
import java.time.Duration;
import java.util.ArrayList;
import java.util.Collection;
import java.util.List;
import java.util.Map;
import java.util.Properties;
import java.util.Set;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import org.apache.kafka.clients.admin.Admin;
import org.apache.kafka.clients.admin.NewTopic;
import org.apache.kafka.clients.consumer.ConsumerRebalanceListener;
import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.apache.kafka.clients.consumer.KafkaConsumer;
import org.apache.kafka.clients.producer.KafkaProducer;
import org.apache.kafka.clients.producer.ProducerRecord;
import org.apache.kafka.common.Metric;
import org.apache.kafka.common.MetricName;
import org.apache.kafka.common.TopicPartition;
import org.apache.kafka.common.serialization.ByteArrayDeserializer;
import org.apache.kafka.common.serialization.ByteArraySerializer;

/**
 * Kafka against one local broker: producer batching
 * (linger.ms), consumer fetch waiting (fetch.min.bytes /
 * fetch.max.wait.ms), partitions against consumers, and
 * max.poll.interval.ms.
 */
public final class KafkaLatency {
  static final String BOOT = "localhost:9092";
  static int topics = 0;

  public static void main(String[] args) throws Exception {
    switch (args[0]) {
      case "producer" -> producer();
      case "fetch" -> fetch();
      case "partitions" -> partitions();
      case "pollinterval" -> pollInterval();
      default -> throw new IllegalArgumentException(args[0]);
    }
  }

  static String topic(int partitions) throws Exception {
    String name = "t" + System.nanoTime() + "-" + topics++;
    var p = new Properties();
    p.put("bootstrap.servers", BOOT);
    try (Admin admin = Admin.create(p)) {
      var topic = new NewTopic(name, partitions, (short) 1);
      admin.createTopics(List.of(topic)).all().get();
    }
    return name;
  }

  static KafkaProducer<byte[], byte[]> producer(long lingerMs) {
    var p = new Properties();
    p.put("bootstrap.servers", BOOT);
    p.put("linger.ms", Long.toString(lingerMs));
    p.put("key.serializer", ByteArraySerializer.class);
    p.put("value.serializer", ByteArraySerializer.class);
    return new KafkaProducer<>(p);
  }

  static KafkaConsumer<byte[], byte[]> consumer(
      Map<String, Object> extra) {
    var p = new Properties();
    p.put("bootstrap.servers", BOOT);
    p.put("key.deserializer", ByteArrayDeserializer.class);
    p.put("value.deserializer", ByteArrayDeserializer.class);
    p.putAll(extra);
    return new KafkaConsumer<>(p);
  }

  // ------------------------------------------------ producer
  /** Records due at a fixed rate; latency from due to ack. */
  static void producer() throws Exception {
    System.out.println("records of 100 bytes, one partition,"
        + " acks=all (default), latency from due time to ack");
    for (int rate : new int[] {20, 2000}) {
      for (long linger : new long[] {0, 5, 50}) {
        String t = topic(1);
        int n = rate * 5;                      // 5 seconds
        long interval = 1_000_000_000L / rate;
        long[] lat = new long[n];
        var done = new CountDownLatch(n);
        try (var prod = producer(linger)) {
          prod.send(new ProducerRecord<>(t, new byte[100]))
              .get();                          // connect first
          long start = System.nanoTime();
          for (int i = 0; i < n; i++) {
            long due = start + i * interval;
            while (System.nanoTime() < due) {
              Thread.onSpinWait();
            }
            final int k = i;
            prod.send(new ProducerRecord<>(t, new byte[100]),
                (md, e) -> {
                  lat[k] = System.nanoTime() - due;
                  done.countDown();
                });
          }
          done.await(60, TimeUnit.SECONDS);
          System.out.printf("rate %4d/s  linger.ms %2d  %s"
              + "  | requests %5.0f  records/request %6.1f%n",
              rate, linger, new Stats(lat).line(),
              metric(prod.metrics(), "request-total"),
              metric(prod.metrics(),
                  "records-per-request-avg"));
        }
      }
    }
  }

  static double metric(Map<MetricName, ? extends Metric> m,
      String name) {
    return m.entrySet().stream()
        .filter(e -> e.getKey().name().equals(name)
            && e.getKey().group().equals("producer-metrics"))
        .mapToDouble(e -> ((Number) e.getValue().metricValue())
            .doubleValue())
        .findFirst().orElse(Double.NaN);
  }

  // --------------------------------------------------- fetch
  /** One record every 100 ms; latency from send to poll. */
  static void fetch() throws Exception {
    System.out.println("one record every 100 ms, 50 records;"
        + " latency from send to the consumer's poll()");
    fetchRun("fetch.min.bytes 1 (default)", Map.of());
    fetchRun("fetch.min.bytes 1000000, max.wait 500",
        Map.of("fetch.min.bytes", 1_000_000,
            "fetch.max.wait.ms", 500));
  }

  static void fetchRun(String label, Map<String, Object> cfg)
      throws Exception {
    String t = topic(1);
    var tp = new TopicPartition(t, 0);
    int n = 50;
    long[] sent = new long[n];
    long[] lat = new long[n];
    try (var cons = consumer(cfg); var prod = producer(0)) {
      cons.assign(List.of(tp));
      cons.seekToBeginning(List.of(tp));
      cons.poll(Duration.ofMillis(200));        // connect first
      var sender = Thread.ofPlatform().start(() -> {
        for (int i = 0; i < n; i++) {
          sent[i] = System.nanoTime();
          prod.send(new ProducerRecord<>(t,
              Integer.toString(i).getBytes(), new byte[100]));
          sleep(100);
        }
      });
      int got = 0;
      long deadline = System.nanoTime() + 30_000_000_000L;
      while (got < n && System.nanoTime() < deadline) {
        var records = cons.poll(Duration.ofSeconds(1));
        long now = System.nanoTime();
        for (ConsumerRecord<byte[], byte[]> r : records) {
          int i = Integer.parseInt(new String(r.key()));
          lat[i] = now - sent[i];
          got++;
        }
      }
      sender.join();
    }
    System.out.printf("%-40s %s%n", label,
        new Stats(lat).line());
  }

  // ---------------------------------------------- partitions
  /** Four consumers in one group, a topic with 2 partitions. */
  static void partitions() throws Exception {
    String t = topic(2);
    int members = 4;
    var threads = new ArrayList<Thread>();
    int[] owned = new int[members];
    var stop = new CountDownLatch(1);
    for (int c = 0; c < members; c++) {
      final int id = c;
      threads.add(Thread.ofPlatform().start(() -> {
        try (var cons = consumer(Map.of(
            "group.id", "g-" + t, "client.id", "c" + id))) {
          var listener = new ConsumerRebalanceListener() {
            public void onPartitionsRevoked(
                Collection<TopicPartition> p) { }

            public void onPartitionsAssigned(
                Collection<TopicPartition> p) {
              owned[id] = cons.assignment().size();
            }
          };
          cons.subscribe(List.of(t), listener);
          while (stop.getCount() > 0) {
            cons.poll(Duration.ofMillis(200));
          }
        }
      }));
    }
    Thread.sleep(15_000);                      // let it settle
    System.out.println("topic with 2 partitions,"
        + " 4 consumers in one group, after 15 s:");
    for (int c = 0; c < members; c++) {
      System.out.printf("consumer c%d  partitions %d%n",
          c, owned[c]);
    }
    stop.countDown();
    for (Thread th : threads) {
      th.join();
    }
  }

  // -------------------------------------------- poll interval
  /** Processing that takes longer than max.poll.interval.ms. */
  static void pollInterval() throws Exception {
    String t = topic(1);
    try (var prod = producer(0)) {
      prod.send(new ProducerRecord<>(t, new byte[100])).get();
    }
    try (var cons = consumer(Map.of("group.id", "slow-" + t,
        "auto.offset.reset", "earliest",
        "enable.auto.commit", false,
        "max.poll.interval.ms", 3000))) {
      cons.subscribe(Set.of(t));
      int got = 0;
      while (got == 0) {
        got = cons.poll(Duration.ofSeconds(1)).count();
      }
      System.out.println("max.poll.interval.ms 3000: polled "
          + got + " record, processing for 6 s");
      Thread.sleep(6_000);                     // "processing"
      try {
        cons.commitSync();
        System.out.println("commitSync: committed");
      } catch (Exception e) {
        System.out.println("commitSync: "
            + e.getClass().getSimpleName() + ": "
            + e.getMessage().lines().findFirst().orElse(""));
      }
    }
  }

  static void sleep(long ms) {
    try {
      Thread.sleep(ms);
    } catch (InterruptedException e) {
      Thread.currentThread().interrupt();
    }
  }
}
