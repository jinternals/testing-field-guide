package shop;

import java.time.Clock;
import java.util.List;
import java.util.UUID;

public class OrderService {
  private final OrderRepository repository;
  private final PaymentGateway payments;
  private final EmailSender email;
  private final DiscountPolicy discounts;
  private final Clock clock;

  public OrderService(OrderRepository repository, PaymentGateway payments,
            EmailSender email, DiscountPolicy discounts, Clock clock) {
    this.repository = repository;
    this.payments = payments;
    this.email = email;
    this.discounts = discounts;
    this.clock = clock;
  }

  public Order placeOrder(String customerEmail, List<Item> items) {
    if (items.isEmpty())
      throw new IllegalArgumentException("order has no items");
    Money subtotal = items.stream().map(Item::total)
        .reduce(Money.of("0"), Money::plus);
    Money total = subtotal.percentOff(discounts.percentFor(subtotal));
    payments.charge(customerEmail, total);  // may throw PaymentDeclined…
    Order order = repository.save(new Order(UUID.randomUUID().toString(),
        customerEmail, List.copyOf(items), total, clock.instant()));
    email.send(customerEmail, "Order confirmed", "Total: " + total);
    return order;
  }
}
