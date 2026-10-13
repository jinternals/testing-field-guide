package shop.http;

import io.github.resilience4j.retry.*;
import java.time.Duration;

public final class Retries {
  private Retries() {}

  /** 3 attempts, 100 ms apart, only for retryable failures. */
  public static Retry forPrices() {
    return Retry.of("prices", RetryConfig.custom()
        .maxAttempts(3)
        .waitDuration(Duration.ofMillis(100))
        .retryExceptions(UpstreamException.class)
        .build());
  }
}
