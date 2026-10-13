package shop;

import static org.openjdk.jcstress.annotations.Expect.ACCEPTABLE;
import static org.openjdk.jcstress.annotations.Expect.FORBIDDEN;

import java.util.concurrent.atomic.AtomicInteger;
import org.openjdk.jcstress.annotations.Actor;
import org.openjdk.jcstress.annotations.Arbiter;
import org.openjdk.jcstress.annotations.JCStressTest;
import org.openjdk.jcstress.annotations.Outcome;
import org.openjdk.jcstress.annotations.State;
import org.openjdk.jcstress.infra.results.I_Result;

/** The fix. A lost update would now fail the run. */
@JCStressTest
@Outcome(id = "2", expect = ACCEPTABLE, desc = "both counted")
@Outcome(id = "1", expect = FORBIDDEN, desc = "lost update")
@State
public class AtomicCounterTest {
  final AtomicInteger count = new AtomicInteger();

  @Actor
  public void first() {
    count.incrementAndGet();
  }

  @Actor
  public void second() {
    count.incrementAndGet();
  }

  @Arbiter
  public void result(I_Result r) {
    r.r1 = count.get();
  }
}
