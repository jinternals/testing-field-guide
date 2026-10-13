package shop;

import static org.assertj.core.api.Assertions.*;

import java.math.BigDecimal;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.data.jpa.test.autoconfigure.DataJpaTest;
import org.springframework.context.annotation.Import;
import org.springframework.dao.DataIntegrityViolationException;

/**
 * @DataJpaTest: each test runs in a transaction that is
 * ROLLED BACK. Fast and tidy, but nothing is ever committed.
 */
@DataJpaTest
@Import(TestcontainersConfiguration.class)
class OrderRepositoryIT {
  @Autowired OrderRepository repository;

  @Test
  void duplicateReferenceSlipsThroughUntilFlush() {
    repository.save(new CustomerOrder("A-1", BigDecimal.ONE));
    repository.save(new CustomerOrder("A-1", BigDecimal.TWO));
    // no error yet: the INSERTs are still waiting in the session

    assertThatThrownBy(repository::flush)
        .isInstanceOf(DataIntegrityViolationException.class);
  }

  @Test
  void lazyLinesLoadBecauseTheTestHoldsATransaction() {
    repository.saveAndFlush(
        new CustomerOrder("B-1", BigDecimal.TEN)
            .addLine("BOOK", 2).addLine("PEN", 1));

    var order = repository.findByReference("B-1").orElseThrow();
    assertThat(order.getLines()).hasSize(2);   // green here …
  }
}
