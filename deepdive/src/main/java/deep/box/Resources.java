package deep.box;

import java.lang.management.ManagementFactory;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.concurrent.ForkJoinPool;
import java.util.stream.Collectors;

/** What the JVM decided from the container's limits. */
public final class Resources {
  public static void main(String[] args) throws Exception {
    var rt = Runtime.getRuntime();
    String gcs = ManagementFactory.getGarbageCollectorMXBeans()
        .stream().map(b -> b.getName())
        .collect(Collectors.joining(", "));
    System.out.printf("cgroup cpu.max %-14s memory.max %-11s"
        + " | CPUs %d  max heap %4d MB  commonPool %d  GC %s%n",
        cgroup("cpu.max"), cgroup("memory.max"),
        rt.availableProcessors(), rt.maxMemory() / (1 << 20),
        ForkJoinPool.getCommonPoolParallelism(), gcs);
  }

  static String cgroup(String file) {
    try {
      return Files.readAllLines(Path.of("/sys/fs/cgroup", file))
          .get(0).trim().replace(' ', '/');
    } catch (Exception e) {
      return "n/a";
    }
  }
}
