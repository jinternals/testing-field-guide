package shop;

import static org.assertj.core.api.Assertions.assertThat;

import java.net.URI;
import java.net.http.*;
import java.time.Instant;
import java.util.List;
import org.junit.jupiter.api.*;

/** Integration test: a real HTTP server on a free port + a real client. */
class OrderApiTest {
  static final OrderRepository repo = new InMemoryOrderRepository();
  static final OrderApi api = new OrderApi(repo);
  static final HttpClient http = HttpClient.newHttpClient();
  static String baseUrl;

  @BeforeAll static void startServer() throws Exception {
    baseUrl = "http://127.0.0.1:" + api.start();
    repo.save(new Order("ord-1", "asha@example.com",
        List.of(new Item("BOOK", Money.of("600"), 2)),
        Money.of("1140"), Instant.EPOCH));
  }

  @AfterAll static void stopServer() { api.stop(); }

  HttpResponse<String> send(String method, String path)
      throws Exception {
    var request = HttpRequest.newBuilder(URI.create(baseUrl + path))
        .method(method, HttpRequest.BodyPublishers.noBody()).build();
    return http.send(request, HttpResponse.BodyHandlers.ofString());
  }

  @Test void existingOrderReturns200WithJson() throws Exception {
    var res = send("GET", "/orders/ord-1");
    assertThat(res.statusCode()).isEqualTo(200);
    assertThat(res.headers().firstValue("Content-Type"))
      .hasValue("application/json");
    assertThat(res.body())
      .isEqualTo("{\"id\":\"ord-1\",\"total\":\"1140.00\",\"items\":1}");
  }

  @Test void unknownOrderReturns404() throws Exception {
    assertThat(send("GET", "/orders/nope").statusCode()).isEqualTo(404);
  }

  @Test void wrongMethodReturns405WithAllowHeader() throws Exception {
    var res = send("DELETE", "/orders/ord-1");
    assertThat(res.statusCode()).isEqualTo(405);
    assertThat(res.headers().firstValue("Allow")).hasValue("GET");
  }

  @Test void pathTricksAreJustNotFound() throws Exception {
    for (String path : List.of("/orders/..%2f..%2fetc%2fpasswd",
                               "/orders/ord-1'%20OR%20'1'='1",
                               "/orders/" + "x".repeat(5_000))) {
      var res = send("GET", path);
      assertThat(res.statusCode()).isEqualTo(404);
      assertThat(res.body())               // no stack traces, no internals
          .isEqualTo("{\"error\":\"order not found\"}");
    }
  }
}
