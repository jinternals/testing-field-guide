package shop.cache;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.clearInvocations;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.context.annotation.Import;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.test.context.bean.override.mockito.MockitoSpyBean;
import shop.RedisContainer;

@SpringBootTest
@Import(RedisContainer.class)
class PriceCacheIT {
  @Autowired PriceService prices;
  @Autowired StringRedisTemplate redis;
  @MockitoSpyBean PriceSource source;

  @BeforeEach
  void emptyCache() {
    redis.delete(redis.keys("*"));
    clearInvocations(source);
  }

  @Test
  void secondCallIsServedFromRedis() {
    prices.price("book-1");
    assertThat(redis.hasKey("prices::book-1")).isTrue();
    prices.price("book-1");

    verify(source, times(1)).fetch("book-1");
    assertThat(redis.hasKey("prices::book-1")).isTrue();
    assertThat(redis.getExpire("prices::book-1"))
        .isBetween(1L, 600L);              // TTL 10m applied
  }

  @Test
  void evictingMakesTheNextCallFetchAgain() {
    prices.price("book-1");
    prices.priceChanged("book-1");
    prices.price("book-1");

    verify(source, times(2)).fetch("book-1");
  }

  @Test
  void selfInvocationBypassesTheCache() {
    prices.priceWithTax("book-1");
    prices.priceWithTax("book-1");

    verify(source, times(2)).fetch("book-1");
    assertThat(redis.hasKey("prices::book-1")).isFalse();
  }

  @Test
  void aValueThatIsNotSerializableFailsOnlyAtRuntime() {
    assertThatThrownBy(() -> prices.quote("book-1"))
        .isInstanceOf(IllegalStateException.class)
        .hasMessage("Cannot serialize value of type "
            + "shop.cache.Quote without a serializer");
  }
}
