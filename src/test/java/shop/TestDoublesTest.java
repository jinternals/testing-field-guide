package shop;

import static org.assertj.core.api.Assertions.*;

import java.time.Clock;
import java.util.*;
import org.junit.jupiter.api.Test;

/** The five kinds of test double, hand-written — no library needed. */
class TestDoublesTest {

  // DUMMY: passed in to satisfy a parameter, never used
  EmailSender dummyEmail = (to, subject, body) -> {
    throw new AssertionError("not used");
  };

  // STUB: returns canned answers
  PaymentGateway alwaysApproves = (customer, amount) -> "PAY-1";

  // SPY: a stub that also records how it was called
  static class SpyEmailSender implements EmailSender {
    final List<String> sentTo = new ArrayList<>();
    @Override public void send(String to, String subject, String body) {
      sentTo.add(to);
    }
  }

  // FAKE: a real but simplified implementation (a map instead of a DB)
  OrderRepository fakeRepo = new InMemoryOrderRepository();

  List<Item> pens = List.of(new Item("PEN", Money.of("50"), 2));

  OrderService serviceWith(EmailSender email) {
    return new OrderService(fakeRepo, alwaysApproves, email,
        new DiscountPolicy(), Clock.systemUTC());
  }

  @Test
  void stubAndFakeLetUsCheckState() {
    var service = serviceWith(new SpyEmailSender());
    Order order = service.placeOrder("meera@example.com", pens);
    assertThat(fakeRepo.findById(order.id())).contains(order);  // state
  }

  @Test
  void spyLetsUsCheckBehaviour() {
    var spy = new SpyEmailSender();
    serviceWith(spy).placeOrder("meera@example.com", pens);
    assertThat(spy.sentTo)
        .containsExactly("meera@example.com");  // behaviour
  }

  @Test
  void dummyIsNeverTouchedWhenValidationFails() {
    var service = serviceWith(dummyEmail);
    assertThatIllegalArgumentException()
      .isThrownBy(() -> service.placeOrder("x@example.com", List.of()));
  }
}
