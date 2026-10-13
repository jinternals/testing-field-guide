package shop;

import java.util.ArrayList;
import java.util.List;

/** Built test-first: see the TDD walk-through. */
public class PasswordPolicy {
  public List<String> problems(String password) {
    List<String> problems = new ArrayList<>();
    if (password.length() < 12)
      problems.add("at least 12 characters");
    if (password.chars().noneMatch(Character::isDigit))
      problems.add("a digit");
    if (password.chars().noneMatch(Character::isUpperCase))
      problems.add("an upper-case letter");
    return problems;
  }
}
