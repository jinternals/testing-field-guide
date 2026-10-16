package deep.jmm;

import java.lang.invoke.MethodHandles;
import java.lang.invoke.VarHandle;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import org.openjdk.jmh.annotations.Benchmark;
import org.openjdk.jmh.annotations.BenchmarkMode;
import org.openjdk.jmh.annotations.Mode;
import org.openjdk.jmh.annotations.OutputTimeUnit;
import org.openjdk.jmh.annotations.Scope;
import org.openjdk.jmh.annotations.State;

/** One thread, no contention: the cost of each access. */
@State(Scope.Thread)
@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.NANOSECONDS)
public class FenceBench {
  int plain;
  volatile int vol;
  int released;
  final AtomicInteger atomic = new AtomicInteger();
  final Object lock = new Object();
  int locked;

  static final VarHandle RELEASED;

  static {
    try {
      RELEASED = MethodHandles.lookup().findVarHandle(
          FenceBench.class, "released", int.class);
    } catch (ReflectiveOperationException e) {
      throw new ExceptionInInitializerError(e);
    }
  }

  @Benchmark
  public void plainStore() { plain++; }

  @Benchmark
  public void volatileStore() { vol = plain++; }

  @Benchmark
  public void releaseStore() {
    RELEASED.setRelease(this, plain++);
  }

  @Benchmark
  public int plainLoad() { return plain; }

  @Benchmark
  public int volatileLoad() { return vol; }

  @Benchmark
  public int atomicIncrement() {
    return atomic.incrementAndGet();
  }

  @Benchmark
  public void synchronizedIncrement() {
    synchronized (lock) {
      locked++;
    }
  }
}
