package shop;

import static org.assertj.core.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

import java.time.*;
import java.util.List;
import org.junit.jupiter.api.*;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.*;
import org.mockito.junit.jupiter.MockitoExtension;

@ExtendWith(MockitoExtension.class)
class OrderServiceTest {

  @Mock OrderRepository repository;
  @Mock PaymentGateway payments;
  @Mock EmailSender email;
  @Captor ArgumentCaptor<Order> savedOrder;

  Clock clock = Clock.fixed(Instant.parse("2026-10-13T10:00:00Z"),
                            ZoneOffset.UTC);
  OrderService service;

  @BeforeEach
  void setUp() {
    service = new OrderService(repository, payments, email,
        new DiscountPolicy(), clock);
  }

  @Test
  void chargesDiscountedTotalSavesAndEmails() {
    when(repository.save(any())).thenAnswer(c -> c.getArgument(0));

    Order order = service.placeOrder("asha@example.com",
        List.of(new Item("BOOK", Money.of("600"), 2))); // ₹1200 → 5%

    assertThat(order.total()).isEqualTo(Money.of("1140"));
    verify(payments).charge("asha@example.com", Money.of("1140"));
    verify(repository).save(savedOrder.capture());
    assertThat(savedOrder.getValue().placedAt())
        .isEqualTo(clock.instant());
    verify(email).send(eq("asha@example.com"), eq("Order confirmed"),
        contains("₹1140.00"));
  }

  @Test
  void declinedPaymentSavesNothingAndSendsNoEmail() {
    when(payments.charge(anyString(), any()))
      .thenThrow(new PaymentDeclinedException("card expired"));

    assertThatThrownBy(() -> service.placeOrder("asha@example.com",
        List.of(new Item("PEN", Money.of("50"), 1))))
      .isInstanceOf(PaymentDeclinedException.class)
      .hasMessage("card expired");

    verifyNoInteractions(repository, email);
  }

  @Test
  void chargesBeforeSaving() {
    when(repository.save(any())).thenAnswer(c -> c.getArgument(0));

    service.placeOrder("asha@example.com",
        List.of(new Item("PEN", Money.of("50"), 1)));

    InOrder inOrder = inOrder(payments, repository, email);
    inOrder.verify(payments).charge(any(), any());
    inOrder.verify(repository).save(any());
    inOrder.verify(email).send(any(), any(), any());
  }

  @Test
  void emptyOrderIsRejectedEarly() {
    assertThatIllegalArgumentException()
      .isThrownBy(() -> service.placeOrder("a@example.com", List.of()))
      .withMessage("order has no items");
    verifyNoInteractions(payments, repository, email);
  }
}
