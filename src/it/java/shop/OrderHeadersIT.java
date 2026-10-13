package shop;

import static org.assertj.core.api.Assertions.assertThat;

import java.time.Instant;
import java.util.List;
import org.junit.jupiter.api.*;

class OrderHeadersIT extends SharedApi {
  @BeforeAll static void hello() {
    log("OrderHeadersIT uses " + BASE_URL);
  }

  @Test void jsonContentType() throws Exception {
    String id = uniqueId("headers");
    REPO.save(new Order(id, "ravi@example.com",
        List.of(new Item("PEN", Money.of("40"), 1)),
        Money.of("40"), Instant.EPOCH));
    assertThat(get("/orders/" + id).headers().firstValue("Content-Type"))
        .hasValue("application/json");
  }
}
