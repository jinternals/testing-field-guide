package deep.vt;

import java.lang.management.ManagementFactory;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.concurrent.CountDownLatch;

/**
 * 10,000 threads, each blocked 20 frames deep. Prints where
 * their stacks live: native memory (Native Memory Tracking,
 * category Thread) or heap objects
 * (jdk.internal.vm.StackChunk).
 * Run with -XX:NativeMemoryTracking=summary.
 */
public final class ThreadMemory {
  static final int N = 10_000;
  static final CountDownLatch release = new CountDownLatch(1);
  static final CountDownLatch blocked = new CountDownLatch(N);

  static void deep(int depth) {
    if (depth > 0) {
      deep(depth - 1);
      return;
    }
    blocked.countDown();
    try {
      release.await();
    } catch (InterruptedException e) {
      Thread.currentThread().interrupt();
    }
  }

  public static void main(String[] args) throws Exception {
    boolean virtual = args[0].equals("virtual");
    for (int i = 0; i < N; i++) {
      Runnable r = () -> deep(20);
      if (virtual) {
        Thread.ofVirtual().start(r);
      } else {
        Thread.ofPlatform().daemon().start(r);
      }
    }
    blocked.await();
    System.gc();
    var heap = ManagementFactory.getMemoryMXBean()
        .getHeapMemoryUsage().getUsed();
    System.out.printf("%s threads: %,d blocked, 20 frames"
        + " deep%n", virtual ? "virtual" : "platform", N);
    System.out.printf("heap used after GC  %,d KB%n",
        heap >> 10);
    System.out.println(status("VmRSS"));
    String pid = Long.toString(ProcessHandle.current().pid());
    print(jcmd(pid, "VM.native_memory", "summary"),
        "Thread (reserved");
    print(jcmd(pid, "GC.class_histogram"), "StackChunk");
    release.countDown();
    System.exit(0);
  }

  static String status(String key) throws Exception {
    return Files.readAllLines(Path.of("/proc/self/status"))
        .stream().filter(l -> l.startsWith(key + ":"))
        .findFirst().orElse(key + ": n/a")
        .replaceAll("\\s+", " ");
  }

  static String jcmd(String... args) throws Exception {
    String jcmd = Path.of(System.getProperty("java.home"),
        "bin", "jcmd").toString();
    var cmd = new java.util.ArrayList<String>();
    cmd.add(jcmd);
    cmd.addAll(java.util.List.of(args));
    Process p = new ProcessBuilder(cmd)
        .redirectErrorStream(true).start();
    String out = new String(p.getInputStream().readAllBytes());
    p.waitFor();
    return out;
  }

  /** The line containing key, and for NMT the next two. */
  static void print(String out, String key) {
    var lines = out.lines().toList();
    for (int i = 0; i < lines.size(); i++) {
      if (lines.get(i).contains(key)) {
        System.out.println(lines.get(i).strip());
        for (int k = 1; k <= 2 && key.contains("reserved")
            && i + k < lines.size(); k++) {
          System.out.println(lines.get(i + k).strip());
        }
        return;
      }
    }
    System.out.println(key + ": not listed");
  }
}
