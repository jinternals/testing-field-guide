package shop;

import static org.openjdk.jcstress.annotations.Expect.ACCEPTABLE;
import static org.openjdk.jcstress.annotations.Expect.ACCEPTABLE_INTERESTING;

import org.openjdk.jcstress.annotations.Actor;
import org.openjdk.jcstress.annotations.JCStressTest;
import org.openjdk.jcstress.annotations.Mode;
import org.openjdk.jcstress.annotations.Outcome;
import org.openjdk.jcstress.annotations.Signal;
import org.openjdk.jcstress.annotations.State;

/** Does a spinning thread see the flag another thread sets? */
@JCStressTest(Mode.Termination)
@Outcome(id = "TERMINATED", expect = ACCEPTABLE,
    desc = "saw it")
@Outcome(id = "STALE", expect = ACCEPTABLE_INTERESTING,
    desc = "spins forever")
@State
public class SpinTest {
  boolean ready;

  @Actor
  public void spin() {
    while (!ready) {
      // wait
    }
  }

  @Signal
  public void signal() {
    ready = true;
  }
}
