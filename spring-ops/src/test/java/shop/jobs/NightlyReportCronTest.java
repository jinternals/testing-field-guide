package shop.jobs;

import static org.assertj.core.api.Assertions.assertThat;

import java.time.LocalDateTime;
import org.junit.jupiter.api.Test;
import org.springframework.scheduling.support.CronExpression;

/** A cron expression is code: test when it fires. */
class NightlyReportCronTest {
  CronExpression cron = CronExpression.parse(NightlyReport.CRON);

  @Test
  void fridayNightRunsNextOnMondayAt2() {
    var friday = LocalDateTime.parse("2026-10-16T22:00");
    assertThat(cron.next(friday))
        .isEqualTo(LocalDateTime.parse("2026-10-19T02:00"));
  }

  @Test
  void exactly2amRunsTheNextWeekdayNotAgain() {
    var tuesday2am = LocalDateTime.parse("2026-10-13T02:00");
    assertThat(cron.next(tuesday2am))
        .isEqualTo(LocalDateTime.parse("2026-10-14T02:00"));
  }
}
