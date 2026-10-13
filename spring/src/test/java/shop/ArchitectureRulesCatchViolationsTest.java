package shop;

import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.tngtech.archunit.core.importer.ClassFileImporter;
import org.junit.jupiter.api.Test;

/** A rule that never fails is no rule: show it catching one. */
class ArchitectureRulesCatchViolationsTest {

  @Test
  void controllerCallingARepositoryIsReported() {
    var classes = new ClassFileImporter()
        .importPackages("shop.archdemo");

    assertThatThrownBy(() -> ArchitectureTest
        .CONTROLLERS_DONT_USE_REPOSITORIES.check(classes))
        .isInstanceOf(AssertionError.class)
        .hasMessageContaining("was violated (")
        .satisfies(e -> System.out.println(e.getMessage()));
  }
}
