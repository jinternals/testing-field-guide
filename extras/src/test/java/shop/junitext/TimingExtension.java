package shop.junitext;

import org.junit.jupiter.api.extension.*;
import org.junit.jupiter.api.extension.ExtensionContext.Namespace;

/** Reports how long each test method took. */
public class TimingExtension
    implements BeforeTestExecutionCallback, AfterTestExecutionCallback {
  private static final Namespace NS =
      Namespace.create(TimingExtension.class);

  @Override
  public void beforeTestExecution(ExtensionContext ctx) {
    ctx.getStore(NS).put("start", System.nanoTime());
  }

  @Override
  public void afterTestExecution(ExtensionContext ctx) {
    long start = ctx.getStore(NS).remove("start", Long.class);
    long ms = (System.nanoTime() - start) / 1_000_000;
    System.out.printf("[timing] %s took %d ms%n",
        ctx.getDisplayName(), ms);
  }
}
