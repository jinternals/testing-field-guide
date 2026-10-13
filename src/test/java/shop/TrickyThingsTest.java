package shop;

import static org.assertj.core.api.Assertions.assertThat;
import static org.junit.jupiter.api.Assertions.assertTimeoutPreemptively;

import java.nio.file.*;
import java.time.*;
import java.util.*;
import java.util.concurrent.*;
import org.junit.jupiter.api.*;
import org.junit.jupiter.api.io.TempDir;

class TrickyThingsTest {

  @Test void timeComesFromAnInjectedClock() {
    Instant newYearsEve = Instant.parse("2026-12-31T23:59:59Z");
    Clock clock = Clock.fixed(newYearsEve, ZoneOffset.UTC);
    var service = new OrderService(new InMemoryOrderRepository(),
        (c, m) -> "PAY", (to, s, b) -> {}, new DiscountPolicy(), clock);

    Order o = service.placeOrder("a@example.com",
        List.of(new Item("PEN", Money.of("1"), 1)));

    assertThat(o.placedAt()).isEqualTo(newYearsEve);
  }

  @Test void randomnessComesFromASeed() {
    var a = new Random(42).ints(5, 0, 100).boxed().toList();
    var b = new Random(42).ints(5, 0, 100).boxed().toList();
    assertThat(a).isEqualTo(b);  // same seed, same sequence
  }

  @Test void filesGoInAFreshTempDir(@TempDir Path dir) throws Exception {
    Path report = dir.resolve("report.csv");
    Files.writeString(report, "sku,qty\nPEN,2\n");
    assertThat(Files.readAllLines(report))
        .containsExactly("sku,qty", "PEN,2");
  }  // JUnit deletes dir afterwards

  @Test void concurrentSavesAreAllKept() throws Exception {
    var repo = new InMemoryOrderRepository();
    int threads = 16, perThread = 500;
    var start = new CountDownLatch(1);
    try (ExecutorService pool = Executors.newFixedThreadPool(threads)) {
      for (int t = 0; t < threads; t++) {
        int base = t * perThread;
        pool.submit(() -> {
          start.await();  // release all threads at once
          for (int i = 0; i < perThread; i++)
            repo.save(new Order("o" + (base + i), "x@example.com",
                List.of(), Money.of("0"), Instant.EPOCH));
          return null;
        });
      }
      start.countDown();
    }  // close() waits for all tasks
    for (int i = 0; i < threads * perThread; i++)
      assertThat(repo.findById("o" + i)).isPresent();
  }

  @Test void slowCodeFailsFastInsteadOfHangingTheBuild() {
    assertTimeoutPreemptively(Duration.ofSeconds(1),
        () -> new DiscountPolicy().percentFor(Money.of("1")));
  }
}
