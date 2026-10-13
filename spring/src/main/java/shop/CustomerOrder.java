package shop;

import jakarta.persistence.*;
import java.math.BigDecimal;
import java.util.*;

@Entity
@Table(name = "orders")
public class CustomerOrder {
  @Id private UUID id;                 // assigned here, not by the DB

  @Column(nullable = false, unique = true)
  private String reference;

  @Column(nullable = false)
  private BigDecimal total;

  @OneToMany(mappedBy = "order", cascade = CascadeType.ALL,
             fetch = FetchType.LAZY)
  private List<OrderLine> lines = new ArrayList<>();

  protected CustomerOrder() {}         // for JPA

  public CustomerOrder(String reference, BigDecimal total) {
    this.id = UUID.randomUUID();
    this.reference = reference;
    this.total = total;
  }

  public CustomerOrder addLine(String sku, int quantity) {
    lines.add(new OrderLine(this, sku, quantity));
    return this;
  }

  public UUID getId() { return id; }
  public String getReference() { return reference; }
  public BigDecimal getTotal() { return total; }
  public List<OrderLine> getLines() { return lines; }
}
