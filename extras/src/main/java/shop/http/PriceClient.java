package shop.http;

import io.github.resilience4j.retry.Retry;
import java.io.IOException;
import java.math.BigDecimal;
import java.net.URI;
import java.net.http.*;
import java.time.Duration;
import java.util.NoSuchElementException;
import java.util.regex.Pattern;

/** Calls another team's price service over HTTP. */
public class PriceClient {
  private static final Pattern PRICE =
      Pattern.compile("\"price\"\\s*:\\s*\"(\\d+\\.\\d{2})\"");

  private final HttpClient http = HttpClient.newHttpClient();
  private final URI baseUrl;
  private final Retry retry;

  public PriceClient(URI baseUrl, Retry retry) {
    this.baseUrl = baseUrl;
    this.retry = retry;
  }

  public BigDecimal priceOf(String sku) {
    return retry.executeSupplier(() -> fetch(sku));
  }

  private BigDecimal fetch(String sku) {
    var request = HttpRequest.newBuilder(
            baseUrl.resolve("/prices/" + sku))
        .timeout(Duration.ofMillis(500))  // never wait forever
        .build();
    HttpResponse<String> response;
    try {
      response = http.send(request,
          HttpResponse.BodyHandlers.ofString());
    } catch (IOException e) {             // timeouts included
      throw new UpstreamException("unreachable", e);
    } catch (InterruptedException e) {
      Thread.currentThread().interrupt();
      throw new IllegalStateException(e);
    }
    int status = response.statusCode();
    if (status == 404) throw new NoSuchElementException(sku);
    if (status >= 500) {
      throw new UpstreamException("HTTP " + status, null);
    }
    var m = PRICE.matcher(response.body());
    if (!m.find()) {
      throw new IllegalStateException("bad price JSON: "
          + response.body());
    }
    return new BigDecimal(m.group(1));
  }
}
