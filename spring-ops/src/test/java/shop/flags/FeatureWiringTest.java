package shop.flags;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.runner.ApplicationContextRunner;

/** The property really reaches the bean; no web server, ~ms. */
class FeatureWiringTest {
  ApplicationContextRunner ctx = new ApplicationContextRunner()
      .withUserConfiguration(FeatureConfig.class);

  @Test
  void offWhenThePropertyIsMissing() {
    ctx.run(c -> assertThat(c.getBean(CheckoutPricing.class)
        .total(100_000, 3)).isEqualTo(100_000));
  }

  @Test
  void onWithThePropertySet() {
    ctx.withPropertyValues("shop.features.bulk-discount=true")
        .run(c -> assertThat(c.getBean(CheckoutPricing.class)
            .total(100_000, 3)).isEqualTo(90_000));
  }
}
