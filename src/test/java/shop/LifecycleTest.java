package shop;

import org.junit.jupiter.api.*;

class LifecycleTest {
  static void log(String s) { System.out.println(s); }

  LifecycleTest() { log("  new LifecycleTest()"); }

  @BeforeAll static void beforeAll() { log("@BeforeAll"); }
  @BeforeEach void beforeEach()      { log("  @BeforeEach"); }

  @Test void first()                 { log("    first()"); }
  @Test void second()                { log("    second()"); }

  @AfterEach void afterEach()        { log("  @AfterEach"); }
  @AfterAll static void afterAll()   { log("@AfterAll"); }
}
