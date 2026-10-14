package deep.gc;

import deep.Stats;
import java.lang.management.ManagementFactory;
import java.util.SplittableRandom;

/**
 * An open-loop workload: one small operation due every 50 µs
 * for N seconds. Each operation replaces one of 400,000 live
 * 1 KB objects (a ~400 MB live set that keeps changing) and
 * allocates 8 KB of short-lived garbage. Latency counts from
 * the time the operation was due, so GC pauses are not hidden.
 */
public final class GcLatency {
  static final int LIVE = 400_000;
  static final long INTERVAL_NS = 50_000;
  static volatile Object sink;

  public static void main(String[] args) {
    int seconds = Integer.parseInt(args[0]);
    Object[] live = new Object[LIVE];
    for (int i = 0; i < LIVE; i++) {
      live[i] = new byte[1024];
    }
    var random = new SplittableRandom(42);
    int total = (int) (seconds * 1_000_000_000L / INTERVAL_NS);
    long[] latency = new long[total];
    // GC log lines carry JVM uptime: count pauses after this
    System.out.printf("measuring from uptime %.3f s%n",
        ManagementFactory.getRuntimeMXBean().getUptime() / 1e3);
    long start = System.nanoTime();
    for (int i = 0; i < total; i++) {
      long due = start + i * INTERVAL_NS;
      while (System.nanoTime() < due) {
        Thread.onSpinWait();
      }
      live[random.nextInt(LIVE)] = new byte[1024];
      sink = new byte[8 * 1024];
      latency[i] = System.nanoTime() - due;
    }
    Stats st = new Stats(latency);
    System.out.printf("%d operations  p50 %.3f  p99 %.3f  p99.9 %.3f"
        + "  max %.3f ms%n", total, st.ms(50), st.ms(99),
        st.ms(99.9), st.maxMs());
  }
}
