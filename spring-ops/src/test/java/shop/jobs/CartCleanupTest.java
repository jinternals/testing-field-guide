package shop.jobs;

import static org.assertj.core.api.Assertions.assertThat;

import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;
import org.junit.jupiter.api.Test;

/** The rule, without Spring or a scheduler: plain and fast. */
class CartCleanupTest {
  Instant now = Instant.parse("2026-10-13T10:00:00Z");
  CartStore carts = new CartStore();
  CartCleanup cleanup = new CartCleanup(carts,
      Clock.fixed(now, ZoneOffset.UTC));

  @Test
  void removesCartsUntouchedForMoreThan24Hours() {
    carts.touch("old", now.minus(Duration.ofHours(25)));
    carts.touch("fresh", now.minus(Duration.ofHours(1)));

    assertThat(cleanup.removeAbandoned()).isEqualTo(1);
    assertThat(carts.ids()).containsExactly("fresh");
  }

  @Test
  void exactly24HoursOldIsKept() {
    carts.touch("edge", now.minus(Duration.ofHours(24)));

    assertThat(cleanup.removeAbandoned()).isZero();
  }
}
