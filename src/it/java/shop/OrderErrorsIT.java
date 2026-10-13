package shop;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.*;

class OrderErrorsIT extends SharedApi {
  @BeforeAll static void hello() {
    log("OrderErrorsIT uses " + BASE_URL);
  }

  @Test void errorBodyHasNoInternals() throws Exception {
    var res = get("/orders/..%2f..%2fetc%2fpasswd");
    assertThat(res.statusCode()).isEqualTo(404);
    assertThat(res.body()).isEqualTo("{\"error\":\"order not found\"}");
  }

  @Test void hugeIdIsJust404() throws Exception {
    assertThat(get("/orders/" + "x".repeat(5_000)).statusCode())
        .isEqualTo(404);
  }
}
