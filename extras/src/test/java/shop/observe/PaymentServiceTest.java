package shop.observe;

import static org.assertj.core.api.Assertions.*;

import ch.qos.logback.classic.*;
import ch.qos.logback.classic.spi.ILoggingEvent;
import ch.qos.logback.core.read.ListAppender;
import io.micrometer.core.instrument.simple.SimpleMeterRegistry;
import org.junit.jupiter.api.*;
import org.slf4j.LoggerFactory;

/** Logs and metrics are behaviour too: alerts depend on them. */
class PaymentServiceTest {
  SimpleMeterRegistry registry = new SimpleMeterRegistry();
  ListAppender<ILoggingEvent> logs = new ListAppender<>();
  Logger logger = (Logger) LoggerFactory.getLogger(PaymentService.class);

  @BeforeEach void captureLogs() { logs.start(); logger.addAppender(logs); }
  @AfterEach void release() { logger.detachAppender(logs); }

  @Test
  void declinedPaymentIsLoggedAndCounted() {
    var payments = new PaymentService(registry);

    assertThat(payments.charge("ord-9", 6_000_000)).isFalse();

    assertThat(logs.list)
        .extracting(ILoggingEvent::getLevel,
                    ILoggingEvent::getFormattedMessage)
        .containsExactly(tuple(Level.WARN,
            "Payment declined for order ord-9: over limit"));
    assertThat(registry.get("payments.declined")
        .tag("reason", "over_limit").counter().count())
        .isEqualTo(1.0);
  }

  @Test
  void normalPaymentRaisesNoAlarm() {
    var payments = new PaymentService(registry);

    assertThat(payments.charge("ord-1", 100_000)).isTrue();

    assertThat(logs.list).noneMatch(e -> e.getLevel() == Level.WARN);
    assertThat(registry.get("payments.declined").counter().count())
        .isZero();
  }
}
