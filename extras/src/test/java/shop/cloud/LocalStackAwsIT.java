package shop.cloud;

import java.net.URI;
import org.junit.jupiter.api.condition.EnabledIfEnvironmentVariable;
import org.testcontainers.localstack.LocalStackContainer;

/** LocalStack: needs LOCALSTACK_AUTH_TOKEN since 23 March 2026. */
@EnabledIfEnvironmentVariable(named = "LOCALSTACK_AUTH_TOKEN",
                              matches = ".+")
class LocalStackAwsIT extends AwsStorageContract {
  static LocalStackContainer localstack;

  @Override URI endpoint() {
    if (localstack == null) {          // start only when enabled
      localstack = new LocalStackContainer("localstack/localstack:4.14.0")
          .withServices("s3", "sqs")
          .withEnv("LOCALSTACK_AUTH_TOKEN",
                   System.getenv("LOCALSTACK_AUTH_TOKEN"));
      localstack.start();
    }
    return localstack.getEndpoint();
  }
}
