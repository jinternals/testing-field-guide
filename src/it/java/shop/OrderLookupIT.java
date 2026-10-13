package shop;

import static org.assertj.core.api.Assertions.assertThat;

import java.time.Instant;
import java.util.List;
import org.junit.jupiter.api.*;

class OrderLookupIT extends SharedApi {
  @BeforeAll static void hello() {
    log("OrderLookupIT uses " + BASE_URL);
  }

  @Test void savedOrderIsServed() throws Exception {
    String id = uniqueId("lookup");
    REPO.save(new Order(id, "asha@example.com",
        List.of(new Item("BOOK", Money.of("600"), 2)),
        Money.of("1140"), Instant.EPOCH));
    var res = get("/orders/" + id);
    assertThat(res.statusCode()).isEqualTo(200);
    assertThat(res.body()).contains("\"total\":\"1140.00\"");
  }

  @Test void unknownOrderIs404() throws Exception {
    assertThat(get("/orders/" + uniqueId("missing")).statusCode())
        .isEqualTo(404);
  }
}
