package shop;

import static org.assertj.core.api.Assertions.*;

import java.util.stream.Stream;
import org.junit.jupiter.api.*;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.*;

@DisplayName("Item")
class ItemTest {

  @Nested @DisplayName("when quantity is valid")
  class ValidQuantity {
    @ParameterizedTest(name = "{0} × ₹{1} = ₹{2}",
             quoteTextArguments = false)
    @MethodSource("shop.ItemTest#totals")
    void totalIsPriceTimesQty(int qty, String price, String total) {
      assertThat(new Item("SKU-1", Money.of(price), qty).total())
        .isEqualTo(Money.of(total));
    }
  }

  @Nested @DisplayName("when quantity is invalid")
  class InvalidQuantity {
    @ParameterizedTest(name = "quantity {0} is rejected")
    @ValueSource(ints = {0, -1, Integer.MIN_VALUE})
    void rejected(int qty) {
      assertThatThrownBy(() -> new Item("SKU-1", Money.of("10"), qty))
        .isInstanceOf(IllegalArgumentException.class)
        .hasMessageContaining("quantity");
    }
  }

  static Stream<Arguments> totals() {
    return Stream.of(
      Arguments.of(1, "10", "10"),
      Arguments.of(3, "19.99", "59.97"),
      Arguments.of(1000, "0.01", "10"));
  }
}
