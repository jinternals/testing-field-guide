package shop;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.BDDMockito.*;

import java.time.Clock;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

@ExtendWith(MockitoExtension.class)
class OrderServiceBddTest {
  @Mock OrderRepository repository;
  @Mock PaymentGateway payments;
  @Mock EmailSender email;

  @Test
  void bigOrderGetsTenPercentOff() {
    // given
    given(repository.save(any())).willAnswer(c -> c.getArgument(0));
    var service = new OrderService(repository, payments, email,
        new DiscountPolicy(), Clock.systemUTC());

    // when
    Order order = service.placeOrder("ravi@example.com",
        List.of(new Item("TV", Money.of("5000"), 1)));

    // then
    assertThat(order.total()).isEqualTo(Money.of("4500"));
    then(payments).should().charge("ravi@example.com", Money.of("4500"));
    then(email).should(times(1)).send(any(), any(), any());
  }
}
