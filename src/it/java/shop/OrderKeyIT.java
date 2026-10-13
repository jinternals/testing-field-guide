package shop;

import static org.assertj.core.api.Assertions.*;

import java.sql.SQLException;
import org.junit.jupiter.api.*;

class OrderKeyIT extends SharedPostgres {
  @BeforeAll static void hello() {
    log("OrderKeyIT uses " + DB.getJdbcUrl());
  }

  @Test void duplicateIdIsRejected() throws Exception {
    String id = uniqueId("dup");
    try (var c = connect()) {
      insert(c, id, "10");
      assertThatThrownBy(() -> insert(c, id, "20"))
          .isInstanceOf(SQLException.class)
          .extracting(e -> ((SQLException) e).getSQLState())
          .isEqualTo("23505");          // unique_violation
    }
  }
}
