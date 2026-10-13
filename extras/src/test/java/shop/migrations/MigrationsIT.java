package shop.migrations;

import static org.assertj.core.api.Assertions.*;

import java.sql.*;
import org.flywaydb.core.Flyway;
import org.flywaydb.core.api.FlywayException;
import org.flywaydb.core.api.configuration.FluentConfiguration;
import org.junit.jupiter.api.Test;
import org.testcontainers.postgresql.PostgreSQLContainer;

/** Migrations run against the same database as production. */
class MigrationsIT {
  static final PostgreSQLContainer DB =
      new PostgreSQLContainer("postgres:17-alpine");
  static { DB.start(); }

  /** One schema per test, so tests never see each other. */
  static FluentConfiguration flyway(String schema) {
    return Flyway.configure()
        .dataSource(DB.getJdbcUrl(), DB.getUsername(),
                    DB.getPassword())
        .schemas(schema);
  }

  static Connection connect() throws SQLException {
    return DriverManager.getConnection(DB.getJdbcUrl(),
        DB.getUsername(), DB.getPassword());
  }

  /** A customer row written while only V1 and V2 existed. */
  static void insertOldOrder(String schema)
      throws SQLException {
    try (var c = connect(); var s = c.createStatement()) {
      s.execute("INSERT INTO " + schema + ".orders (id, email, "
          + "total) VALUES ('old-1', 'asha@example.com', 10)");
    }
  }

  @Test
  void allMigrationsApplyToAnEmptyDatabase() {
    var result = flyway("fresh").load().migrate();

    assertThat(result.migrationsExecuted).isEqualTo(3);
    assertThat(result.targetSchemaVersion).isEqualTo("3");
    flyway("fresh").load().validate();  // checksums unchanged
  }

  @Test
  void v3BackfillsRowsThatAlreadyExist() throws SQLException {
    flyway("live").target("2").load().migrate();   // yesterday
    insertOldOrder("live");

    flyway("live").load().migrate();               // deploy V3

    try (var c = connect(); var rs = c.createStatement()
        .executeQuery("SELECT status FROM live.orders")) {
      rs.next();
      assertThat(rs.getString(1)).isEqualTo("PLACED");
    }
  }

  @Test
  void v3WithoutBackfillFailsOnRealData() throws SQLException {
    flyway("broken").target("2").load().migrate();
    insertOldOrder("broken");

    var withBrokenV3 = flyway("broken")
        .locations("classpath:db/broken")       // only V3
        .ignoreMigrationPatterns("*:missing")   // V1, V2 ran
        .load();

    assertThatThrownBy(withBrokenV3::migrate)
        .isInstanceOf(FlywayException.class)
        .hasMessageContaining("contains null values");
  }
}
