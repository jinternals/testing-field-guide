package shop.batch;

import java.util.Map;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;
import org.springframework.stereotype.Component;
import shop.cache.Price;

@Component
public class PriceCatalog {
  private final Map<String, Price> prices =
      new ConcurrentHashMap<>();

  public void put(Price price) {
    prices.put(price.sku(), price);
  }

  public Optional<Price> get(String sku) {
    return Optional.ofNullable(prices.get(sku));
  }
}
