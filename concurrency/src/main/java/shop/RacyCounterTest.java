package shop;

import static org.openjdk.jcstress.annotations.Expect.ACCEPTABLE;
import static org.openjdk.jcstress.annotations.Expect.ACCEPTABLE_INTERESTING;

import org.openjdk.jcstress.annotations.Actor;
import org.openjdk.jcstress.annotations.Arbiter;
import org.openjdk.jcstress.annotations.JCStressTest;
import org.openjdk.jcstress.annotations.Outcome;
import org.openjdk.jcstress.annotations.State;
import org.openjdk.jcstress.infra.results.I_Result;

/** Two threads each do count++ once. Is the result always 2? */
@JCStressTest
@Outcome(id = "2", expect = ACCEPTABLE, desc = "both counted")
@Outcome(id = "1", expect = ACCEPTABLE_INTERESTING,
    desc = "lost update: count++ is read, add, write")
@State
public class RacyCounterTest {
  int count;

  @Actor
  public void first() {
    count++;
  }

  @Actor
  public void second() {
    count++;
  }

  @Arbiter
  public void result(I_Result r) {
    r.r1 = count;
  }
}
