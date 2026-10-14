package deep.jmm;

/**
 * A thread spins until another thread sets a flag. With a
 * plain field the JIT may read it once and loop forever; with
 * volatile every read must see the latest write.
 */
public final class StaleFlag {
  static boolean plain;
  static volatile boolean marked;

  public static void main(String[] args) throws Exception {
    System.out.println("plain field:    " + stops(false));
    System.out.println("volatile field: " + stops(true));
    System.exit(0);           // the stuck spinner never ends
  }

  static String stops(boolean useVolatile) throws Exception {
    Thread spinner = new Thread(() -> {
      if (useVolatile) {
        while (!marked) {
          // spin
        }
      } else {
        while (!plain) {
          // spin
        }
      }
    });
    spinner.setDaemon(true);
    spinner.start();
    Thread.sleep(1_000);      // let the JIT compile the loop
    if (useVolatile) {
      marked = true;
    } else {
      plain = true;
    }
    spinner.join(3_000);
    return spinner.isAlive()
        ? "still spinning 3 s after the flag was set"
        : "stopped";
  }
}
