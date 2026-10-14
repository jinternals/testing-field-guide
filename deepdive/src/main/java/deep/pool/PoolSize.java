package deep.pool;

import deep.Stats;
import java.util.concurrent.ConcurrentLinkedQueue;
import java.util.concurrent.Semaphore;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.LongAdder;

/**
 * 64 callers share an app-side pool of P connections in
 * front of a database that serves 4 queries at a time, 10 ms
 * each. Each
 * caller loops for 3 s. Measured over the steady window
 * 0.5–2.5 s: throughput λ, mean time in system W, and the
 * number in the system L, sampled every millisecond.
 * Little's Law says L = λ·W.
 */
public final class PoolSize {
  static final int CALLERS = 64;
  static final int DB_CAPACITY = 4;
  static final long QUERY_MS = 10;
  static final long RUN_MS = 3_000;
  static final long FROM_MS = 500;
  static final long TO_MS = 2_500;

  record Done(long finishedAt, long latency) {}

  public static void main(String[] args) throws Exception {
    System.out.printf("%5s %10s %9s %9s %11s %7s %7s%n",
        "pool", "queries/s", "mean ms", "p99 ms", "wait in DB",
        "L", "λ·W");
    for (int pool : new int[] {1, 2, 4, 8, 16, 64}) {
      run(pool);
    }
  }

  static void run(int poolSize) throws Exception {
    var pool = new Semaphore(poolSize, true);
    var db = new Semaphore(DB_CAPACITY, true);
    var done = new ConcurrentLinkedQueue<Done>();
    var dbWait = new LongAdder();
    var inSystem = new AtomicInteger();
    long start = System.nanoTime();
    long end = start + RUN_MS * 1_000_000;
    Thread[] callers = new Thread[CALLERS];
    for (int i = 0; i < CALLERS; i++) {
      callers[i] = Thread.ofVirtual().start(() -> {
        while (System.nanoTime() < end) {
          long t0 = System.nanoTime();
          inSystem.incrementAndGet();
          pool.acquireUninterruptibly();
          long t1 = System.nanoTime();
          db.acquireUninterruptibly();   // the database's queue
          dbWait.add(System.nanoTime() - t1);
          sleep(QUERY_MS);
          db.release();
          pool.release();
          inSystem.decrementAndGet();
          long t2 = System.nanoTime();
          done.add(new Done(t2 - start, t2 - t0));
        }
      });
    }
    double lSum = 0;
    int samples = 0;
    while (System.nanoTime() - start < TO_MS * 1_000_000) {
      if (System.nanoTime() - start >= FROM_MS * 1_000_000) {
        lSum += inSystem.get();
        samples++;
      }
      Thread.sleep(1);
    }
    for (Thread t : callers) {
      t.join();
    }
    long[] w = done.stream()
        .filter(d -> d.finishedAt() >= FROM_MS * 1_000_000
            && d.finishedAt() < TO_MS * 1_000_000)
        .mapToLong(Done::latency).toArray();
    Stats st = new Stats(w);
    double lambda = w.length / ((TO_MS - FROM_MS) / 1e3);
    System.out.printf(
        "%5d %10.0f %9.1f %9.1f %8.1f ms %7.1f %7.1f%n",
        poolSize, lambda, st.meanMs(), st.ms(99),
        dbWait.sum() / 1e6 / done.size(), lSum / samples,
        lambda * st.meanMs() / 1e3);
  }

  static void sleep(long ms) {
    try {
      Thread.sleep(ms);
    } catch (InterruptedException e) {
      Thread.currentThread().interrupt();
    }
  }
}
