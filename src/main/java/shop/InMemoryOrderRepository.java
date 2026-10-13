package shop;

import java.util.Map;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;

/** A fake: a real, working implementation that takes a shortcut (memory, not a DB). */
public class InMemoryOrderRepository implements OrderRepository {
  private final Map<String, Order> orders = new ConcurrentHashMap<>();
  @Override public Order save(Order order) {
    orders.put(order.id(), order);
    return order;
  }
  @Override public Optional<Order> findById(String id) {
    return Optional.ofNullable(orders.get(id));
  }
}
