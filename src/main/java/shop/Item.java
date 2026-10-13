package shop;

public record Item(String sku, Money price, int quantity) {
  public Item {
    if (quantity < 1) throw new IllegalArgumentException("quantity must be ≥ 1");
  }
  public Money total() { return price.times(quantity); }
}
