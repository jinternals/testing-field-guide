package shop;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.*;

class OrderSearchIT extends SharedPostgres {
  @BeforeAll static void hello() {
    log("OrderSearchIT uses " + DB.getJdbcUrl());
  }

  @Test void bigOrdersQueryFindsOnlyBigOnes() throws Exception {
    String big = uniqueId("big"), small = uniqueId("small");
    try (var c = connect()) {
      insert(c, big, "6000");
      insert(c, small, "100");
      try (var ps = c.prepareStatement(
          "SELECT id FROM orders WHERE total >= 5000 AND id IN (?, ?)")) {
        ps.setString(1, big);
        ps.setString(2, small);
        var rs = ps.executeQuery();
        assertThat(rs.next()).isTrue();
        assertThat(rs.getString(1)).isEqualTo(big);
        assertThat(rs.next()).isFalse();
      }
    }
  }
}
