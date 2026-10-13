package shop.contract;

import static org.assertj.core.api.Assertions.assertThat;

import au.com.dius.pact.consumer.MockServer;
import au.com.dius.pact.consumer.dsl.*;
import au.com.dius.pact.consumer.junit5.*;
import au.com.dius.pact.core.model.V4Pact;
import au.com.dius.pact.core.model.annotations.Pact;
import java.net.URI;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;

/**
 * Consumer side: records what the shop needs from the order
 * service into target/pacts/shop-orders.json.
 */
@ExtendWith(PactConsumerTestExt.class)
@PactTestFor(providerName = "orders")
class OrderStatusConsumerPactTest {

  @Pact(consumer = "shop", provider = "orders")
  V4Pact paidOrder(PactDslWithProvider builder) {
    return builder
        .given("order ord-1 is paid")
        .uponReceiving("a status request for ord-1")
          .path("/orders/ord-1/status").method("GET")
        .willRespondWith()
          .status(200)
          .body(new PactDslJsonBody()
              .stringValue("id", "ord-1")
              .stringType("status", "PAID"))   // any string
        .toPact(V4Pact.class);
  }

  @Test
  void readsTheStatus(MockServer server) throws Exception {
    var client =
        new OrderStatusClient(URI.create(server.getUrl()));

    assertThat(client.statusOf("ord-1")).isEqualTo("PAID");
  }
}
