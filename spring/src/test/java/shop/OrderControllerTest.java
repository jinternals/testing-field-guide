package shop;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.BDDMockito.given;

import java.math.BigDecimal;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.http.HttpStatus;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.assertj.MockMvcTester;

/** Controller slice: web layer only; the service is a mock. */
@WebMvcTest(OrderController.class)
class OrderControllerTest {
  @Autowired MockMvcTester mvc;       // AssertJ-style MockMvc
  @MockitoBean OrderService orders;   // replaces the real bean

  @Test
  void knownOrderIsReturnedAsJson() {
    given(orders.find("A-1")).willReturn(Optional.of(
        new OrderView("A-1", new BigDecimal("1140.00"), 2)));

    assertThat(mvc.get().uri("/orders/A-1"))
        .hasStatusOk()
        .bodyJson().isLenientlyEqualTo("""
            {"reference":"A-1","total":1140.00,"lines":2}""");
  }

  @Test
  void unknownOrderIs404() {
    given(orders.find("nope")).willReturn(Optional.empty());

    assertThat(mvc.get().uri("/orders/nope"))
        .hasStatus(HttpStatus.NOT_FOUND);
  }
}
