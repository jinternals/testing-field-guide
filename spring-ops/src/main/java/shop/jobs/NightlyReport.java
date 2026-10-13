package shop.jobs;

import java.util.concurrent.atomic.AtomicInteger;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

@Component
public class NightlyReport {
  /** 02:00 on weekdays, India time, whatever the server's zone. */
  public static final String CRON = "0 0 2 * * MON-FRI";
  public static final String ZONE = "Asia/Kolkata";
  private final AtomicInteger runs = new AtomicInteger();

  @Scheduled(cron = CRON, zone = ZONE)
  public void run() {
    runs.incrementAndGet();
  }

  public int runs() {
    return runs.get();
  }
}
