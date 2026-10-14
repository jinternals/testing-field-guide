package deep.jit;

/**
 * Times the same method from its first call: 30 batches of 100
 * calls, mean time per call in each batch. Run it normally, and
 * with -Xint (interpreter only) to see what the JIT adds;
 * -XX:+PrintCompilation shows when each tier compiles it.
 */
public final class WarmUp {
  static final int[] DATA = new int[10_000];
  static volatile long sink;

  public static void main(String[] args) {
    for (int i = 0; i < DATA.length; i++) {
      DATA[i] = i % 97;
    }
    System.out.println("batch  µs per call");
    for (int batch = 1; batch <= 30; batch++) {
      long t0 = System.nanoTime();
      for (int i = 0; i < 100; i++) {
        sink = sumOfSquares(DATA);
      }
      double us = (System.nanoTime() - t0) / 1e3 / 100;
      if (batch <= 5 || batch % 5 == 0) {
        System.out.printf("%5d %10.2f%n", batch, us);
      }
    }
  }

  static long sumOfSquares(int[] a) {
    long s = 0;
    for (int x : a) {
      s += (long) x * x;
    }
    return s;
  }
}
