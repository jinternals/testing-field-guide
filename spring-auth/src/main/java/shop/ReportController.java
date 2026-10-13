package shop;

import java.util.Map;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.web.bind.annotation.*;

@RestController
public class ReportController {
  @GetMapping("/reports/daily")
  public Map<String, Object> daily(
      @AuthenticationPrincipal Jwt jwt) {
    return Map.of("orders", 42,
                  "requestedBy", jwt.getSubject());
  }
}
