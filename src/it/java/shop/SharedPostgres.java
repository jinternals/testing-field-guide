package shop;

import java.sql.*;
import org.testcontainers.postgresql.PostgreSQLContainer;

/**
 * Singleton container: started once per test JVM (fork) when the
 * first subclass loads, shared by every IT class in that JVM, and
 * removed by Testcontainers' Ryuk container when the JVM exits.
 */
abstract class SharedPostgres {
  static final String FORK = System.getProperty("fork",
      System.getProperty("org.gradle.test.worker", "1"));
  static final PostgreSQLContainer DB =
      new PostgreSQLContainer("postgres:17-alpine");

  static {
    DB.start();                 // once per JVM, never stop() here
    try (var c = connect(); var s = c.createStatement()) {
      s.execute("""
          CREATE TABLE orders (
            id    text PRIMARY KEY,
            email text NOT NULL,
            total numeric(12,2) NOT NULL CHECK (total >= 0))""");
    } catch (SQLException e) {
      throw new IllegalStateException(e);
    }
    log("Postgres " + DB.getContainerId().substring(0, 12)
        + " on port " + DB.getFirstMappedPort());
  }

  static Connection connect() throws SQLException {
    return DriverManager.getConnection(
        DB.getJdbcUrl(), DB.getUsername(), DB.getPassword());
  }

  static void log(String msg) {
    System.out.printf("[fork %s pid %d] %s%n",
        FORK, ProcessHandle.current().pid(), msg);
  }

  /** Unique per test, so tests never depend on each other's rows. */
  static String uniqueId(String test) {
    return "f" + FORK + "-" + test + "-" + System.nanoTime();
  }

  static void insert(Connection c, String id, String total)
      throws SQLException {
    try (var ps = c.prepareStatement(
        "INSERT INTO orders (id, email, total) VALUES (?, ?, ?)")) {
      ps.setString(1, id);
      ps.setString(2, "asha@example.com");
      ps.setBigDecimal(3, new java.math.BigDecimal(total));
      ps.executeUpdate();
    }
  }
}
