package shop;

import java.net.URI;
import java.net.http.*;
import java.time.Instant;
import java.util.*;
import java.util.concurrent.*;

/** A tiny closed-model load test: N virtual users loop for a fixed time. */
public class LoadSmoke {
  public static void main(String[] args) throws Exception {
    var repo = new InMemoryOrderRepository();
    repo.save(new Order("ord-1", "a@example.com", List.of(),
        Money.of("1140"), Instant.EPOCH));
    var api = new OrderApi(repo);
    var uri = URI.create("http://127.0.0.1:" + api.start() + "/orders/ord-1");
    var http = HttpClient.newHttpClient();
    var req = HttpRequest.newBuilder(uri).build();

    int users = args.length > 0 ? Integer.parseInt(args[0]) : 50;
    long warmUpEnd = System.nanoTime() + 3_000_000_000L;   // 3 s warm-up
    long end = warmUpEnd + 10_000_000_000L;                 // 10 s measured
    var latencies = new ConcurrentLinkedQueue<Long>();
    var errors = new LongAdderBox();
    try (var pool = Executors.newVirtualThreadPerTaskExecutor()) {
      for (int u = 0; u < users; u++) {
        pool.submit(() -> {
          while (System.nanoTime() < end) {
            long t0 = System.nanoTime();
            try {
              var res = http.send(req, HttpResponse.BodyHandlers.ofString());
              if (res.statusCode() != 200) errors.inc();
            } catch (Exception e) { errors.inc(); }
            if (t0 > warmUpEnd) latencies.add(System.nanoTime() - t0);
          }
          return null;
        });
      }
    }
    api.stop();
    long[] ms = latencies.stream().mapToLong(Long::longValue).sorted().toArray();
    System.out.printf("users=%d  requests=%,d  errors=%d  throughput=%,.0f req/s%n",
        users, ms.length, errors.n, ms.length / 10.0);
    for (double p : new double[] {50, 90, 95, 99, 99.9})
      System.out.printf("p%-4s %7.2f ms%n", fmt(p), pct(ms, p) / 1e6);
    System.out.printf("max   %7.2f ms%n", ms[ms.length - 1] / 1e6);
    System.out.printf("mean  %7.2f ms%n",
        Arrays.stream(ms).average().orElse(0) / 1e6);
  }
  static long pct(long[] sorted, double p) {
    int i = (int) Math.ceil(p / 100 * sorted.length) - 1;   // nearest-rank
    return sorted[Math.max(0, i)];
  }
  static String fmt(double p) { return p % 1 == 0 ? String.valueOf((int) p) : String.valueOf(p); }
  static final class LongAdderBox { volatile long n; synchronized void inc() { n++; } }
}
