package shop;

import static org.assertj.core.api.Assertions.*;

import java.math.BigDecimal;
import org.hibernate.LazyInitializationException;
import org.junit.jupiter.api.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.testcontainers.service.connection.ServiceConnection;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.test.web.servlet.assertj.MockMvcTester;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;
import org.testcontainers.postgresql.PostgreSQLContainer;

/**
 * Whole application, real PostgreSQL, NO test transaction:
 * every save commits, exactly as in production.
 */
@SpringBootTest
@AutoConfigureMockMvc
@Testcontainers
class OrderFlowIT {
  @Container @ServiceConnection
  static PostgreSQLContainer postgres =
      new PostgreSQLContainer("postgres:17-alpine");

  @Autowired MockMvcTester mvc;
  @Autowired OrderRepository repository;

  @BeforeEach
  void cleanSlate() { repository.deleteAll(); }   // no rollback here

  @Test
  void duplicateReferenceFailsOnSave() {
    repository.save(new CustomerOrder("A-1", new BigDecimal("10")));

    assertThatThrownBy(() ->
        repository.save(new CustomerOrder("A-1", new BigDecimal("20"))))
        .isInstanceOf(DataIntegrityViolationException.class);
  }

  @Test
  void lazyLinesFailOutsideATransaction() {
    repository.save(new CustomerOrder("B-1", BigDecimal.TEN)
        .addLine("BOOK", 2).addLine("PEN", 1));

    var order = repository.findByReference("B-1").orElseThrow();
    assertThatThrownBy(() -> order.getLines().size())   // … red here
        .isInstanceOf(LazyInitializationException.class);
  }

  @Test
  void apiReturnsTheOrderFromTheDatabase() {
    repository.save(new CustomerOrder("C-1", new BigDecimal("1140.00"))
        .addLine("BOOK", 2).addLine("PEN", 1));

    assertThat(mvc.get().uri("/orders/C-1"))
        .hasStatusOk()
        .bodyJson().isLenientlyEqualTo("""
            {"reference":"C-1","total":1140.00,"lines":2}""");
  }
}
