package shop;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.jwt;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.context.annotation.Import;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.test.web.servlet.assertj.MockMvcTester;

/** No auth server: Spring Security builds the JWT in memory. */
@WebMvcTest(ReportController.class)
@Import(SecurityConfig.class)
class ReportControllerTest {
  @Autowired MockMvcTester mvc;

  @Test
  void noTokenIs401() {
    assertThat(mvc.get().uri("/reports/daily"))
        .hasStatus(HttpStatus.UNAUTHORIZED);
  }

  @Test
  void tokenWithoutTheScopeIs403() {
    assertThat(mvc.get().uri("/reports/daily").with(jwt()))
        .hasStatus(HttpStatus.FORBIDDEN);
  }

  @Test
  void tokenWithTheScopeIs200() {
    var scope = new SimpleGrantedAuthority("SCOPE_reports.read");
    var token = jwt().jwt(t -> t.subject("asha")).authorities(scope);
    assertThat(mvc.get().uri("/reports/daily").with(token))
        .hasStatusOk()
        .bodyJson().isLenientlyEqualTo("""
            {"orders":42,"requestedBy":"asha"}""");
  }
}
