package shop;

import static org.assertj.core.api.Assertions.*;
import static org.springframework.boot.test.context.SpringBootTest.WebEnvironment.RANDOM_PORT;

import java.util.Map;
import no.nav.security.mock.oauth2.MockOAuth2Server;
import org.junit.jupiter.api.*;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.server.LocalServerPort;
import org.springframework.test.context.*;
import org.springframework.web.client.*;
import org.springframework.web.client.HttpClientErrorException.Unauthorized;

/**
 * Lightweight option: the mock auth server runs in the test
 * JVM as a library. Real signed tokens, a real JWKS endpoint,
 * no Docker, starts in milliseconds.
 */
@SpringBootTest(webEnvironment = RANDOM_PORT)
class InProcessAuthServerIT {
  static final MockOAuth2Server AUTH = new MockOAuth2Server();
  static { AUTH.start(); }

  @DynamicPropertySource
  static void authServer(DynamicPropertyRegistry props) {
    props.add(
        "spring.security.oauth2.resourceserver.jwt.issuer-uri",
        () -> AUTH.issuerUrl("shop").toString());
  }

  @AfterAll static void stop() { AUTH.shutdown(); }

  @LocalServerPort int port;

  String report(String token) {
    return RestClient.create()
        .get().uri("http://localhost:{p}/reports/daily", port)
        .headers(h -> h.setBearerAuth(token))
        .retrieve().body(String.class);
  }

  @Test
  void tokenWithScopeIsAccepted() {
    var scope = Map.<String, Object>of("scope", "reports.read");
    String token = AUTH.issueToken("shop", "asha",
        "reports-api", scope).serialize();

    assertThat(report(token)).contains("asha");
  }

  @Test
  void tokenForAnotherAudienceIsRejected() {
    var scope = Map.<String, Object>of("scope", "reports.read");
    String token = AUTH.issueToken("shop", "asha",
        "billing-api", scope).serialize();

    assertThatThrownBy(() -> report(token))
        .isInstanceOf(Unauthorized.class);
  }
}
