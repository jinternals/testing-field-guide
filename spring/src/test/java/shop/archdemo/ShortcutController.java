package shop.archdemo;

import shop.OrderRepository;

/** A deliberate violation, used to prove the rule bites. */
class ShortcutController {
  private final OrderRepository repository;

  ShortcutController(OrderRepository repository) {
    this.repository = repository;
  }

  long count() { return repository.count(); }
}
