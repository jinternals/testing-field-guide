package shop;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;

/** 100% line + branch coverage, yet the bug survives. */
class WeakDiscountPolicyTest {
  DiscountPolicy policy = new DiscountPolicy();

  @Test void small() {
    assertEquals(0, policy.percentFor(Money.of("500")));
  }
  @Test void medium() {
    assertEquals(5, policy.percentFor(Money.of("2000")));
  }
  @Test void large() {
    assertEquals(10, policy.percentFor(Money.of("6000")));
  }
}
