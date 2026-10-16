package deep.jit;

import java.util.concurrent.TimeUnit;
import org.openjdk.jmh.annotations.Benchmark;
import org.openjdk.jmh.annotations.BenchmarkMode;
import org.openjdk.jmh.annotations.CompilerControl;
import org.openjdk.jmh.annotations.Fork;
import org.openjdk.jmh.annotations.Mode;
import org.openjdk.jmh.annotations.OutputTimeUnit;
import org.openjdk.jmh.annotations.Scope;
import org.openjdk.jmh.annotations.Setup;
import org.openjdk.jmh.annotations.State;

/**
 * What C2 does to calls and allocations: inlining, the
 * receiver types seen at a call site, and escape analysis.
 * JMH runs each benchmark in its own JVM, so each call site
 * is profiled only with the types its own benchmark uses.
 */
@State(Scope.Thread)
@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.NANOSECONDS)
public class InliningBench {
  interface Shape {
    int area();
  }

  static final class Square implements Shape {
    final int s = 3;
    public int area() { return s * s; }
  }

  static final class Rect implements Shape {
    final int w = 2, h = 5;
    public int area() { return w * h; }
  }

  static final class Tri implements Shape {
    final int b = 4, h = 3;
    public int area() { return b * h / 2; }
  }

  static final class Circle implements Shape {
    final int r = 2;
    public int area() { return 3 * r * r; }
  }

  static final class Point {
    final int x, y;
    Point(int x, int y) { this.x = x; this.y = y; }
  }

  Shape[] mono = new Shape[1024];
  Shape[] bi = new Shape[1024];
  Shape[] mega = new Shape[1024];
  int a = 3, b = 4;

  @Setup
  public void setup() {
    Shape[] four = {new Square(), new Rect(), new Tri(),
        new Circle()};
    for (int i = 0; i < 1024; i++) {
      mono[i] = four[0];
      bi[i] = four[i % 2];
      mega[i] = four[i % 4];
    }
  }

  // ---- inlining: the same tiny method, inlined or not
  static int add(int x, int y) { return x + y; }

  @CompilerControl(CompilerControl.Mode.DONT_INLINE)
  static int addNotInlined(int x, int y) { return x + y; }

  @Benchmark
  public int callInlined() { return add(a, b); }

  @Benchmark
  public int callNotInlined() { return addNotInlined(a, b); }

  // ---- one call site, 1, 2 or 4 receiver types
  static int sum(Shape[] shapes) {
    int t = 0;
    for (Shape s : shapes) {
      t += s.area();                   // the profiled call site
    }
    return t;
  }

  @Benchmark
  public int types1() { return sum(mono); }

  @Benchmark
  public int types2() { return sum(bi); }

  @Benchmark
  public int types4() { return sum(mega); }

  // ---- escape analysis: a Point that never leaves the method
  @Benchmark
  public int allocation() {
    Point p = new Point(a, b);
    return p.x + p.y;
  }

  @Benchmark
  @Fork(jvmArgsAppend = "-XX:-DoEscapeAnalysis")
  public int allocationNoEscapeAnalysis() {
    Point p = new Point(a, b);
    return p.x + p.y;
  }
}
