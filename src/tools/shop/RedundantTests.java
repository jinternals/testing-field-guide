package shop;

import java.nio.file.Path;
import java.util.*;
import java.util.regex.*;
import javax.xml.parsers.DocumentBuilderFactory;
import org.w3c.dom.*;

/**
 * Finds tests that kill the same mutants as another test, or a strict
 * subset of them. Input: PIT's mutations.xml from a run with
 * fullMutationMatrix=true. Plain JDK, no dependencies.
 */
public class RedundantTests {
  static final Pattern PART =
      Pattern.compile("\\[([\\w-]+):([^\\]]+)\\]");
  static final Set<String> NAMED =
      Set.of("class", "nested-class", "method", "test-template");

  public static void main(String[] args) throws Exception {
    Path xml = Path.of(args.length > 0
        ? args[0] : "target/pit-reports/mutations.xml");
    Map<String, Set<Integer>> kills = new HashMap<>();  // test -> mutants
    NodeList mutations = DocumentBuilderFactory.newInstance()
        .newDocumentBuilder().parse(xml.toFile())
        .getElementsByTagName("mutation");
    for (int i = 0; i < mutations.getLength(); i++) {
      Element m = (Element) mutations.item(i);
      String killing = m.getElementsByTagName("killingTests")
          .item(0).getTextContent();
      for (String t : killing.split("\\|")) {
        if (!t.isBlank())
          kills.computeIfAbsent(name(t), k -> new TreeSet<>()).add(i);
      }
    }

    List<String> tests = new ArrayList<>(kills.keySet());
    tests.sort(Comparator.comparing((String t) -> -kills.get(t).size())
        .thenComparing(Comparator.naturalOrder()));
    System.out.println(
        tests.size() + " tests kill at least one mutant\n");

    System.out.println(
        "Same mutants killed as another test (candidates for merging):");
    Map<Set<Integer>, List<String>> groups = new LinkedHashMap<>();
    for (String t : tests)
      groups.computeIfAbsent(kills.get(t), k -> new ArrayList<>()).add(t);
    for (List<String> g : groups.values())
      if (g.size() > 1)
        System.out.println("  " + String.join("  ≡  ", g) + "   ("
            + kills.get(g.get(0)).size() + " mutants)");

    System.out.println(
        "\nStrict subset of another test (adds no extra mutant kills):");
    for (String a : tests)
      for (String b : tests)
        if (!a.equals(b) && kills.get(b).containsAll(kills.get(a))
            && kills.get(b).size() > kills.get(a).size()) {
          System.out.printf("  %s (%d) ⊂ %s (%d)%n", a,
              kills.get(a).size(), b, kills.get(b).size());
          break;
        }
  }

  /** PIT test id -> "Class.Nested.method#invocation". */
  static String name(String testId) {
    StringJoiner name = new StringJoiner(".");
    String invocation = "";
    Matcher m = PART.matcher(testId);
    while (m.find()) {
      String kind = m.group(1), value = m.group(2);
      if (NAMED.contains(kind))
        name.add(value.split("\\(")[0].replace("shop.", ""));
      else if (kind.endsWith("invocation"))
        invocation = value;
    }
    return name + invocation;
  }
}
