package shop;

import static org.assertj.core.api.Assertions.*;
import static org.springframework.boot.test.context.SpringBootTest.WebEnvironment.RANDOM_PORT;

import java.util.Map;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.server.LocalServerPort;
import org.springframework.http.MediaType;
import org.springframework.test.context.*;
import org.springframework.util.*;
import org.springframework.web.client.*;
import org.testcontainers.containers.GenericContainer;

/**
 * A real OAuth2/OIDC server in a container issues real signed
 * tokens; the app checks issuer, signature, audience and scope.
 */
@SpringBootTest(webEnvironment = RANDOM_PORT)
class MockAuthServerIT {
  static final GenericContainer<?> AUTH =
      new GenericContainer<>("ghcr.io/navikt/mock-oauth2-server:6.0.7")
          .withExposedPorts(8080)
          .withEnv("JSON_CONFIG", """
              {"tokenCallbacks": [{"issuerId": "shop",
                "requestMappings": [{"requestParam": "scope",
                  "match": "reports.read",
                  "claims": {"sub": "reporting-job",
                    "aud": ["reports-api"], "scope": "reports.read"}}]
              }]}""");
  static { AUTH.start(); }

  static String issuer(String id) {
    return "http://" + AUTH.getHost() + ":"
        + AUTH.getMappedPort(8080) + "/" + id;
  }

  @DynamicPropertySource
  static void authServer(DynamicPropertyRegistry props) {
    props.add("spring.security.oauth2.resourceserver.jwt.issuer-uri",
        () -> issuer("shop"));
  }

  @LocalServerPort int port;
  RestClient http = RestClient.create();

  /** client_credentials grant against the mock server. */
  String token(String issuerId, String scope) {
    MultiValueMap<String, String> form = new LinkedMultiValueMap<>();
    form.add("grant_type", "client_credentials");
    form.add("client_id", "reporting-job");
    form.add("client_secret", "any");
    form.add("scope", scope);
    Map<?, ?> body = http.post().uri(issuer(issuerId) + "/token")
        .contentType(MediaType.APPLICATION_FORM_URLENCODED)
        .body(form).retrieve().body(Map.class);
    return (String) body.get("access_token");
  }

  String report(String token) {
    return http.get().uri("http://localhost:" + port + "/reports/daily")
        .headers(h -> h.setBearerAuth(token))
        .retrieve().body(String.class);
  }

  @Test
  void realTokenWithScopeIsAccepted() {
    assertThat(report(token("shop", "reports.read")))
        .contains("\"requestedBy\":\"reporting-job\"");
  }

  @Test
  void tokenFromAnotherIssuerIsRejected() {
    assertThatThrownBy(() -> report(token("evil", "reports.read")))
        .isInstanceOf(HttpClientErrorException.Unauthorized.class);
  }

  @Test
  void tokenWithoutScopeIsForbidden() {
    assertThatThrownBy(() -> report(token("shop", "profile")))
        .isInstanceOf(HttpClientErrorException.class)
        .hasMessageStartingWith("40");
  }
}
