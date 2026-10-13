package shop.synthetic;

import static org.assertj.core.api.Assertions.assertThat;

import java.net.URI;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.context.SpringBootTest.WebEnvironment;
import org.springframework.context.annotation.Import;
import shop.RedisContainer;

/** The production check, run against the app before it ships. */
@SpringBootTest(webEnvironment = WebEnvironment.RANDOM_PORT)
@Import(RedisContainer.class)
class SyntheticCheckIT {
  @Value("${local.server.port}") int port;

  @Test
  void passesAgainstAHealthyApp() {
    var base = URI.create("http://localhost:" + port);
    assertThat(SyntheticCheck.run(base)).isEmpty();
  }
}
