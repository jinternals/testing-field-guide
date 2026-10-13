package shop;

import java.math.BigDecimal;
import java.math.RoundingMode;

/** Immutable money value in rupees, always 2 decimal places. */
public record Money(BigDecimal amount) implements Comparable<Money> {
  public Money {
    if (amount.signum() < 0)
      throw new IllegalArgumentException("negative amount: " + amount);
    amount = amount.setScale(2, RoundingMode.HALF_UP);
  }
  public static Money of(String value) { return new Money(new BigDecimal(value)); }
  public Money plus(Money other) { return new Money(amount.add(other.amount)); }
  public Money times(int qty) {
    return new Money(amount.multiply(BigDecimal.valueOf(qty)));
  }
  public Money percentOff(int percent) {
    BigDecimal factor = BigDecimal.valueOf(100 - percent).movePointLeft(2);
    return new Money(amount.multiply(factor));
  }
  @Override public int compareTo(Money o) { return amount.compareTo(o.amount); }
  @Override public String toString() { return "₹" + amount; }
}
