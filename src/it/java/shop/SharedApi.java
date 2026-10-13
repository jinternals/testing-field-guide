package shop;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.net.URI;
import java.net.http.*;

/**
 * Singleton resource: started once per JVM, the first time any IT
 * class touches it, and shared by every IT class in that JVM.
 * Same shape as a singleton Testcontainers container.
 */
abstract class SharedApi {
  // Maven: set from ${surefire.forkNumber}; Gradle: worker id
  static final String FORK = System.getProperty("fork",
      System.getProperty("org.gradle.test.worker", "1"));
  static final OrderRepository REPO = new InMemoryOrderRepository();
  static final String BASE_URL;
  static final HttpClient HTTP = HttpClient.newHttpClient();

  static {                       // runs once per JVM (class init)
    try {
      BASE_URL = "http://127.0.0.1:" + new OrderApi(REPO).start();
    } catch (IOException e) {
      throw new UncheckedIOException(e);
    }
    log("API started on " + BASE_URL);
  }                              // no stop(): JVM exit frees it

  static void log(String msg) {
    System.out.printf("[fork %s pid %d] %s%n",
        FORK, ProcessHandle.current().pid(), msg);
  }

  /** Unique per fork and test: forks never share rows. */
  static String uniqueId(String test) {
    return "f" + FORK + "-" + test;
  }

  static HttpResponse<String> get(String path) throws Exception {
    var req =
        HttpRequest.newBuilder(URI.create(BASE_URL + path)).build();
    return HTTP.send(req, HttpResponse.BodyHandlers.ofString());
  }
}
