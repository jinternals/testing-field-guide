package shop;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

@ExtendWith(MockitoExtension.class)
class FailingExamplesTest {
  @Mock PaymentGateway payments;
  @Mock EmailSender email;

  @Test void a_assertEquals() {
    assertEquals(Money.of("900.00"), Money.of("999.99").percentOff(10));
  }

  @Test void b_assertAll() {
    Money m = Money.of("12.50");
    assertAll("arithmetic",
        () -> assertEquals(Money.of("25.00"), m.times(3)),
        () -> assertEquals("Rs 12.50", m.toString()));
  }

  @Test void c_assertj() {
    org.assertj.core.api.Assertions.assertThat(List.of("PEN", "BOOK", "TV"))
      .containsExactly("PEN", "TV", "BOOK");
  }

  @Test void d_unnecessaryStubbing() {
    when(payments.charge(any(), any())).thenReturn("PAY-1");  // never used
    new DiscountPolicy().percentFor(Money.of("10"));
  }

  @Test void e_argumentMismatch() {
    email.send("asha@example.com", "Order confirmed", "Total: ₹1140.00");
    verify(email).send("asha@example.com", "Order confirmed", "Total: ₹1200.00");
  }

  @Test void f_wantedButNotInvoked() {
    verify(payments).charge(any(), any());
  }
}
