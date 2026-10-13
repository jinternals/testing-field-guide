package shop;

import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.boot.testcontainers.service.connection.ServiceConnection;
import org.springframework.context.annotation.Bean;
import org.testcontainers.containers.GenericContainer;

/** A real Redis, started with the test context. */
@TestConfiguration(proxyBeanMethods = false)
public class RedisContainer {
  @Bean
  @ServiceConnection(name = "redis")
  GenericContainer<?> redis() {
    return new GenericContainer<>("redis:8-alpine")
        .withExposedPorts(6379);
  }
}
