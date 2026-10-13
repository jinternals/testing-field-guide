package shop.cache;

import org.springframework.stereotype.Component;

/** The slow call worth caching: a database, another service. */
@Component
public class PriceSource {
  public Price fetch(String sku) {
    return new Price(sku, 49_900);
  }
}
