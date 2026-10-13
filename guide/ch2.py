from lib import *

C = CH["2"]

# ============================================================================
# CH2 · junit
# ============================================================================
def arch():
    b = []
    b.append('<rect x="8" y="8" width="504" height="34" rx="6" fill="#0F172A"/>')
    b.append('<text x="20" y="22" font-size="9.5" font-weight="700" fill="#fff">JUnit Platform</text>')
    b.append('<text x="20" y="34" font-size="7.5" fill="#CBD5E1">launcher · discovery · console · used by Maven Surefire, Gradle, IntelliJ, Eclipse, VS Code</text>')
    engines = [("Jupiter", "the @Test API used in this guide", C, True),
               ("Vintage", "runs JUnit 4 tests · deprecated", "#5B6474", False),
               ("Others", "Cucumber, jqwik, ArchUnit…", "#0E7490", False)]
    for i, (n, d, c, main) in enumerate(engines):
        x = 8 + i * 170
        b.append(f'<line x1="{x + 82}" y1="42" x2="{x + 82}" y2="56" stroke="#94A3B8"/>')
        b.append(f'<rect x="{x}" y="56" width="164" height="36" rx="6" fill="{c}" fill-opacity="{.14 if main else .08}" stroke="{c}"/>')
        b.append(f'<text x="{x + 10}" y="71" font-size="9.5" font-weight="700" fill="{c}">{n} engine</text>')
        b.append(f'<text x="{x + 10}" y="84" font-size="7.2" fill="#334155">{d}</text>')
    return svg("".join(b), 520, 98, "JUnit architecture: the JUnit Platform launches test engines. Jupiter is the main API; Vintage runs JUnit 4 tests and is deprecated; other engines include Cucumber and jqwik.")

ANN = [("@Test", "A test method. No return value, not private."),
       ("@ParameterizedTest", "Runs once per set of arguments (see p.@@params@@)."),
       ("@BeforeEach / @AfterEach", "Run around <b>every</b> test: fresh fixtures, clean-up."),
       ("@BeforeAll / @AfterAll", "Once per class; <code>static</code> unless <code>@TestInstance(PER_CLASS)</code>."),
       ("@DisplayName", "Readable name in reports, any text or emoji."),
       ("@Nested", "Inner class that groups related tests and shares setup."),
       ("@Tag(\"slow\")", "Label for filtering what runs, e.g. in CI stages."),
       ("@Disabled(\"why\")", "Skip, with a reason. Prefer fixing or deleting."),
       ("@TempDir", "Inject a fresh temporary directory, deleted afterwards."),
       ("@ExtendWith", "Plug in an extension, e.g. <code>MockitoExtension</code>."),]
ann = "".join(f'<tr><td class="hn" style="color:{C}">{a}</td><td>{b}</td></tr>' for a, b in ANN)
lifecycle_out = "\n".join(capture("suite-output.txt").split("\n")[:10])

POM = """<dependencyManagement>
  <dependencies>
    <dependency>
      <groupId>org.junit</groupId>
      <artifactId>junit-bom</artifactId>
      <version>6.1.3</version>
      <type>pom</type>
      <scope>import</scope>
    </dependency>
  </dependencies>
</dependencyManagement>

<dependencies>
  <dependency>
    <groupId>org.junit.jupiter</groupId>
    <artifactId>junit-jupiter</artifactId>
    <scope>test</scope>
  </dependency>
  <dependency>
    <groupId>org.assertj</groupId>
    <artifactId>assertj-core</artifactId>
    <version>3.27.7</version>
    <scope>test</scope>
  </dependency>
  <dependency>
    <groupId>org.mockito</groupId>
    <artifactId>mockito-junit-jupiter</artifactId>
    <version>5.24.0</version>
    <scope>test</scope>
  </dependency>
</dependencies>"""
GRADLE = """dependencies {
  testImplementation(platform("org.junit:junit-bom:6.1.3"))
  testImplementation("org.junit.jupiter:junit-jupiter")
  testRuntimeOnly("org.junit.platform:junit-platform-launcher")
  testImplementation("org.assertj:assertj-core:3.27.7")
  testImplementation("org.mockito:mockito-junit-jupiter:5.24.0")
}

tasks.test {
  useJUnitPlatform()
}"""
MIG = [("@Before / @After", "@BeforeEach / @AfterEach"), ("@BeforeClass / @AfterClass", "@BeforeAll / @AfterAll"),
       ("@Ignore", "@Disabled"), ("@Category(Slow.class)", "@Tag(\"slow\")"), ("@RunWith(…)", "@ExtendWith(…)"),
       ("@Rule / @ClassRule", "@ExtendWith or @RegisterExtension"), ("@Test(expected = X.class)", "assertThrows(X.class, …)"),
       ("@Test(timeout = 500)", "@Timeout(value = 500, unit = MILLISECONDS)"), ("assertEquals(msg, exp, act)", "assertEquals(exp, act, msg) — message last"),
       ("public class / public void", "package-private is enough")]
mig = "".join(f'<tr><td class="hn">{a}</td><td class="hn" style="color:{C}">{b}</td></tr>' for a, b in MIG)

page("setup", f'''
{head("02", "Chapter two", "Unit testing with JUnit 6", "JUnit is the standard test framework for Java. Version 6 (30 September 2025) keeps the JUnit 5 programming model — the <code>org.junit.jupiter</code> API — and raises the floor to Java 17. Every test in this guide ran on JUnit 6.1.3, Mockito 5.24.0 and AssertJ 3.27.7 on Java 21.", C)}
<h2>How the pieces fit</h2>
{arch()}
<div class="two top" style="grid-template-columns:1fr 1fr;margin-top:1mm">
  <div>
    <h2 style="margin-top:2mm">Maven</h2>
    {code(POM, "pom.xml — test dependencies", kind="xml", cls="xs")}
  </div>
  <div>
    <h2 style="margin-top:2mm">Gradle (Kotlin DSL)</h2>
    {code(GRADLE, "build.gradle.kts", kind="java", cls="xs")}
    <h2>Coming from JUnit 4</h2>
    <table class="tbl xs mig"><thead><tr><th>JUnit 4</th><th>JUnit 5 / 6</th></tr></thead><tbody>{mig}</tbody></table>
  </div>
</div>


<p class="small muted" style="margin-top:1.4mm"><code>junit-jupiter</code> bundles the API, the parameterized-test module and the engine. <code>mockito-junit-jupiter</code> brings <code>mockito-core</code> with it. Run with <code>mvn test</code> or <code>./gradlew test</code>; one class with <code>mvn test -Dtest=MoneyTest</code>.</p>
''', chapter="02 · Unit testing with JUnit 6", color=C, bm="02 · Unit testing with JUnit 6")

page("junit", f'''
{sub("02 · Unit testing with JUnit 6", "Your first test &amp; the lifecycle", C)}
<div class="two top" style="grid-template-columns:1fr 1fr">
  <div>
    {code(jfile("MoneyTest.java", end="error.getMessage());\n  }") + "\n\n  // addsAndMultiplies() is shown on p.@@assert@@\n}", "MoneyTest.java", cls="xs", right="✔ 3 / 3 passed")}
    <p class="small" style="margin-top:1.6mm">The class under test is a small <code>Money</code> record (₹, two decimals). Test classes and methods can be package-private; JUnit finds any method annotated with <code>@Test</code>.</p>
  </div>
  <div>
    <h2 style="margin-top:0">The annotations you’ll use daily</h2>
    <table class="tbl xs ann"><tbody>{ann}</tbody></table>
  </div>
</div>
<h2>Lifecycle, observed</h2>
<div class="two top" style="grid-template-columns:1.5fr 1fr;gap:3mm">
  {code(jfile("LifecycleTest.java"), "LifecycleTest.java", cls="xs")}
  {code(lifecycle_out, "real output", kind="out", cls="xs")}
</div>
<div class="two" style="margin-top:1.4mm">
  {ticks(["<b>A new instance per test method</b>, so fields can’t leak state between tests.",
          "<b>Order is deterministic but deliberately not obvious</b> — here <code>second()</code> ran first. Never depend on it."], C)}
  {ticks(["Need an order? <code>@TestMethodOrder(OrderAnnotation.class)</code> — mostly for slow, staged integration tests.",
          "<code>@TestInstance(PER_CLASS)</code> reuses one instance, so <code>@BeforeAll</code> need not be static."], C)}
</div>

<h2>What changed in JUnit 6</h2>
{table(["Change", "What it means for you"], [
    ("Java 17 minimum", "Projects on older JDKs stay on JUnit 5.14.x until they upgrade."),
    ("One version for everything", "Platform, Jupiter and Vintage now share one number, so the BOM is simpler."),
    ("Vintage deprecated", "JUnit 4 tests still run, but the engine flags them at discovery; plan the migration."),
    ("Quoted text arguments", "Parameterized names show <code>&quot;1000&quot;</code>; turn off with <code>quoteTextArguments = false</code>."),
    ("CSV parsing via FastCSV", "<code>@CsvSource</code> is stricter: characters after a closing quote are now an error."),
], "xs")}
''', chapter="02 · Unit testing with JUnit 6", color=C)

# ============================================================================
# CH2 · assert
# ============================================================================
ASSERTS = [("assertEquals(expected, actual)", "Uses <code>equals()</code>. Expected first!"),
           ("assertTrue / assertFalse", "For booleans; message explains little."),
           ("assertNull / assertNotNull", "Null checks."),
           ("assertSame", "Same object reference (<code>==</code>)."),
           ("assertIterableEquals", "Same elements, same order."),
           ("assertThrows(Type, code)", "Returns the exception for further checks."),
           ("assertThrowsExactly", "Exact type, not a subclass."),
           ("assertDoesNotThrow", "Documents that code must not fail."),
           ("assertAll(…)", "Runs every check and reports all failures."),
           ("assertTimeout(Preemptively)", "Fails when slower than a limit."),
           ("assertInstanceOf", "Type check that returns the cast value.")]
asr = "".join(f'<tr><td class="hn" style="color:{C}">{a}</td><td>{b}</td></tr>' for a, b in ASSERTS)

page("assert", f'''
{sub("02 · Unit testing with JUnit 6", "Assertions &amp; AssertJ", C)}
<p class="lede-s">An assertion is the test’s oracle. JUnit’s <code>Assertions</code> class covers the basics; <b>AssertJ</b> adds a fluent style — type <code>assertThat(x).</code> and your IDE lists every check that makes sense for <code>x</code> — and much clearer failure messages.</p>
<div class="two top" style="grid-template-columns:1fr 1.08fr">
  <div>
    <h2 style="margin-top:0">JUnit assertions</h2>
    <table class="tbl xs"><tbody>{asr}</tbody></table>
  </div>
  <div>
    <h2 style="margin-top:0">Exceptions and grouped checks</h2>
    {code(jfile("MoneyTest.java", "  @Test\n  void rejectsNegativeAmounts", "m.toString()));\n  }", dedent=2), "MoneyTest.java", cls="xs", right="✔ both pass")}
    <h2>The same ideas in AssertJ</h2>
    {code(jfile("ItemTest.java", "    void rejected", "\"quantity\");\n    }", dedent=4), "ItemTest.java", cls="xs")}
  </div>
</div>
<h2>Failure messages are the real product</h2>
<p class="small" style="margin-bottom:2mm">A test earns its keep the day it fails. These are the exact messages JUnit and AssertJ printed when we broke an expectation on purpose:</p>
<div style="display:grid;grid-template-columns:1fr 1.15fr;gap:1.6mm 3mm;align-items:start">
  {code('assertEquals(Money.of("900.00"),\n    Money.of("999.99").percentOff(10));', "assertEquals", cls="xs")}
  {code(fail_block("a_assertEquals"), "JUnit says", kind="out", cls="xs wrap")}
  {code('assertAll("arithmetic",\n  () -> assertEquals(Money.of("25.00"), m.times(3)),\n  () -> assertEquals("Rs 12.50", m.toString()));', "assertAll", cls="xs")}
  {code(fail_block("b_assertAll").replace("org.opentest4j.", ""), "JUnit says — both failures", kind="out", cls="xs wrap")}
  {code('assertThat(List.of("PEN", "BOOK", "TV"))\n    .containsExactly("PEN", "TV", "BOOK");', "AssertJ", cls="xs")}
  {code(fail_block("c_assertj"), "AssertJ says", kind="out", cls="xs wrap")}
</div>
<div class="two" style="margin-top:1.5mm">
  {note("Put <b>expected first</b> in <code>assertEquals(expected, actual)</code>. Swapped arguments still fail correctly, but the message lies about which value was wrong. AssertJ avoids the problem: <code>assertThat(actual).isEqualTo(expected)</code>.", "warn")}
  {note("Compare <b>money with <code>BigDecimal</code></b> and a fixed scale. <code>new BigDecimal(&quot;1.0&quot;).equals(new BigDecimal(&quot;1.00&quot;))</code> is <code>false</code>; that’s why <code>Money</code> always calls <code>setScale(2)</code>.", "tip")}
</div>
''', chapter="02 · Unit testing with JUnit 6", color=C)

# ============================================================================
# CH2 · params
# ============================================================================
SOURCES = [("@ValueSource(ints = {0, -1})", "One literal argument per run"),
           ("@NullAndEmptySource", "Adds <code>null</code> and <code>\"\"</code>/empty collection"),
           ("@EnumSource(Status.class)", "Every enum constant, or a filtered set"),
           ("@CsvSource({\"a, 1\"})", "Several arguments per row, inline"),
           ("@CsvFileSource(\"/cases.csv\")", "Rows from a CSV file on the classpath"),
           ("@MethodSource(\"cases\")", "A static factory returning <code>Stream&lt;Arguments&gt;</code>"),
           ("@FieldSource(\"cases\")", "A static field holding the arguments (JUnit 5.11+)"),
           ("@ArgumentsSource(My.class)", "Your own reusable <code>ArgumentsProvider</code>")]
src = "".join(f'<tr><td class="hn" style="color:{C}">{a}</td><td>{b}</td></tr>' for a, b in SOURCES)

MORE = [("Tags &amp; filtering", "<code>@Tag(\"slow\")</code> on a class or method, then <code>mvn test -Dgroups=fast</code> or <code>-DexcludedGroups=slow</code>."),
        ("Assumptions", "<code>assumeTrue(isCi())</code> aborts (skips) the test instead of failing it when a precondition doesn’t hold."),
        ("Conditional tests", "<code>@EnabledOnOs(LINUX)</code>, <code>@EnabledForJreRange(min = JAVA_21)</code>, <code>@EnabledIfEnvironmentVariable</code>."),
        ("Timeouts", "<code>@Timeout(5)</code> on a method or class; <code>assertTimeoutPreemptively</code> for one block (see p.@@tricky@@)."),
        ("Temp files", "<code>@TempDir Path dir</code> gives each test a fresh folder and deletes it afterwards."),
        ("Extensions", "<code>@ExtendWith</code> / <code>@RegisterExtension</code> hook into the lifecycle: Mockito, Spring, Testcontainers all work this way.")]
more = "".join(f'<div class="card"><b class="h">{a}</b>{b}</div>' for a, b in MORE)

page("params", f'''
{sub("02 · Unit testing with JUnit 6", "Parameterized, nested &amp; more", C)}
<p class="lede-s">When several tests differ only in their data, write one parameterized test. Each row becomes its own entry in the report, so you see exactly which case failed.</p>
<div class="two top" style="grid-template-columns:1.42fr 1fr;gap:3mm">
  {code(jfile("ItemTest.java"), "ItemTest.java — @Nested + @MethodSource + @ValueSource", cls="xs")}
  <div>
    {code(suite_tree("Item"), "real output", kind="out", cls="xs", right="6 / 6 passed")}
    {note("JUnit 6 prints text arguments in quotes, and <code>@CsvSource</code> values count as text — even numbers. <code>quoteTextArguments = false</code> keeps names like <b>₹1000 → 5% off</b>.", "info", "JUnit 6 change")}
    {note("Keep each row <b>one behaviour</b>. If rows need different assertions, they are different tests.", "rule")}
  </div>
</div>
<h2>Argument sources</h2>
<div class="two">
  <table class="tbl xs"><tbody>{"".join(f'<tr><td class="hn" style="color:{C}">{a}</td><td>{b}</td></tr>' for a, b in SOURCES[:4])}</tbody></table>
  <table class="tbl xs"><tbody>{"".join(f'<tr><td class="hn" style="color:{C}">{a}</td><td>{b}</td></tr>' for a, b in SOURCES[4:])}</tbody></table>
</div>
<h2>More tools in the box</h2>
<div class="three">{more}</div>
''', chapter="02 · Unit testing with JUnit 6", color=C)
