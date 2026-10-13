package shop.jobs;

import java.time.Clock;
import java.time.Duration;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

@Component
public class CartCleanup {
  static final Duration MAX_AGE = Duration.ofHours(24);
  private final CartStore carts;
  private final Clock clock;

  public CartCleanup(CartStore carts, Clock clock) {
    this.carts = carts;
    this.clock = clock;
  }

  /** The schedule is wiring; the rule is a plain method. */
  @Scheduled(fixedDelayString = "${shop.cleanup.every:PT10M}")
  public void scheduledRun() {
    removeAbandoned();
  }

  public int removeAbandoned() {
    return carts.removeTouchedBefore(clock.instant().minus(MAX_AGE));
  }
}
