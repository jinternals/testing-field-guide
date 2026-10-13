package shop.jobs;

import static org.awaitility.Awaitility.await;

import java.time.Duration;
import java.time.Instant;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

/** The wiring: the schedule really fires (here every 0.2 s). */
@SpringBootTest(properties = {"shop.cleanup.every=PT0.2S",
    "spring.cache.type=none"})
class CartCleanupScheduleIT {
  @Autowired CartStore carts;

  @Test
  void theScheduledRunRemovesAbandonedCarts() {
    carts.touch("abandoned", Instant.EPOCH);

    await().atMost(Duration.ofSeconds(5))
        .until(() -> carts.ids().isEmpty());
  }
}
