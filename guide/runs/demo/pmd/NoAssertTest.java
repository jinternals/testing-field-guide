package shop;
import org.junit.jupiter.api.Test;
class NoAssertTest {
  @Test void runsButChecksNothing() { new java.util.ArrayList<String>().add("x"); }
}
