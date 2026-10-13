package shop.http;

import static com.github.tomakehurst.wiremock.client.WireMock.*;
import static com.github.tomakehurst.wiremock.core.WireMockConfiguration.wireMockConfig;
import static com.github.tomakehurst.wiremock.stubbing.Scenario.STARTED;
import static org.assertj.core.api.Assertions.*;

import com.github.tomakehurst.wiremock.junit5.WireMockExtension;
import java.net.URI;
import java.util.NoSuchElementException;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.RegisterExtension;

/** WireMock: a real HTTP server that answers as told. */
class PriceClientTest {
  @RegisterExtension
  static WireMockExtension wm = WireMockExtension.newInstance()
      .options(wireMockConfig().dynamicPort()).build();

  static final String PATH = "/prices/BOOK";
  static final String BOOK = """
      {"sku":"BOOK","price":"600.00"}""";

  PriceClient client = new PriceClient(
      URI.create(wm.baseUrl()), Retries.forPrices());

  @Test
  void returnsThePrice() {
    wm.stubFor(get(PATH).willReturn(okJson(BOOK)));

    assertThat(client.priceOf("BOOK")).isEqualTo("600.00");
  }

  @Test
  void twoOutagesThenSuccessIsRetried() {
    wm.stubFor(get(PATH).inScenario("flaky")
        .whenScenarioStateIs(STARTED)
        .willReturn(serviceUnavailable()).willSetStateTo("2"));
    wm.stubFor(get(PATH).inScenario("flaky")
        .whenScenarioStateIs("2")
        .willReturn(serverError()).willSetStateTo("up"));
    wm.stubFor(get(PATH).inScenario("flaky")
        .whenScenarioStateIs("up").willReturn(okJson(BOOK)));

    assertThat(client.priceOf("BOOK")).isEqualTo("600.00");
    wm.verify(3, getRequestedFor(urlEqualTo(PATH)));
  }

  @Test
  void slowServiceTimesOutAfterThreeTries() {
    wm.stubFor(get(PATH)
        .willReturn(okJson(BOOK).withFixedDelay(2_000)));

    assertThatThrownBy(() -> client.priceOf("BOOK"))
        .isInstanceOf(UpstreamException.class)
        .hasMessage("unreachable");
    wm.verify(3, getRequestedFor(urlEqualTo(PATH)));
  }

  @Test
  void unknownProductIsNotRetried() {
    wm.stubFor(get("/prices/NOPE").willReturn(notFound()));

    assertThatThrownBy(() -> client.priceOf("NOPE"))
        .isInstanceOf(NoSuchElementException.class);
    wm.verify(1, getRequestedFor(urlEqualTo("/prices/NOPE")));
  }

  @Test
  void malformedJsonIsAClearError() {
    wm.stubFor(get(PATH).willReturn(ok("<html>error</html>")));

    assertThatThrownBy(() -> client.priceOf("BOOK"))
        .isInstanceOf(IllegalStateException.class)
        .hasMessageStartingWith("bad price JSON");
  }
}
