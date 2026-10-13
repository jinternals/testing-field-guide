package shop.cache;

import static org.awaitility.Awaitility.await;

import java.time.Duration;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.context.annotation.Import;
import org.springframework.data.redis.core.StringRedisTemplate;
import shop.RedisContainer;

/** The library default, no immediate writes: count the lag. */
@SpringBootTest(properties =
    "shop.cache.immediate-writes=false")
@Import(RedisContainer.class)
class AsyncCacheWritesIT {
  @Autowired PriceService prices;
  @Autowired StringRedisTemplate redis;

  @Test
  void writesLandAfterTheCallReturns() {
    int notYet = 0;
    for (int i = 0; i < 1000; i++) {
      prices.price("sku-" + i);
      if (!redis.hasKey("prices::sku-" + i)) {
        notYet++;
      }
    }
    System.out.println("[async writes] " + notYet + " of 1000"
        + " entries were not in Redis when price() returned");

    await().atMost(Duration.ofSeconds(5)).until(
        () -> redis.keys("prices::sku-*").size() == 1000);
  }
}
