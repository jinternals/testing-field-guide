package deep.jit;

import java.util.concurrent.TimeUnit;
import org.openjdk.jmh.annotations.Benchmark;
import org.openjdk.jmh.annotations.BenchmarkMode;
import org.openjdk.jmh.annotations.Mode;
import org.openjdk.jmh.annotations.OutputTimeUnit;
import org.openjdk.jmh.annotations.Scope;
import org.openjdk.jmh.annotations.State;
import org.openjdk.jmh.infra.Blackhole;

/** The same Math.log call, measured five ways with JMH. */
@State(Scope.Thread)
@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.NANOSECONDS)
public class DeadCodeBench {
  static final double CONSTANT = Math.PI;
  double x = Math.PI;

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
    return Math.log(x);              // JMH consumes return values
  }

  @Benchmark
  public void blackhole(Blackhole bh) {
    bh.consume(Math.log(x));
  }

  @Benchmark
  public double constant() {
    return Math.log(CONSTANT);       // may be folded at compile time
  }
}
