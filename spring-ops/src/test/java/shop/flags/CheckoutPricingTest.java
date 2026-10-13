package shop.flags;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;

/** Every flag is two code paths: test both, every build. */
class CheckoutPricingTest {
  @ParameterizedTest(name = "flag={0}, {1} items → {2}")
  @CsvSource({
      "false, 3, 100000",
      "true,  3,  90000",
      "true,  2, 100000"})
  void bulkDiscountFollowsTheFlag(boolean on, int items,
      long total) {
    var pricing = new CheckoutPricing(new Features(on));
    assertThat(pricing.total(100_000, items)).isEqualTo(total);
  }
}
