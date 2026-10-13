package shop;

import static org.assertj.core.api.Assertions.assertThat;

import java.net.URI;
import java.net.http.*;
import org.junit.jupiter.api.*;

class OrderMethodsIT extends SharedApi {
  @BeforeAll static void hello() {
    log("OrderMethodsIT uses " + BASE_URL);
  }

  @Test void deleteIs405WithAllow() throws Exception {
    var req = HttpRequest.newBuilder(URI.create(BASE_URL + "/orders/x"))
        .DELETE().build();
    var res = HTTP.send(req, HttpResponse.BodyHandlers.ofString());
    assertThat(res.statusCode()).isEqualTo(405);
    assertThat(res.headers().firstValue("Allow")).hasValue("GET");
  }
}
