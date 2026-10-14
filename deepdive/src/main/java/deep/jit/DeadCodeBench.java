package deep.jit;

import java.util.concurrent.TimeUnit;
import org.openjdk.jmh.annotations.Benchmark;
import org.openjdk.jmh.annotations.BenchmarkMode;
import org.openjdk.jmh.annotations.Mode;
import org.openjdk.jmh.annotations.OutputTimeUnit;
import org.openjdk.jmh.annotations.Scope;
import org.openjdk.jmh.annotations.State;
import org.openjdk.jmh.infra.Blackhole;

/**
 * Does the JIT remove work whose result is never used, or
 * compute constant expressions ahead of time? Three kinds of
 * work, each with its result discarded, returned, or computed
 * from a compile-time constant.
 */
@State(Scope.Thread)
@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.NANOSECONDS)
public class DeadCodeBench {
  static final double CONSTANT = Math.PI;
  static final int[] FIXED = new int[1_000];
  double x = Math.PI;
  int[] data = new int[1_000];

  @Benchmark
  public void baseline() {
    // nothing: the cost of the harness itself
  }

  @Benchmark
  public void discarded() {
    Math.log(x);                     // result unused: dead code
  }

  @Benchmark
  public double returned() {
    return Math.log(x);           // JMH consumes the result
  }

  @Benchmark
  public void blackhole(Blackhole bh) {
    bh.consume(Math.log(x));
  }

  @Benchmark
  public double constant() {
    return Math.log(CONSTANT);    // foldable at compile time?
  }

  @Benchmark
  public void sumDiscarded() {
    long s = 0;
    for (int v : data) {
      s += v;                        // the sum is never used
    }
  }

  @Benchmark
  public long sumReturned() {
    long s = 0;
    for (int v : data) {
      s += v;
    }
    return s;
  }

  @Benchmark
  public void mulDiscarded() {
    double r = x * x + 1;            // never used
  }

  @Benchmark
  public double mulReturned() {
    return x * x + 1;
  }

  @Benchmark
  public double mulConstant() {
    return CONSTANT * CONSTANT + 1;  // static final: foldable
  }
}
