package shop.flags;

/** Registered by FeatureConfig. */
public class CheckoutPricing {
  private final Features features;

  public CheckoutPricing(Features features) {
    this.features = features;
  }

  public long total(long subtotalPaise, int items) {
    if (features.bulkDiscount() && items >= 3) {
      return subtotalPaise * 90 / 100;
    }
    return subtotalPaise;
  }
}
