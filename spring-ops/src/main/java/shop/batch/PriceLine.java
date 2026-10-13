package shop.batch;

import java.math.BigDecimal;

/** One line of the supplier's CSV: sku,rupees */
public record PriceLine(String sku, BigDecimal rupees) {}
