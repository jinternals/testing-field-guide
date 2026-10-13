package shop.batch;

import static org.assertj.core.api.Assertions.assertThat;

import java.math.BigDecimal;
import org.junit.jupiter.api.Test;
import shop.cache.Price;

/** The processor is plain Java: test it without Batch. */
class ToPaiseTest {
  ToPaise toPaise = new ToPaise();

  @Test
  void convertsRupeesToPaise() {
    var line = new PriceLine("book-2",
        new BigDecimal("1299.50"));
    assertThat(toPaise.process(line))
        .isEqualTo(new Price("book-2", 129_950));
  }

  @Test
  void filtersNegativePrices() {
    var line = new PriceLine("pen-1", new BigDecimal("-5.00"));
    assertThat(toPaise.process(line)).isNull();
  }
}
