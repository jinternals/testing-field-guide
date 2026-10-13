package shop.legacy;

import java.time.Clock;
import java.time.LocalDate;
import java.util.List;

/**
 * Legacy code, as found — except for ONE change: the Clock.
 * It used to call LocalDate.now() directly, so its output
 * changed every day and no test could pin it down.
 */
public class InvoiceReport {
  private final Clock clock;

  public InvoiceReport() { this(Clock.systemDefaultZone()); }

  public InvoiceReport(Clock clock) {   // the seam
    this.clock = clock;
  }

  /** rows: sku, quantity, unit price */
  public String render(List<String[]> rows) {
    StringBuilder out = new StringBuilder();
    out.append("INVOICE ").append(LocalDate.now(clock))
       .append('\n');
    double total = 0;
    for (String[] r : rows) {
      int qty = Integer.parseInt(r[1]);
      double price = Double.parseDouble(r[2]);
      double line = qty * price;
      if (qty >= 10) line = line * 0.95;     // bulk discount
      total += line;
      out.append(String.format("%-5s %3d x %7.2f = %8.2f%n",
          r[0], qty, price, line));
    }
    if (total > 1000) total = total - 50;    // ??? nobody knows
    out.append(String.format("TOTAL %.2f%n", total));
    return out.toString();
  }
}
