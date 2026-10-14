package shop;

import static org.openjdk.jcstress.annotations.Expect.ACCEPTABLE;
import static org.openjdk.jcstress.annotations.Expect.FORBIDDEN;

import org.openjdk.jcstress.annotations.Actor;
import org.openjdk.jcstress.annotations.JCStressTest;
import org.openjdk.jcstress.annotations.Outcome;
import org.openjdk.jcstress.annotations.State;
import org.openjdk.jcstress.infra.results.II_Result;

/** The same with volatile: 0, 0 is now forbidden. */
@JCStressTest
@Outcome(id = {"1, 0", "0, 1", "1, 1"}, expect = ACCEPTABLE,
    desc = "some interleaving of the four steps")
@Outcome(id = "0, 0", expect = FORBIDDEN,
    desc = "both read before either write was visible")
@State
public class StoreBufferingVolatileTest {
  volatile int x;
  volatile int y;

  @Actor
  public void first(II_Result r) {
    x = 1;
    r.r1 = y;
  }

  @Actor
  public void second(II_Result r) {
    y = 1;
    r.r2 = x;
  }
}
