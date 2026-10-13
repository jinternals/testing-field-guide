package shop.junitext;

import static org.assertj.core.api.Assertions.assertThat;

import java.time.*;
import org.junit.jupiter.api.*;

@ShopTest
@FixedClock("2026-10-16T09:00:00Z")          // a Friday
class DeliveryDateTest {

  /** Ships in 2 working days; weekends don't count. */
  static LocalDate deliveryDate(Clock clock) {
    LocalDate day = LocalDate.now(clock);
    for (int left = 2; left > 0; ) {
      day = day.plusDays(1);
      if (day.getDayOfWeek().getValue() < 6) left--;
    }
    return day;
  }

  @Test
  void fridayOrderArrivesTuesday(Clock clock) {
    assertThat(deliveryDate(clock)).isEqualTo("2026-10-20");
  }

  @Test
  @FixedClock("2026-10-13T09:00:00Z")        // method wins: Tuesday
  void tuesdayOrderArrivesThursday(Clock clock, TestInfo info) {
    assertThat(deliveryDate(clock)).isEqualTo("2026-10-15");
    assertThat(info.getTags()).containsExactly("unit");
  }

  @RepeatedTest(3)
  void sameAnswerEveryTime(Clock clock, RepetitionInfo rep) {
    assertThat(deliveryDate(clock)).isEqualTo("2026-10-20");
    assertThat(rep.getTotalRepetitions()).isEqualTo(3);
  }
}
