package deep.pool;

import deep.Stats;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;

/**
 * 400 CPU-bound tasks (about 5 ms of work each) on thread pools
 * of different sizes. No simulation: the resource is the CPU.
 */
public final class CpuPool {
  static final int TASKS = 400;

  public static void main(String[] args) throws Exception {
    int cpus = Runtime.getRuntime().availableProcessors();
    long iterations = calibrate();
    System.out.println("availableProcessors: " + cpus);
    System.out.printf("%8s %10s %10s %16s %16s%n", "threads",
        "total ms", "tasks/s", "task p50 ms", "task p99 ms");
    for (int threads : new int[] {1, cpus, cpus * 4, 64}) {
      run(threads, iterations);
    }
  }

  static void run(int threads, long iterations)
      throws Exception {
    long t0 = System.nanoTime();
    long[] done = new long[TASKS];
    try (var pool = Executors.newFixedThreadPool(threads)) {
      List<Future<?>> fs = new ArrayList<>();
      for (int i = 0; i < TASKS; i++) {
        int n = i;
        fs.add(pool.submit(() -> {
          long start = System.nanoTime();
          work(iterations);
          done[n] = System.nanoTime() - start;
        }));
      }
      for (Future<?> f : fs) {
        f.get();
      }
    }
    double totalMs = (System.nanoTime() - t0) / 1e6;
    Stats st = new Stats(done);
    System.out.printf("%8d %10.0f %10.0f %16.1f %16.1f%n",
        threads, totalMs, TASKS / (totalMs / 1e3),
        st.ms(50), st.ms(99));
  }

  static volatile long sink;

  static void work(long iterations) {
    long x = 1;
    for (long i = 0; i < iterations; i++) {
      x = x * 6364136223846793005L + 1442695040888963407L;
    }
    sink = x;
  }

  /** Iterations that take about 5 ms on this machine. */
  static long calibrate() {
    long n = 1_000_000;
    for (int i = 0; i < 5; i++) {
      work(n);                                // warm up
    }
    long t0 = System.nanoTime();
    work(n);
    double ms = (System.nanoTime() - t0) / 1e6;
    return (long) (n * 5 / ms);
  }
}
