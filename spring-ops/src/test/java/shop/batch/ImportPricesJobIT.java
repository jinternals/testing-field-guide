package shop.batch;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;
import org.springframework.batch.core.BatchStatus;
import org.springframework.batch.core.job.JobExecution;
import org.springframework.batch.core.step.StepExecution;
import org.springframework.batch.test.JobOperatorTestUtils;
import org.springframework.batch.test.context.SpringBatchTest;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import shop.cache.Price;

/** prices.csv: 2 good lines, 1 negative, 1 broken, 1 more good. */
@SpringBootTest(properties = "spring.cache.type=none")
@SpringBatchTest
class ImportPricesJobIT {
  @Autowired JobOperatorTestUtils jobs;
  @Autowired PriceCatalog catalog;

  @Test
  void importsGoodLinesFiltersNegativeSkipsBroken() throws Exception {
    JobExecution run = jobs.startJob();

    assertThat(run.getStatus()).isEqualTo(BatchStatus.COMPLETED);
    StepExecution step = run.getStepExecutions().iterator().next();
    assertThat(step.getReadCount()).isEqualTo(4);
    assertThat(step.getFilterCount()).isEqualTo(1);
    assertThat(step.getReadSkipCount()).isEqualTo(1);
    assertThat(step.getWriteCount()).isEqualTo(3);
    assertThat(catalog.get("book-2"))
        .contains(new Price("book-2", 129_950));
  }
}
