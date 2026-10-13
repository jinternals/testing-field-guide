package shop.junitext;

import java.lang.annotation.*;

/** Gives the test a Clock frozen at this instant. */
@Target({ElementType.METHOD, ElementType.TYPE})
@Retention(RetentionPolicy.RUNTIME)
public @interface FixedClock {
  String value();                      // e.g. "2026-10-13T09:00:00Z"
}
