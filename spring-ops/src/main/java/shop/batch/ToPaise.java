package shop.batch;

import java.math.BigDecimal;
import org.springframework.batch.infrastructure.item.ItemProcessor;
import shop.cache.Price;

/** Rupees to paise; a negative price is filtered (null). */
public class ToPaise
    implements ItemProcessor<PriceLine, Price> {
  @Override
  public Price process(PriceLine line) {
    if (line.rupees().signum() < 0) {
      return null;
    }
    BigDecimal paise = line.rupees().movePointRight(2);
    return new Price(line.sku(), paise.longValueExact());
  }
}
