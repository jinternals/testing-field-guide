package deep.gc;

import java.util.concurrent.TimeUnit;
import org.openjdk.jmh.annotations.Benchmark;
import org.openjdk.jmh.annotations.BenchmarkMode;
import org.openjdk.jmh.annotations.Mode;
import org.openjdk.jmh.annotations.OutputTimeUnit;
import org.openjdk.jmh.annotations.Scope;
import org.openjdk.jmh.annotations.Setup;
import org.openjdk.jmh.annotations.State;

/**
 * Reading and writing object references, run under several
 * collectors (-jvmArgs): each collector adds its own code,
 * a barrier, around reference loads and/or stores.
 */
@State(Scope.Thread)
@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.MICROSECONDS)
public class BarrierBench {
  static final class Box {
    Object ref;
    int value = 1;
  }

  Box[] boxes = new Box[4096];
  Object[] targets = new Object[4096];

  @Setup
  public void setup() {
    for (int i = 0; i < boxes.length; i++) {
      boxes[i] = new Box();
      targets[i] = new Object();
    }
  }

  /** 4,096 reference loads (and int reads through them). */
  @Benchmark
  public int loadRefs() {
    int t = 0;
    for (Box b : boxes) {
      t += b.value;
    }
    return t;
  }

  /** 4,096 reference stores into heap objects. */
  @Benchmark
  public void storeRefs() {
    for (int i = 0; i < boxes.length; i++) {
      boxes[i].ref = targets[(i + 1) & 4095];
    }
  }

  /** The same loop storing ints: no reference, no barrier. */
  @Benchmark
  public void storeInts() {
    for (int i = 0; i < boxes.length; i++) {
      boxes[i].value = i;
    }
  }
}
