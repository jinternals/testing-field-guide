package shop.junitext;

import java.lang.annotation.*;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.extension.ExtendWith;

/** One annotation for the team: tag + both extensions. */
@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
@Tag("unit")
@ExtendWith({FixedClockExtension.class, TimingExtension.class})
public @interface ShopTest {}
