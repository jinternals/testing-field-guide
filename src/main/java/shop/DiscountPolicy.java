package shop;

public final class DiscountPolicy {
  /** 0% below ₹1000, 5% from ₹1000, 10% from ₹5000. */
  public int percentFor(Money subtotal) {
    if (subtotal.compareTo(Money.of("5000")) >= 0) return 10;
    if (subtotal.compareTo(Money.of("1000")) >= 0) return 5;
    return 0;
  }
}
