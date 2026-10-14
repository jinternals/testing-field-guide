package deep.box;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;

/**
 * Busy threads use up the container's CPU quota; a timer
 * thread measures how late its 5 ms sleeps wake up, and the
 * kernel's cpu.stat counts the throttled periods.
 */
public final class Throttle {
  static volatile boolean running = true;

  public static void main(String[] args) throws Exception {
    int burners = Integer.parseInt(args[0]);
    for (int i = 0; i < burners; i++) {
      Thread t = new Thread(() -> {
        long x = 0;
        while (running) {
          x++;
        }
      });
      t.setDaemon(true);
      t.start();
    }
    Thread.sleep(500);                 // let the burners run
    Map<String, Long> before = cpuStat();
    int n = 600;                       // 600 × 5 ms ≈ 3 s
    long[] late = new long[n];
    for (int i = 0; i < n; i++) {
      long t0 = System.nanoTime();
      Thread.sleep(5);
      late[i] = System.nanoTime() - t0 - 5_000_000;
    }
    Map<String, Long> after = cpuStat();
    running = false;
    Arrays.sort(late);
    System.out.printf("burners %d  sleep 5 ms, late by:"
        + " p50 %.1f  p99 %.1f  max %.1f ms  |  periods %d"
        + "  throttled %d  throttled %.0f ms%n", burners,
        late[n / 2] / 1e6, late[n * 99 / 100] / 1e6,
        late[n - 1] / 1e6,
        delta(before, after, "nr_periods"),
        delta(before, after, "nr_throttled"),
        delta(before, after, "throttled_usec") / 1e3);
  }

  static long delta(Map<String, Long> a, Map<String, Long> b,
      String key) {
    return b.getOrDefault(key, 0L) - a.getOrDefault(key, 0L);
  }

  static Map<String, Long> cpuStat() throws Exception {
    Map<String, Long> m = new HashMap<>();
    Path p = Path.of("/sys/fs/cgroup/cpu.stat");
    if (Files.exists(p)) {
      for (String line : Files.readAllLines(p)) {
        String[] kv = line.split(" ");
        m.put(kv[0], Long.parseLong(kv[1]));
      }
    }
    return m;
  }
}
