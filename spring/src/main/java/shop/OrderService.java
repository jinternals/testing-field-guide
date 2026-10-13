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

  /** Map to a view while the transaction is still open. */
  @Transactional(readOnly = true)
  public Optional<OrderView> find(String reference) {
    return repository.findWithLines(reference).map(OrderView::of);
  }
}
