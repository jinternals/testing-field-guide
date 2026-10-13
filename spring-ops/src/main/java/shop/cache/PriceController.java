package shop.cache;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RestController;

@RestController
class PriceController {
  private final PriceService prices;

  PriceController(PriceService prices) {
    this.prices = prices;
  }

  @GetMapping("/prices/{sku}")
  Price price(@PathVariable String sku) {
    return prices.price(sku);
  }
}
