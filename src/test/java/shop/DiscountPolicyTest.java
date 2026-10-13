package shop;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;

class DiscountPolicyTest {

  private final DiscountPolicy policy = new DiscountPolicy();

  @ParameterizedTest(name = "₹{0} → {1}% off",
                     quoteTextArguments = false)
  @CsvSource({
    "0,       0",
    "999.99,  0",  // just below the first boundary
    "1000,    5",  // on the boundary
    "1000.01, 5",
    "4999.99, 5",
    "5000,   10",  // on the second boundary
    "250000, 10"
  })
  void percentForSubtotal(String subtotal, int expectedPercent) {
    assertEquals(expectedPercent, policy.percentFor(Money.of(subtotal)));
  }
}
