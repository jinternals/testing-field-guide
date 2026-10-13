package shop.synthetic;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;

/**
 * What a user does, run against a deployed instance:
 * java -cp classes shop.synthetic.SyntheticCheck URL
 * The same class runs in a test against the app on a random port.
 */
public final class SyntheticCheck {
  private static final HttpClient HTTP = HttpClient.newBuilder()
      .connectTimeout(Duration.ofSeconds(3)).build();

  public static List<String> run(URI base) {
    List<String> failures = new ArrayList<>();
    check(failures, base, "/actuator/health", "\"UP\"");
    check(failures, base, "/prices/book-1", "\"paise\"");
    return failures;
  }

  private static void check(List<String> failures, URI base,
      String path, String mustContain) {
    long t0 = System.nanoTime();
    String result;
    try {
      var req = HttpRequest.newBuilder(base.resolve(path))
          .timeout(Duration.ofSeconds(5)).build();
      var res = HTTP.send(req, HttpResponse.BodyHandlers.ofString());
      boolean ok = res.statusCode() == 200
          && res.body().contains(mustContain);
      result = (ok ? "✔ " : "✘ ") + path + "  " + res.statusCode();
    } catch (Exception e) {
      result = "✘ " + path + "  " + e.getClass().getSimpleName();
    }
    long ms = (System.nanoTime() - t0) / 1_000_000;
    System.out.println(result + "  " + ms + " ms");
    if (result.startsWith("✘")) {
      failures.add(result);
    }
  }

  public static void main(String[] args) {
    List<String> failures = run(URI.create(args[0]));
    System.out.println(failures.isEmpty() ? "synthetic check passed"
        : "synthetic check FAILED: " + failures.size());
    System.exit(failures.isEmpty() ? 0 : 1);
  }

  private SyntheticCheck() {
  }
}
