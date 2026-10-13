package shop;

import static org.junit.jupiter.api.Assertions.*;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

class MoneyTest {

  @Test
  @DisplayName("10% off ₹999.99 rounds half-up to ₹899.99")
  void percentOffRoundsHalfUp() {
    Money price = Money.of("999.99");  // Arrange

    Money discounted = price.percentOff(10);  // Act

    assertEquals(Money.of("899.99"), discounted); // Assert
  }

  @Test
  void rejectsNegativeAmounts() {
    var error = assertThrows(IllegalArgumentException.class,
        () -> Money.of("-1"));
    assertEquals("negative amount: -1", error.getMessage());
  }

  @Test
  void addsAndMultiplies() {
    Money m = Money.of("12.50");
    assertAll("arithmetic",
        () -> assertEquals(Money.of("25.00"), m.plus(m)),
        () -> assertEquals(Money.of("37.50"), m.times(3)),
        () -> assertEquals("₹12.50", m.toString()));
  }
}
