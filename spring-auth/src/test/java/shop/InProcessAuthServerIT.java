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

/**
 * Lightweight option: the mock auth server runs inside the test
 * JVM as a library. Real signed tokens and a real JWKS endpoint,
 * no Docker, starts in milliseconds.
 */
@SpringBootTest(webEnvironment = RANDOM_PORT)
class InProcessAuthServerIT {
  static final MockOAuth2Server AUTH = new MockOAuth2Server();
  static { AUTH.start(); }

  @DynamicPropertySource
  static void authServer(DynamicPropertyRegistry props) {
    props.add("spring.security.oauth2.resourceserver.jwt.issuer-uri",
        () -> AUTH.issuerUrl("shop").toString());
  }

  @AfterAll static void stop() { AUTH.shutdown(); }

  @LocalServerPort int port;

  String report(String token) {
    return RestClient.create()
        .get().uri("http://localhost:" + port + "/reports/daily")
        .headers(h -> h.setBearerAuth(token))
        .retrieve().body(String.class);
  }

  @Test
  void tokenWithScopeIsAccepted() {
    String token = AUTH.issueToken("shop", "asha", "reports-api",
        Map.of("scope", "reports.read")).serialize();

    assertThat(report(token)).contains("\"requestedBy\":\"asha\"");
  }

  @Test
  void tokenForAnotherAudienceIsRejected() {
    String token = AUTH.issueToken("shop", "asha", "billing-api",
        Map.of("scope", "reports.read")).serialize();

    assertThatThrownBy(() -> report(token))
        .isInstanceOf(HttpClientErrorException.Unauthorized.class);
  }
}
