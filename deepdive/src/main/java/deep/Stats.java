package deep;

import java.util.Arrays;

/** Exact percentiles of recorded latencies (nanoseconds). */
public final class Stats {
  private final long[] values;

  public Stats(long[] nanos) {
    values = nanos.clone();
    Arrays.sort(values);
  }

  /** Nearest-rank percentile, in milliseconds. */
  public double ms(double percentile) {
    int rank = (int) Math.ceil(percentile / 100 * values.length);
    return values[Math.max(rank, 1) - 1] / 1e6;
  }

  public double maxMs() {
    return values[values.length - 1] / 1e6;
  }

  public double meanMs() {
    return Arrays.stream(values).average().orElse(0) / 1e6;
  }

  public long countAbove(double ms) {
    return Arrays.stream(values).filter(v -> v > ms * 1e6).count();
  }

  public String line() {
    return String.format("p50 %7.2f  p90 %7.2f  p99 %7.2f"
        + "  max %7.2f ms", ms(50), ms(90), ms(99), maxMs());
  }
}
