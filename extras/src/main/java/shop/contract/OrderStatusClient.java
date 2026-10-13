package shop.contract;

import java.io.IOException;
import java.net.URI;
import java.net.http.*;
import java.util.regex.Pattern;

/** The CONSUMER: only needs the order's status. */
public class OrderStatusClient {
  private static final Pattern STATUS =
      Pattern.compile("\"status\"\\s*:\\s*\"(\\w+)\"");
  private final HttpClient http = HttpClient.newHttpClient();
  private final URI baseUrl;

  public OrderStatusClient(URI baseUrl) {
    this.baseUrl = baseUrl;
  }

  public String statusOf(String orderId)
      throws IOException, InterruptedException {
    URI uri = baseUrl.resolve("/orders/" + orderId + "/status");
    var request = HttpRequest.newBuilder(uri).build();
    String body = http.send(request,
        HttpResponse.BodyHandlers.ofString()).body();
    var m = STATUS.matcher(body);
    if (!m.find()) throw new IllegalStateException(body);
    return m.group(1);
  }
}
