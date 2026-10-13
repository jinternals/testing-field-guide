from lib import *

C = CH["6"]

# ============================================================================
# CH6 · tdd
# ============================================================================
def cycle():
    b = [ARROW.format(id="ca", c="#475569")]
    pts = [("RED", "Write a failing test", "#B91C1C", 95, 18), ("GREEN", "Make it pass, simply", "#047857", 170, 108), ("REFACTOR", "Clean up, stay green", "#1D4ED8", 20, 108)]
    for t, s_, c, x, y in pts:
        b.append(f'<rect x="{x}" y="{y}" width="110" height="40" rx="20" fill="{c}" fill-opacity=".07" stroke="{c}" stroke-width="1.4"/>')
        b.append(f'<text x="{x + 55}" y="{y + 18}" text-anchor="middle" font-size="10.5" font-weight="800" fill="{c}" letter-spacing="1">{t}</text>')
        b.append(f'<text x="{x + 55}" y="{y + 31}" text-anchor="middle" font-size="7.5" fill="#334155">{s_}</text>')
    b.append('<path d="M195,50 Q235,70 230,104" fill="none" stroke="#475569" stroke-width="1.2" marker-end="url(#ca)"/>')
    b.append('<path d="M168,128 L134,128" fill="none" stroke="#475569" stroke-width="1.2" marker-end="url(#ca)"/>')
    b.append('<path d="M60,104 Q55,70 93,46" fill="none" stroke="#475569" stroke-width="1.2" marker-end="url(#ca)"/>')
    b.append('<text x="150" y="88" text-anchor="middle" font-size="7.5" fill="#5B6474">minutes per loop</text>')
    return svg("".join(b), 300, 156, "The TDD cycle: red, write a failing test; green, make it pass in the simplest way; refactor, clean up while staying green; then repeat.")

GHERKIN = """Feature: Order discounts
  Scenario: Orders of ₹1000 or more get 5% off
    Given a cart with 2 books at ₹600 each
    When the customer places the order
    Then the order total is ₹1140.00
    And a confirmation e-mail is sent"""

_red = capture("demo-output.txt").split("===== TDD step 1 (red) =====")[1].split("Failures (3)")[0]
_lines = [l for l in _red.split("\n") if "--" in l]
_first = _red.split("shortPasswordIsReported() [X]")[1].split("+--")[0]
red_out = "\n".join(_lines).replace("'-- JUnit Jupiter [OK]", "JUnit Jupiter") + "\n\nshortPasswordIsReported():" + "\n".join(re.sub(r"^\s*\|\s{5}", "  ", l) for l in _first.rstrip().split("\n"))

page("tdd", f'''
{head("06", "Chapter six", "Quality &amp; process", "Tests are only as useful as the habits around them: when you write them, how you know they are good enough, and how they run on every change. This chapter covers TDD, coverage, mutation testing, CI — and questions to check your understanding of all of it.", C)}
<h2>Test-driven development</h2>
<div class="two top" style="grid-template-columns:.9fr 1.1fr">
  {cycle()}
  <div>
    <p class="small">Kent Beck’s <em>Test-Driven Development: By Example</em> (2002) describes a short loop: write a test for behaviour that doesn’t exist yet, watch it fail, write just enough code to pass, then improve the design while the tests stay green.</p>
    {ticks(["<b>Red first</b> proves the test can fail — a test that never failed may not test anything.",
            "<b>Simplest code</b> that passes, even if it looks naive; the next test forces the real logic.",
            "<b>Refactor</b> both code and tests; the tests are your safety net."], C)}
  </div>
</div>
<h2>A real TDD loop: <code>PasswordPolicy</code></h2>
<div class="two top" style="gap:3.5mm">
  <div>
    {code(jfile("demo/tdd/shop/PasswordPolicy.java", "public class"), "step 1 · tests written, class just compiles", cls="xs")}
    <div style="height:1.6mm"></div>
    {code(red_out, "real output · RED", kind="out", cls="xs", right="3 failed")}
  </div>
  <div>
    {code(jfile("PasswordPolicy.java", "public class", test=False), "step 2 · just enough code", cls="xs")}
    <div style="height:1.6mm"></div>
    {code(suite_tree("PasswordPolicyTest"), "real output · GREEN", kind="out", cls="xs", right="4 / 4 passed")}
    <p class="small" style="margin-top:1.4mm"><b>Step 3 · refactor:</b> with all four green, we could pull the rules into a list of <code>(predicate, message)</code> pairs — and re-run to prove nothing changed.</p>
  </div>
</div>
<p class="small muted" style="margin-top:1.2mm">Honest note: we wrote all four tests before the code, so three failed at once. Strict TDD adds one test at a time. The strong-password test passed even in the red step, because an empty list happens to be its right answer — a reminder to watch <em>each</em> new test fail before trusting it.</p>
<h2>BDD: tests in the customer’s words</h2>
<div class="two top">
  {code(GHERKIN, "orders.feature · Gherkin example", kind="plain", cls="xs")}
  <p class="small">Behaviour-driven development writes acceptance tests as <b>Given / When / Then</b> scenarios that product owners can read. Cucumber-JVM maps each line to a Java step method. Worth it when non-developers really read and write the scenarios; otherwise plain JUnit tests with good names are cheaper.</p>
</div>
''', chapter="06 · Quality &amp; process", color=C, bm="06 · Quality &amp; process")

# ============================================================================
# CH6 · cov
# ============================================================================
COUNTERS = [("Instructions", "C0", "Java bytecode instructions executed — the finest grain"),
            ("Branches", "C1", "Both outcomes of every <code>if</code> and <code>switch</code> case"),
            ("Lines", "", "A line counts as covered when at least one of its instructions ran"),
            ("Complexity", "", "Cyclomatic complexity: paths that would need tests"),
            ("Methods / classes", "", "Executed at least once")]
cnt = "".join(f'<tr><td class="nm">{a}</td><td class="hn">{b}</td><td>{c}</td></tr>' for a, b, c in COUNTERS)

MUT = [("CONDITIONALS_BOUNDARY", "<code>&lt;</code> ↔ <code>&lt;=</code>, <code>&gt;=</code> ↔ <code>&gt;</code>"), ("NEGATE_CONDITIONALS", "<code>==</code> ↔ <code>!=</code>, <code>&lt;</code> ↔ <code>&gt;=</code>"),
       ("MATH", "<code>+</code> ↔ <code>-</code>, <code>*</code> ↔ <code>/</code>"), ("INCREMENTS", "<code>i++</code> ↔ <code>i--</code>"),
       ("INVERT_NEGS", "<code>-x</code> → <code>x</code>"), ("VOID_METHOD_CALLS", "removes a call to a void method"),
       ("…_RETURNS", "empty, null, true/false and 0 returns")]
mut = "".join(f'<tr><td class="hn" style="color:{C}">{a}</td><td>{b}</td></tr>' for a, b in MUT)

demo = capture("demo-output.txt")
weak_out = demo.split("===== MUTANT: weak tests =====")[1].split("Test run finished")[0].strip().split("\n", 1)[1].replace("'-- JUnit Jupiter [OK]", "JUnit Jupiter").strip()
strong_out = demo.split("===== MUTANT: boundary tests =====")[1].split("Failures (1)")[0].strip().split("\n", 1)[1].replace("'-- JUnit Jupiter [OK]", "JUnit Jupiter").strip()
diff = """-    if (subtotal.compareTo(Money.of("1000")) >= 0) return 5;
+    if (subtotal.compareTo(Money.of("1000")) > 0) return 5;"""

page("cov", f'''
{sub("06 · Quality &amp; process", "Coverage &amp; mutation testing", C)}
<div class="two top">
  <div>
    <h2 style="margin-top:0">Code coverage (JaCoCo)</h2>
    <table class="tbl xs"><tbody>{cnt}</tbody></table>
    <p class="small" style="margin-top:1.4mm">Coverage tells you what the tests <b>ran</b>, not what they <b>checked</b>. A test with no assertions can reach 100%. Use it to find untested code, not as a score to chase.</p>
  </div>
  <div>
    <h2 style="margin-top:0">Mutation testing (PIT)</h2>
    <p class="small">A tool changes your code in small ways — a <b>mutant</b> — and re-runs the tests. If they still pass, the mutant <b>survived</b>: your tests missed a bug. Mutation score = killed ÷ total. The idea goes back to Lipton (1971) and DeMillo, Lipton &amp; Sayward (1978).</p>
    <table class="tbl xs" style="margin-top:1.4mm"><tbody>{mut}</tbody></table>
  </div>
</div>
<h2>A mutant, by hand: does the test suite notice?</h2>
<div class="two top" style="gap:3.5mm;grid-template-columns:1.2fr 1fr">
  <div>
    {code(jfile("demo/weak/shop/WeakDiscountPolicyTest.java", "/**"), "WeakDiscountPolicyTest.java", cls="xs")}
    <div style="height:1.6mm"></div>
    {code(diff, "the mutant · CONDITIONALS_BOUNDARY", kind="plain", cls="xs")}
  </div>
  <div>
    {code(weak_out, "weak tests vs MUTANT · real output", kind="out", cls="xs", right="mutant survived")}
    <div style="height:1.6mm"></div>
    {code(strong_out, "boundary tests (p.@@design@@) vs MUTANT", kind="out", cls="xs", right="mutant killed")}
  </div>
</div>
<p class="small" style="margin-top:1.6mm">The weak tests execute every line and both outcomes of each <code>if</code>, so line and branch coverage are both 100% — yet they let the bug through. The boundary test at exactly ₹1000 kills it. PIT does this automatically for thousands of mutants: <code>mvn test-compile org.pitest:pitest-maven:mutationCoverage</code> (pitest-maven 1.30.0, with the <code>pitest-junit5-plugin</code> for JUnit 5/6 tests).</p>
<h2>Test smells to refactor away</h2>
{table(["Smell", "Looks like", "Fix"], [
    ("Assertion-free test", "Calls code, checks nothing — still counts as coverage", "Assert the outcome, or delete the test"),
    ("Eager test", "One test checks five behaviours; the name says “testOrder”", "Split it: one behaviour, one name"),
    ("Mystery guest", "Expected values come from a file or DB row you can’t see", "Build the data inside the test (builders)"),
    ("Fragile test", "Breaks on harmless refactors; verifies every internal call", "Assert results, not implementation steps"),
    ("Sleepy test", "<code>Thread.sleep</code> to wait for async work", "Wait for a condition with a timeout"),
], "xs")}
{note("Run mutation testing where it matters — pricing, permissions, money — or only on files changed in a pull request; it re-runs tests for every mutant, so it is slow.", "rule")}
''', chapter="06 · Quality &amp; process", color=C)

# ============================================================================
# CH6 · ci
# ============================================================================
def pipeline():
    st = [("Compile &amp;", "static checks", LV["static"]), ("Unit tests", "Surefire", LV["unit"]), ("Integration", "Failsafe + containers", LV["integration"]),
          ("Package", "image / jar", "#334155"), ("Staging", "e2e smoke · DAST", LV["e2e"]), ("Production", "smoke · monitor", CH["6"])]
    b = [ARROW.format(id="pa2", c="#475569")]
    w, gap = 78, 10
    for i, (t, s_, c) in enumerate(st):
        x = 6 + i * (w + gap)
        b.append(f'<rect x="{x}" y="10" width="{w}" height="38" rx="6" fill="{c}" fill-opacity=".07" stroke="{c}"/>')
        b.append(f'<text x="{x + w/2}" y="26" text-anchor="middle" font-size="8.6" font-weight="700" fill="{c}">{t}</text>')
        b.append(f'<text x="{x + w/2}" y="39" text-anchor="middle" font-size="6.8" fill="#334155">{s_}</text>')
        if i < len(st) - 1:
            b.append(f'<line x1="{x + w}" y1="29" x2="{x + w + gap - 1}" y2="29" stroke="#475569" marker-end="url(#pa2)"/>')
    b.append('<text x="6" y="62" font-size="7" fill="#5B6474">← every push, minutes · fail fast</text>')
    b.append('<text x="534" y="62" text-anchor="end" font-size="7" fill="#5B6474">nightly: full e2e, performance, mutation, DAST →</text>')
    return svg("".join(b), 540, 66, "CI pipeline: compile and static checks, unit tests with Surefire, integration tests with Failsafe and containers, package, staging with end-to-end smoke tests and DAST, production with smoke tests and monitoring.")

PAR = capture("config/junit-platform.properties").strip()
par = capture("parallel-output.txt")
seq_t = re.findall(r"# sequential\n((?:Test run.*\n)+)", par)[0].strip().split("\n")
par_t = [l for l in par.split("# parallel")[1].split("\n") if l.startswith("Test run")]
ms = lambda l: int(re.search(r"(\d+) ms", l).group(1))
seq_ms = sorted(ms(l) for l in seq_t); par_ms = sorted(ms(l) for l in par_t)
PAR_CPUS = re.search(r"# cpus: (\d+)", par).group(1)

GHA = """name: build
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-java@v6
        with: { distribution: temurin, java-version: '21', cache: maven }
      - run: ./mvnw -B verify   # unit + integration
      - uses: actions/upload-artifact@v7
        if: always()            # keep reports on failure
        with: { name: test-reports, path: '**/target/*-reports/*.xml' }"""

page("ci", f'''
{sub("06 · Quality &amp; process", "Build tools &amp; CI pipelines", C)}
{pipeline()}
<div class="two top" style="margin-top:2mm">
  <div>
    <h2 style="margin-top:0">Maven: Surefire and Failsafe</h2>
    {table(["", "Surefire", "Failsafe"], [
        ("Runs in phase", "<code>test</code>", "<code>integration-test</code>, then <code>verify</code> fails the build"),
        ("Default class names", "<code>Test*</code>, <code>*Test</code>, <code>*Tests</code>, <code>*TestCase</code>", "<code>IT*</code>, <code>*IT</code>, <code>*ITCase</code>"),
        ("Use for", "Fast unit tests", "Tests needing a started app, DB or containers"),
        ("Command", "<code>mvn test</code>", "<code>mvn verify</code> — so <code>post-integration-test</code> clean-up runs")], "xs")}
    <p class="small" style="margin-top:1.4mm">Both are at version 3.6.0. With Gradle, register a second <code>Test</code> task (or use the JVM Test Suite plugin) for integration tests.</p>
  </div>
  <div>
    <h2 style="margin-top:0">Run tests in parallel</h2>
    {code(PAR, "junit-platform.properties", kind="props", cls="xs")}
    <p class="small" style="margin-top:1.4mm">Our {N_TESTS} tests on {PAR_CPUS} CPUs, three runs each: sequential <b>{seq_ms[0]:,}–{seq_ms[-1]:,} ms</b>, parallel <b>{par_ms[0]:,}–{par_ms[-1]:,} ms</b>, all passing. Parallel runs only work if tests share no state — a good test of your tests.</p>
  </div>
</div>
<h2>Where should this test live? A Spring Boot service</h2>
{table(["What you’re checking", "Level", "Tooling"], [
    ("Pricing, validation, state rules", lv("unit"), "JUnit + AssertJ, real value objects, no Spring"),
    ("Service orchestration (charge → save → e-mail)", lv("unit"), "Mockito for ports: gateway, repository, mailer"),
    ("URL mapping, JSON shape, validation errors, status codes", lv("integration"), "<code>@WebMvcTest</code> + <code>MockMvcTester</code> + <code>@MockitoBean</code>"),
    ("SQL, mappings, migrations, transactions", lv("integration"), "<code>@DataJpaTest</code> + Testcontainers (same DB as prod)"),
    ("Outbound HTTP client: timeouts, errors, parsing", lv("integration"), "WireMock or <code>@RestClientTest</code>"),
    ("Agreement with another team’s service", lv("contract"), "Pact or Spring Cloud Contract"),
    ("Sign-up, checkout, payment journeys", lv("e2e", "end-to-end"), "Playwright against staging; a few smoke tests in prod"),
], "xs")}
<div class="two top" style="margin-top:2.4mm;grid-template-columns:1.45fr 1fr">
  {code(GHA, ".github/workflows/build.yml · sketch", kind="plain", cls="xs", right="not run here")}
  <div>
    <h2 style="margin-top:0">Pipeline habits</h2>
    {ticks(["<b>Fastest first.</b> Static checks and unit tests run before anything slow, so most failures arrive in minutes.",
            "<b>Every pull request</b> runs the full unit and integration suite; merging is blocked on red.",
            "<b>Keep reports</b> (JUnit XML, coverage, Playwright traces) as build artefacts, especially on failure.",
            "<b>Budget the time.</b> If the main build creeps past ~10 minutes, parallelise, split jobs or push slow suites to nightly.",
            "<b>Quarantine flaky tests</b> in a non-blocking job and fix them — never “retry until green”.",
            "<b>Show results in the pull request:</b> test, coverage and mutation summaries next to the diff get read; a link to a dashboard doesn’t."], C)}
  </div>
</div>
''', chapter="06 · Quality &amp; process", color=C)

# ============================================================================
# CH6 · interview
# ============================================================================
QA = [("Unit vs integration test?", "A unit test checks one class with its collaborators replaced, in memory and in milliseconds. An integration test checks your code together with real parts — database, HTTP, framework — and is slower but catches wiring and configuration bugs."),
      ("Mock vs stub?", "A stub returns canned answers so the code under test can run; you then check the result (state). A mock is set up with expectations about calls, which you verify (behaviour). Mockito objects can play either role."),
      ("What does <code>@InjectMocks</code> do?", "Creates the class under test and injects <code>@Mock</code>/<code>@Spy</code> fields by constructor, then setter, then field. It fails silently when it can’t inject — many teams prefer calling the constructor explicitly."),
      ("<code>when().thenReturn()</code> vs <code>doReturn().when()</code>?", "Use <code>doReturn</code> for spies (the <code>when</code> form calls the real method first) and <code>doThrow</code>/<code>doNothing</code> for void methods."),
      ("How do you test a private method?", "Through the public method that uses it. If that is too hard, the private logic probably wants to be its own class with its own tests."),
      ("How do you test code that uses the current time?", "Inject a <code>java.time.Clock</code>; production passes <code>Clock.systemUTC()</code>, tests pass <code>Clock.fixed(…)</code>."),
      ("What is a flaky test and how do you fix it?", "One that passes and fails without code changes. Find the uncontrolled input — time, randomness, order, shared state, network, sleeps — and control it; quarantine until fixed."),
      ("Is 100% coverage the goal?", "No. Coverage shows what ran, not what was checked. Use it to find untested code; use mutation testing to judge test strength."),
      ("<code>@BeforeEach</code> vs <code>@BeforeAll</code>?", "<code>@BeforeEach</code> runs before every test on a fresh instance; <code>@BeforeAll</code> runs once per class and must be static unless <code>@TestInstance(PER_CLASS)</code>."),
      ("Can Mockito mock final classes and statics?", "Yes. Since Mockito 5 the inline mock maker is the default, so final classes and methods work; statics need <code>mockStatic</code> in a try-with-resources block."),
      ("What is the test pyramid?", "Many fast unit tests, fewer integration tests, very few end-to-end tests — because cost and flakiness grow as tests get broader. The testing trophy puts more weight on integration tests."),
      ("How do you test a REST controller in Spring Boot?", "<code>@WebMvcTest</code> with <code>MockMvcTester</code> (or <code>MockMvc</code>) and <code>@MockitoBean</code> services for the web layer; <code>@SpringBootTest(webEnvironment = RANDOM_PORT)</code> plus Testcontainers for a full flow."),
      ("What is TDD and when is it worth it?", "Red–green–refactor in short loops. Most valuable for logic with clear rules (pricing, parsing, validation); less so for exploratory UI work."),
      ("How do you test exceptions in JUnit?", "<code>assertThrows(Type.class, () -&gt; …)</code> returns the exception so you can check its message; AssertJ offers <code>assertThatThrownBy(…)</code>. Avoid the JUnit 4 <code>@Test(expected = …)</code> style — it passes if <em>any</em> line throws."),
      ("What is mutation testing?", "A tool (PIT) makes small changes to your code — flips <code>&gt;=</code> to <code>&gt;</code>, removes a call — and re-runs the tests. Surviving mutants show where tests run code without really checking it."),
      ("How do you make tests run in parallel safely?", "Remove shared mutable state: no statics, unique test data, temp dirs, random ports. Then enable <code>junit.jupiter.execution.parallel.enabled</code>; use <code>@ResourceLock</code> for anything truly shared."),
      ("Surefire vs Failsafe?", "Surefire runs unit tests in the <code>test</code> phase (<code>*Test</code>). Failsafe runs integration tests (<code>*IT</code>) in <code>integration-test</code> and fails the build in <code>verify</code>, so clean-up still happens."),
      ("What do you test in a microservice architecture?", "Each service with unit and integration tests, the agreements between services with contract tests, and only a few critical journeys end to end."),
      ("How do you find duplicate or redundant tests?", "Run PIT with the full mutation matrix and compare which mutants each test kills; equal sets are merge candidates. Add copy-paste detection (PMD CPD, SonarQube) and review — boundary tests often look redundant but aren’t."),
      ("What is contract testing?", "Consumers publish the requests and responses they rely on; the provider’s build verifies them (Pact, Spring Cloud Contract). It replaces many slow end-to-end tests between services.")]
NUMQ = ["Zero","One","Two","Three","Four","Five","Six","Seven","Eight","Nine","Ten","Eleven","Twelve","Thirteen","Fourteen","Fifteen","Sixteen","Seventeen","Eighteen","Nineteen","Twenty","Twenty-one","Twenty-two"][len(QA)]
qa = "".join(f'<div class="q"><b><span>Q{i:02d}</span>{q}</b><p>{a}</p></div>' for i, (q, a) in enumerate(QA, 1))

page("interview", f'''
{sub("06 · Quality &amp; process", "Check your understanding", C)}
<p class="lede-s">{NUMQ} questions to check your understanding — for self-review, team discussions or onboarding. Each has a short answer to start from; the index points to the page that covers the topic in depth.</p>
<div class="qa">{qa}</div>
''', chapter="06 · Quality &amp; process", color=C)
