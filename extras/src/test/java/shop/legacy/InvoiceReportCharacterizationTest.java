package shop.legacy;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.fail;

import java.nio.file.*;
import java.time.*;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;

/**
 * Characterization tests: they record what the code DOES today,
 * right or wrong, so a refactoring can't change it by accident.
 */
class InvoiceReportCharacterizationTest {
  static final Clock FIXED = Clock.fixed(
      Instant.parse("2026-10-13T09:00:00Z"), ZoneOffset.UTC);

  @Test
  void outputMatchesTheApprovedFile() throws Exception {
    String actual = new InvoiceReport(FIXED).render(List.of(
        new String[] {"BOOK", "2", "600.00"},
        new String[] {"PEN", "10", "12.50"},
        new String[] {"BAG", "1", "499.99"}));

    Path approved = Path.of("src/test/resources/approved/invoice.txt");
    if (!Files.exists(approved)) {             // first run: record it
      Files.writeString(Path.of("target/invoice.received.txt"), actual);
      fail("Review target/invoice.received.txt, then approve it");
    }
    assertThat(actual).isEqualTo(Files.readString(approved));
  }

  @ParameterizedTest(name = "{0} x {1} -> {2}")
  @CsvSource({        // edges found by probing; values are TODAY's
      " 9, 100.00, 900.00",     // no bulk discount below 10
      "10, 100.00, 950.00",     // 5% off from 10
      " 1, 1000.00, 1000.00",   // exactly 1000: no 50 off
      " 1, 1000.01, 950.01",    // just above: 50 off
  })
  void totalsAsTheyAreToday(int qty, String price, String total) {
    String out = new InvoiceReport(FIXED).render(List.<String[]>of(
        new String[] {"X", String.valueOf(qty), price}));
    assertThat(out).endsWith("TOTAL " + total + "\n");
  }
}
