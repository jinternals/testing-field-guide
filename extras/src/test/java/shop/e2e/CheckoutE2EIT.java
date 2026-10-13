package shop.e2e;

import static com.microsoft.playwright.assertions.PlaywrightAssertions.assertThat;

import com.microsoft.playwright.*;
import com.sun.net.httpserver.HttpServer;
import java.net.InetSocketAddress;
import java.nio.file.*;
import org.junit.jupiter.api.*;

/** A real Chromium, driven by Playwright for Java. */
class CheckoutE2EIT {
  static HttpServer web;           // serves the shop page
  static Playwright playwright;
  static Browser browser;
  BrowserContext context;
  Page page;

  @BeforeAll static void start() throws Exception {
    byte[] html = CheckoutE2EIT.class
        .getResourceAsStream("/web/shop.html").readAllBytes();
    web = HttpServer.create(
        new InetSocketAddress("127.0.0.1", 0), 0);
    web.createContext("/", ex -> {
      ex.getResponseHeaders().set("Content-Type", "text/html");
      ex.sendResponseHeaders(200, html.length);
      ex.getResponseBody().write(html);
      ex.close();
    });
    web.start();
    playwright = Playwright.create();
    browser = playwright.chromium().launch();       // headless
  }

  @BeforeEach void open() {
    context = browser.newContext();          // fresh cookies
    context.tracing().start(new Tracing.StartOptions()
        .setScreenshots(true).setSnapshots(true));
    page = context.newPage();
    page.navigate("http://127.0.0.1:"
        + web.getAddress().getPort() + "/");
  }

  @AfterEach void close(TestInfo info) {
    String name = info.getTestMethod().orElseThrow().getName();
    page.screenshot(new Page.ScreenshotOptions()
        .setPath(Path.of("target/" + name + ".png")));
    context.tracing().stop(new Tracing.StopOptions()
        .setPath(Path.of("target/" + name + "-trace.zip")));
    context.close();
  }

  @AfterAll static void stop() {
    browser.close();
    playwright.close();
    web.stop(0);
  }

  @Test
  void twoBooksGetTheBulkDiscount() {
    var checkout = new CheckoutPage(page);
    checkout.addToCart("Book");
    checkout.addToCart("Book");
    checkout.checkout();

    assertThat(checkout.total()).hasText("₹1,140.00"); // waits
  }

  @Test
  void smallOrderPaysFullPrice() {
    var checkout = new CheckoutPage(page);
    checkout.addToCart("Pen");
    checkout.checkout();

    assertThat(checkout.total()).hasText("₹40.00");
  }
}
