package shop;

import static org.assertj.core.api.Assertions.*;

import java.sql.SQLException;
import org.junit.jupiter.api.*;

class OrderTableIT extends SharedPostgres {
  @BeforeAll static void hello() {
    log("OrderTableIT uses " + DB.getJdbcUrl());
  }

  @Test void totalKeepsTwoDecimals() throws Exception {
    String id = uniqueId("scale");
    try (var c = connect()) {
      insert(c, id, "1140.5");
      try (var ps = c.prepareStatement(
          "SELECT total::text FROM orders WHERE id = ?")) {
        ps.setString(1, id);
        var rs = ps.executeQuery();
        assertThat(rs.next()).isTrue();
        assertThat(rs.getString(1)).isEqualTo("1140.50");
      }
    }
  }

  @Test void negativeTotalIsRejectedByTheDatabase() throws Exception {
    try (var c = connect()) {
      assertThatThrownBy(() -> insert(c, uniqueId("neg"), "-1"))
          .isInstanceOf(SQLException.class)
          .extracting(e -> ((SQLException) e).getSQLState())
          .isEqualTo("23514");          // check_violation
    }
  }
}
