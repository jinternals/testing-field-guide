package shop;

import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.noClasses;

import com.tngtech.archunit.core.importer.ImportOption;
import com.tngtech.archunit.junit.*;
import com.tngtech.archunit.lang.ArchRule;
import jakarta.persistence.Entity;

/** Design rules, checked on every build like any other test. */
@AnalyzeClasses(packages = "shop",
    importOptions = ImportOption.DoNotIncludeTests.class)
class ArchitectureTest {

  @ArchTest
  static final ArchRule CONTROLLERS_DONT_USE_REPOSITORIES =
      noClasses().that().haveSimpleNameEndingWith("Controller")
          .should().dependOnClassesThat()
          .haveSimpleNameEndingWith("Repository")
          .because("controllers go through a service");

  @ArchTest
  static final ArchRule CONTROLLERS_DONT_RETURN_ENTITIES =
      noClasses().that().haveSimpleNameEndingWith("Controller")
          .should().dependOnClassesThat()
          .areAnnotatedWith(Entity.class)
          .because("lazy JPA proxies must not reach JSON");

  @ArchTest
  static final ArchRule SERVICES_DONT_KNOW_THE_WEB =
      noClasses().that().haveSimpleNameEndingWith("Service")
          .should().dependOnClassesThat()
          .resideInAPackage("org.springframework.web..");
}
