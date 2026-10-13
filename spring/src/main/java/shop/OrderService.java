package shop;

import java.util.Optional;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class OrderService {
  private final OrderRepository repository;

  public OrderService(OrderRepository repository) {
    this.repository = repository;
  }

  /** Maps to a view inside the transaction, so nothing lazy escapes. */
  @Transactional(readOnly = true)
  public Optional<OrderView> find(String reference) {
    return repository.findWithLines(reference).map(OrderView::of);
  }
}
