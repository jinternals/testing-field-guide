package shop;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/orders")
public class OrderController {
  private final OrderService orders;

  public OrderController(OrderService orders) { this.orders = orders; }

  @GetMapping("/{reference}")
  public ResponseEntity<OrderView> get(@PathVariable String reference) {
    return ResponseEntity.of(orders.find(reference));
  }
}
