package deep.vt;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.locks.ReentrantLock;

/**
 * 1) 10,000 tasks that each block for 100 ms: a pool of 200
 *    platform threads against one virtual thread per task.
 * 2) Pinning on Java 21: 100 virtual threads block for 100 ms
 *    while holding a lock, synchronized against ReentrantLock.
 */
public final class VirtualThreads {
  public static void main(String[] args) throws Exception {
    System.out.println("Java " + Runtime.version().feature()
        + ", carrier threads (availableProcessors): "
        + Runtime.getRuntime().availableProcessors());
    time("10,000 tasks, 200 platform threads", 10_000,
        Executors.newFixedThreadPool(200),
        VirtualThreads::block);
    time("10,000 tasks, virtual thread each", 10_000,
        Executors.newVirtualThreadPerTaskExecutor(),
        VirtualThreads::block);
    time("100 tasks, synchronized + sleep", 100,
        Executors.newVirtualThreadPerTaskExecutor(),
        VirtualThreads::blockInSynchronized);
    time("100 tasks, ReentrantLock + sleep", 100,
        Executors.newVirtualThreadPerTaskExecutor(),
        VirtualThreads::blockInLock);
  }

  static void time(String name, int tasks, ExecutorService ex,
      Runnable task) {
    long t0 = System.nanoTime();
    try (ex) {
      for (int i = 0; i < tasks; i++) {
        ex.submit(task);
      }
    }                               // close() waits for all
    System.out.printf("%-36s %6.2f s%n", name,
        (System.nanoTime() - t0) / 1e9);
  }

  static void block() {
    sleep(100);
  }

  static void blockInSynchronized() {
    Object lock = new Object();             // one lock per task
    synchronized (lock) {
      sleep(100);                           // pins the carrier
    }
  }

  static void blockInLock() {
    var lock = new ReentrantLock();
    lock.lock();
    try {
      sleep(100);                           // unmounts
    } finally {
      lock.unlock();
    }
  }

  static void sleep(long ms) {
    try {
      Thread.sleep(ms);
    } catch (InterruptedException e) {
      Thread.currentThread().interrupt();
    }
  }
}
