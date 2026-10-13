package shop.contract;

import au.com.dius.pact.provider.junit5.*;
import au.com.dius.pact.provider.junitsupport.*;
import au.com.dius.pact.provider.junitsupport.loader.PactFolder;
import org.junit.jupiter.api.*;
import org.junit.jupiter.api.extension.ExtendWith;

/**
 * Provider side: replays every consumer's recorded requests
 * against the real API and checks each response.
 */
@Provider("orders")
@PactFolder("target/pacts")      // in real life: a Pact Broker
class OrderStatusProviderPactIT {
  static OrderStatusApi api;

  @BeforeAll static void start() throws Exception {
    api = new OrderStatusApi();
  }

  @AfterAll static void stop() { api.close(); }

  @BeforeEach void target(PactVerificationContext context) {
    context.setTarget(
        new HttpTestTarget("localhost", api.port()));
  }

  @State("order ord-1 is paid")
  void orderIsPaid() { /* set up data; ours is fixed */ }

  @TestTemplate
  @ExtendWith(PactVerificationInvocationContextProvider.class)
  void honoursTheContract(PactVerificationContext context) {
    context.verifyInteraction();
  }
}
