package shop;

import static org.assertj.core.api.Assertions.*;
import static org.mockito.Mockito.*;

import java.util.*;
import org.junit.jupiter.api.Test;
import org.mockito.MockedStatic;

class MockitoFeaturesTest {

  @Test
  void consecutiveAnswersForRetries() {
    PaymentGateway gateway = mock(PaymentGateway.class);
    when(gateway.charge(any(), any()))
      .thenThrow(new PaymentDeclinedException("timeout"))
      .thenReturn("PAY-2");

    Money one = Money.of("1");
    assertThatThrownBy(() -> gateway.charge("a@example.com", one));
    assertThat(gateway.charge("a@example.com", one)).isEqualTo("PAY-2");
    verify(gateway, times(2)).charge(any(), any());
  }

  @Test
  void spyWrapsARealObject() {
    List<String> list = spy(new ArrayList<>());
    list.add("one");
    // on spies use doReturn: when(list.size()) calls the real method
    doReturn(100).when(list).size();

    assertThat(list.size()).isEqualTo(100);
    assertThat(list.get(0)).isEqualTo("one");  // real behaviour kept
    verify(list).add("one");
  }

  @Test
  void mockStaticIsScopedToTheTryBlock() {
    UUID fixed = UUID.fromString("0-0-0-0-42");
    try (MockedStatic<UUID> uuid =
             mockStatic(UUID.class, CALLS_REAL_METHODS)) {
      uuid.when(UUID::randomUUID).thenReturn(fixed);
      assertThat(UUID.randomUUID()).isEqualTo(fixed);
    }
    assertThat(UUID.randomUUID()).isNotEqualTo(fixed); // real again
  }

  @Test
  void finalClassesCanBeMockedByDefault() {
    DiscountPolicy policy = mock(DiscountPolicy.class); // final class
    when(policy.percentFor(any())).thenReturn(50);
    assertThat(policy.percentFor(Money.of("10"))).isEqualTo(50);
  }
}
