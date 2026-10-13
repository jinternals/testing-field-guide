package shop;

public interface PaymentGateway {
  /** @return a payment reference; throws PaymentDeclinedException if refused. */
  String charge(String customerEmail, Money amount);
}
