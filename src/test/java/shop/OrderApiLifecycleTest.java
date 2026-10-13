package shop;

import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.net.ConnectException;
import java.net.Socket;
import org.junit.jupiter.api.Test;

/** Kills the mutant PIT found: deleting server.stop(0). */
class OrderApiLifecycleTest {

  @Test void stopReleasesThePort() throws Exception {
    var api = new OrderApi(new InMemoryOrderRepository());
    int port = api.start();

    api.stop();

    assertThatThrownBy(() -> new Socket("127.0.0.1", port).close())
        .isInstanceOf(ConnectException.class);  // port is free
  }
}
