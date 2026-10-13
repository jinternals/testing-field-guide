package shop;

import jakarta.persistence.*;
import java.util.UUID;

@Entity
public class OrderLine {
  @Id private UUID id = UUID.randomUUID();

  @ManyToOne(fetch = FetchType.LAZY, optional = false)
  private CustomerOrder order;

  private String sku;
  private int quantity;

  protected OrderLine() {}

  OrderLine(CustomerOrder order, String sku, int quantity) {
    this.order = order;
    this.sku = sku;
    this.quantity = quantity;
  }

  public String getSku() { return sku; }
  public int getQuantity() { return quantity; }
}
