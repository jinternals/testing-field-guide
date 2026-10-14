package deep.latency;

import deep.Stats;
import java.util.Arrays;

/**
 * A service that answers in 1 ms, except that it stalls for
 * 1 s once (from second 2 to second 3 of a 10 s run). Measured
 * three ways: a closed loop (send the next request when the
 * last one returns); the same data with HdrHistogram's
 * correction; and an open loop that keeps a schedule of one
 * request every 2 ms and measures from the time each request
 * was due.
 */
public final class CoordinatedOmission {
  static final long RUN_NS = 10_000_000_000L;
  static final long STALL_FROM = 2_000_000_000L;
  static final long STALL_TO = 3_000_000_000L;
  static final long INTERVAL = 2_000_000L;   // 500 per second
  static long start;

  public static void main(String[] args) throws Exception {
    long[] closed = closedLoop();
    report("closed loop (naive)", closed);
    report("closed loop, corrected", corrected(closed));
    report("open loop, from due time", openLoop());
  }

  static void serve() throws InterruptedException {
    long now = System.nanoTime() - start;
    if (now >= STALL_FROM && now < STALL_TO) {
      Thread.sleep((STALL_TO - now) / 1_000_000 + 1);  // stall
    } else {
      Thread.sleep(1);
    }
  }

  /** Waits for each response, then sleeps to keep 500/s. */
  static long[] closedLoop() throws Exception {
    long[] out = new long[10_000];
    int n = 0;
    start = System.nanoTime();
    while (System.nanoTime() - start < RUN_NS) {
      long t0 = System.nanoTime();
      serve();
      long t1 = System.nanoTime();
      out = grow(out, n);
      out[n++] = t1 - t0;
      long next = t0 + INTERVAL;
      while (System.nanoTime() < next) {
        Thread.onSpinWait();
      }
    }
    return Arrays.copyOf(out, n);
  }

  /** Requests are due every 2 ms; latency from due time. */
  static long[] openLoop() throws Exception {
    int total = (int) (RUN_NS / INTERVAL);
    long[] out = new long[total];
    start = System.nanoTime();
    for (int i = 0; i < total; i++) {
      long due = start + i * INTERVAL;
      while (System.nanoTime() < due) {
        Thread.onSpinWait();
      }
      serve();
      out[i] = System.nanoTime() - due;
    }
    return out;
  }

  /**
   * HdrHistogram's recordValueWithExpectedInterval: for a value
   * longer than the interval, also record the requests that
   * would have been sent meanwhile: value - k·interval.
   */
  static long[] corrected(long[] values) {
    long[] out = new long[values.length * 2];
    int n = 0;
    for (long v : values) {
      out = grow(out, n);
      out[n++] = v;
      for (long m = v - INTERVAL; m >= INTERVAL;
          m -= INTERVAL) {
        out = grow(out, n);
        out[n++] = m;
      }
    }
    return Arrays.copyOf(out, n);
  }

  static long[] grow(long[] a, int n) {
    return n < a.length ? a : Arrays.copyOf(a, a.length * 2);
  }

  static void report(String name, long[] v) {
    Stats st = new Stats(v);
    System.out.printf("%-26s %6d samples  p50 %7.2f  p99 %7.2f"
        + "  p99.9 %7.2f  max %7.2f ms%n", name, v.length,
        st.ms(50), st.ms(99), st.ms(99.9), st.maxMs());
  }
}
