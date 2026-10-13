package shop;

import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;
import java.io.IOException;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;

/** A tiny JSON API on the JDK's built-in HTTP server: GET /orders/{id}. */
public class OrderApi {
  private final OrderRepository repository;
  private HttpServer server;

  public OrderApi(OrderRepository repository) { this.repository = repository; }

  public int start() throws IOException {
    // port 0 = let the OS pick any free port
    server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
    server.createContext("/orders/", this::handle);
    server.start();
    return server.getAddress().getPort();
  }

  public void stop() { server.stop(0); }

  private void handle(HttpExchange ex) throws IOException {
    if (!ex.getRequestMethod().equals("GET")) {
      ex.getResponseHeaders().set("Allow", "GET");
      send(ex, 405, "{\"error\":\"method not allowed\"}");
      return;
    }
    String id = ex.getRequestURI().getPath().substring("/orders/".length());
    var order = repository.findById(id);
    if (order.isEmpty()) {
      send(ex, 404, "{\"error\":\"order not found\"}");
      return;
    }
    Order o = order.get();
    send(ex, 200, "{\"id\":\"%s\",\"total\":\"%s\",\"items\":%d}"
        .formatted(o.id(), o.total().amount(), o.items().size()));
  }

  private static void send(HttpExchange ex, int status, String json) throws IOException {
    byte[] body = json.getBytes(StandardCharsets.UTF_8);
    ex.getResponseHeaders().set("Content-Type", "application/json");
    ex.sendResponseHeaders(status, body.length);
    try (var out = ex.getResponseBody()) { out.write(body); }
  }
}
