package shop.batch;

import org.springframework.batch.core.job.Job;
import org.springframework.batch.core.job.builder.JobBuilder;
import org.springframework.batch.core.repository.JobRepository;
import org.springframework.batch.core.step.Step;
import org.springframework.batch.core.step.builder.StepBuilder;
import org.springframework.batch.infrastructure.item.file.FlatFileItemReader;
import org.springframework.batch.infrastructure.item.file.FlatFileParseException;
import org.springframework.batch.infrastructure.item.file.builder.FlatFileItemReaderBuilder;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.io.Resource;
import shop.cache.Price;

@Configuration
class ImportPricesJob {
  @Bean
  Job importPrices(JobRepository repo, Step importStep) {
    return new JobBuilder("importPrices", repo)
        .start(importStep).build();
  }

  @Bean
  Step importStep(JobRepository repo, PriceCatalog catalog,
      FlatFileItemReader<PriceLine> reader) {
    return new StepBuilder("importStep", repo)
        .<PriceLine, Price>chunk(100)
        .reader(reader)
        .processor(new ToPaise())
        .writer(chunk -> chunk.forEach(catalog::put))
        .faultTolerant()
        .skip(FlatFileParseException.class)
        .skipLimit(5)
        .build();
  }

  @Bean
  FlatFileItemReader<PriceLine> reader(
      @Value("${shop.import.file}") Resource file) {
    return new FlatFileItemReaderBuilder<PriceLine>()
        .name("prices").resource(file).linesToSkip(1)
        .delimited().names("sku", "rupees")
        .targetType(PriceLine.class).build();
  }
}
