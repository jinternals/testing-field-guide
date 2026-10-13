package shop.junitext;

import java.time.*;
import org.junit.jupiter.api.extension.*;
import org.junit.platform.commons.support.AnnotationSupport;

/** Resolves a Clock parameter from @FixedClock on the test. */
public class FixedClockExtension implements ParameterResolver {
  @Override
  public boolean supportsParameter(ParameterContext p,
      ExtensionContext ctx) {
    return p.getParameter().getType() == Clock.class;
  }

  @Override
  public Object resolveParameter(ParameterContext p,
      ExtensionContext ctx) {
    FixedClock fixed = AnnotationSupport
        .findAnnotation(ctx.getRequiredTestMethod(), FixedClock.class)
        .or(() -> AnnotationSupport.findAnnotation(
            ctx.getRequiredTestClass(), FixedClock.class))
        .orElseThrow(() -> new ParameterResolutionException(
            "Clock parameter needs @FixedClock"));
    return Clock.fixed(Instant.parse(fixed.value()), ZoneOffset.UTC);
  }
}
