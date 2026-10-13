package shop;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;

class PasswordPolicyTest {
  private final PasswordPolicy policy = new PasswordPolicy();

  @Test void shortPasswordIsReported() {
    assertThat(policy.problems("Abc1"))
        .containsExactly("at least 12 characters");
  }

  @Test void passwordWithoutDigitIsReported() {
    assertThat(policy.problems("Abcdefghijkl"))
        .containsExactly("a digit");
  }

  @Test void passwordWithoutUpperCaseIsReported() {
    assertThat(policy.problems("abcdefghijk1"))
      .containsExactly("an upper-case letter");
  }

  @Test void strongPasswordHasNoProblems() {
    assertThat(policy.problems("Correct-Horse-7")).isEmpty();
  }
}
