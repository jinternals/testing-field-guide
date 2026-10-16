package deep.jit;

/**
 * Runs one call site with 1 receiver type and another with
 * 4, long enough for C2 to compile both. Started with
 * -XX:+PrintInlining, the JVM reports what it did with each.
 */
public final class CallSites {
  interface Shape {
    int area();
  }

  static final class A implements Shape {
    public int area() { return 1; }
  }

  static final class B implements Shape {
    public int area() { return 2; }
  }

  static final class C implements Shape {
    public int area() { return 3; }
  }

  static final class D implements Shape {
    public int area() { return 4; }
  }

  static int oneType(Shape[] s) {
    int t = 0;
    for (Shape x : s) {
      t += x.area();
    }
    return t;
  }

  static int fourTypes(Shape[] s) {
    int t = 0;
    for (Shape x : s) {
      t += x.area();
    }
    return t;
  }

  public static void main(String[] args) {
    Shape[] one = new Shape[1000];
    Shape[] four = new Shape[1000];
    Shape[] all = {new A(), new B(), new C(), new D()};
    for (int i = 0; i < 1000; i++) {
      one[i] = all[0];
      four[i] = all[i % 4];
    }
    long sink = 0;
    for (int i = 0; i < 50_000; i++) {
      sink += oneType(one) + fourTypes(four);
    }
    System.out.println("sink " + sink);
  }
}
