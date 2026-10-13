package shop.observe;

import io.micrometer.core.instrument.Counter;
import io.micrometer.core.instrument.MeterRegistry;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class PaymentService {
  private static final Logger log =
      LoggerFactory.getLogger(PaymentService.class);
  static final long LIMIT_PAISE = 5_000_000;     // ₹50,000

  private final Counter declined;

  public PaymentService(MeterRegistry registry) {
    declined = Counter.builder("payments.declined")
        .tag("reason", "over_limit")
        .register(registry);
  }

  public boolean charge(String orderId, long amountPaise) {
    if (amountPaise > LIMIT_PAISE) {
      declined.increment();
      log.warn("Payment declined for order {}: over limit",
          orderId);
      return false;
    }
    log.info("Charged order {}", orderId);
    return true;
  }
}
