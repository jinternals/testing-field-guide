package shop;

import java.math.BigDecimal;

/** What the API returns: plain data, no lazy JPA proxies. */
public record OrderView(String reference, BigDecimal total, int lines) {
  static OrderView of(CustomerOrder o) {
    return new OrderView(o.getReference(), o.getTotal(), o.getLines().size());
  }
}
