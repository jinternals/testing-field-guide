package shop.contract;

import com.sun.net.httpserver.HttpServer;
import java.io.IOException;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;

/**
 * The PROVIDER: GET /orders/{id}/status. -Dorders.v2=true
 * renames "status" to "state": the breaking change Pact catches.
 */
public class OrderStatusApi implements AutoCloseable {
  private final HttpServer server;

  public OrderStatusApi() throws IOException {
    boolean v2 = Boolean.getBoolean("orders.v2");
    server = HttpServer.create(
        new InetSocketAddress("127.0.0.1", 0), 0);
    server.createContext("/orders/", exchange -> {
      String path = exchange.getRequestURI().getPath();
      String id = path.split("/")[2];
      String body = """
          {"id":"%s","%s":"PAID","total":"1140.00"}"""
          .formatted(id, v2 ? "state" : "status");
      byte[] bytes = body.getBytes(StandardCharsets.UTF_8);
      exchange.getResponseHeaders()
          .set("Content-Type", "application/json");
      exchange.sendResponseHeaders(200, bytes.length);
      exchange.getResponseBody().write(bytes);
      exchange.close();
    });
    server.start();
  }

  public int port() { return server.getAddress().getPort(); }

  @Override public void close() { server.stop(0); }
}
