package shop.cache;

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.boot.cache.autoconfigure.RedisCacheManagerBuilderCustomizer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.redis.cache.RedisCacheWriter;
import org.springframework.data.redis.connection.RedisConnectionFactory;

/**
 * Spring Data Redis 4 with Lettuce: put() and evict() are
 * asynchronous by default and can finish after the call
 * returns. Wait for them: a read right after a write must
 * see it.
 */
@Configuration(proxyBeanMethods = false)
class CacheConfig {
  @Bean
  @ConditionalOnProperty(name = "shop.cache.immediate-writes",
      havingValue = "true", matchIfMissing = true)
  RedisCacheManagerBuilderCustomizer immediateWrites(
      RedisConnectionFactory redis) {
    return builder -> builder.cacheWriter(RedisCacheWriter
        .create(redis, w -> w.immediateWrites()));
  }
}
