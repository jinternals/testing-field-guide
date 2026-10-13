package shop.cache;

import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;

@Service
public class PriceService {
  private final PriceSource source;

  public PriceService(PriceSource source) {
    this.source = source;
  }

  @Cacheable("prices")
  public Price price(String sku) {
    return source.fetch(sku);
  }

  @CacheEvict("prices")
  public void priceChanged(String sku) {
  }

  /** Calls price() on "this", not on the proxy: never cached. */
  public long priceWithTax(String sku) {
    return price(sku).paise() * 118 / 100;
  }

  @Cacheable("quotes")
  public Quote quote(String sku) {
    return new Quote(sku, source.fetch(sku).paise());
  }
}
