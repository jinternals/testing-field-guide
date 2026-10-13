"""Chapter 6, part 3: duplicate tests, build plugins, parallel integration tests, singleton containers.
Every output on these pages comes from the GitHub Actions run of the example project (ci-logs/)."""
from lib import *

C = CH["6"]
CHAP = "06 · Quality &amp; process"
LOGS = JAVA / "ci-logs"
RUNNER = "/home/runner/work/testing-field-guide/testing-field-guide/"


def log(name):
    return (LOGS / name).read_text(errors="replace").replace(RUNNER, "")


def cut(text, start, end, include_end=True):
    i = text.index(start)
    j = text.index(end, i) + (len(end) if include_end else 0)
    return text[i:j]


def undent(s, n):
    return "\n".join(l[n:] if l[:n].strip() == "" else l for l in s.split("\n"))


POM = capture("pom.xml")
GRADLE = capture("build.gradle.kts")
MVN = log("maven/mvn.txt").split("\n")[0].split(" (")[0]            # "Apache Maven 3.10.0"
JDK = re.search(r'version "([^"]+)"', log("maven/java.txt")).group(1)
CPUS = log("maven/nproc.txt").strip()

# ============================================================================
# duplicate / redundant tests — Java checker, run from Maven or Gradle
# ============================================================================
red = capture("redundancy-java.txt")
mvn_exec = log("maven/maven-pit.log").split("exec:3.6.4:java (default-cli) @ shop ---\n")[1].split("[INFO] ---")[0]
gr_exec = log("gradle/gradle-pit.log").split("> Task :findRedundantTests\n")[1].split("gradle/actions:")[0]
norm = lambda s: [l for l in s.strip().split("\n") if l.strip()]
SAME = norm(mvn_exec) == norm(red) == norm(gr_exec)
assert SAME, "Maven, Gradle and local checker output differ"
eq = [l.strip() for l in red.split("candidates for merging):")[1].split("\n\nStrict")[0].strip().split("\n")]
sub_lines = [l.strip() for l in red.split("adds no extra mutant kills):")[1].strip().split("\n")]
ntests = re.search(r"(\d+) tests kill", red).group(1)
pit_stats = re.search(r"Generated (\d+) mutations Killed (\d+)", log("maven/maven-pit.log")).groups()

VERDICT = [
    ("ItemTest…rejected #1 ≡ #2 ≡ #3", "quantities 0, -1, MIN_VALUE", "<b class='part'>Redundant</b> — same partition. Keep 0 (the boundary) and one negative."),
    ("DiscountPolicyTest #4 ≡ #5", "₹4999.99 and ₹5000", "<b class='yes'>Keep both</b> — the two sides of a boundary."),
    ("PasswordPolicyTest digit ≡ upper-case", "two different rules", "<b class='yes'>Keep both</b> — they specify different rules."),
    ("OrderApiTest pathTricks ≡ unknownOrder", "both expect 404", "<b class='part'>Merge candidate</b> — the hostile-input loop already covers the plain 404."),
    ("Unit test ⊂ OrderServiceTest", "e.g. <code>MoneyTest</code>", "<b class='yes'>Keep</b> — a failing broad test doesn’t say <em>which</em> rule broke."),
]

CORE = jfile("src/tools/shop/RedundantTests.java", "    List<String> tests", "          break;\n        }", dedent=4)
CORE = CORE.replace("""System.out.println(
    tests.size() + " tests kill at least one mutant\\n");

""", "").replace("""System.out.println(
    "Same mutants killed as another test (candidates for merging):");
""", "").replace("""System.out.println(
    "\\nStrict subset of another test (adds no extra mutant kills):");
""", "")
EXECPOM = undent(cut(POM, "      <plugin>\n        <groupId>org.codehaus.mojo</groupId>\n        <artifactId>exec-maven-plugin", "      </plugin>"), 6)
JAVAEXEC = cut(GRADLE, 'tasks.register<JavaExec>("findRedundantTests")', "\n}")

page("dupes", f'''
{sub(CHAP, "Finding duplicate &amp; redundant tests", C)}
<p class="lede-s">Two tests duplicate each other when they <b>catch the same bugs</b>. Run PIT with <code>fullMutationMatrix=true</code> — it records every test that kills each mutant — then compare the tests’ kill sets. The comparison is a small Java class with no dependencies; Maven or Gradle runs it right after PIT.</p>
<div class="two top" style="grid-template-columns:1.32fr 1fr;gap:3mm">
  {code(CORE, "src/tools/shop/RedundantTests.java — comparing kill sets", cls="xs")}
  {code(f"{ntests} tests kill at least one mutant\n\nSame mutants killed:\n" + "\n".join("  " + l for l in eq) + f"\n\nStrict subset of another test: {len(sub_lines)} tests", "real output · identical from Maven and Gradle", kind="plain", cls="xs out wrap")}
</div>
<div class="two top" style="grid-template-columns:1fr 1.1fr;gap:3mm;margin-top:2mm">
  {code(EXECPOM, "pom.xml · mvn test-compile pitest:mutationCoverage exec:java", kind="xml", cls="xs")}
  {code(JAVAEXEC, "build.gradle.kts · gradle pitest findRedundantTests", kind="plain", cls="xs wrap")}
</div>
{note(f"Both builds ran on GitHub Actions ({MVN}, Gradle 9.8.1, JDK {JDK}): PIT killed {pit_stats[1]} of {pit_stats[0]} mutants and the checker printed the same report in both. Equal kill sets mean the tests <em>currently</em> catch the same bugs — not that they are the same test. Delete only when the inputs are in the same partition <em>and</em> the assertions are the same.", "warn")}
<h2>A human verdict on each match</h2>
{table(["Match", "What the tests are", "Verdict"], VERDICT, "xs")}
''', chapter=CHAP, color=C)

# ============================================================================
# build plugins for test quality
# ============================================================================
cpd_local = capture("cpd-output.txt")
cpd_n = dict(re.findall(r"--minimum-tokens (\d+) .*\n(\d+)", cpd_local))
mvn_cpd = log("maven/maven-cpd.log")
mvn_found = re.search(r"CPD [\d.]+ has found (\d+) duplications", mvn_cpd).group(1)
g_cpd = log("gradle/cpd/cpdCheck.text")
g_found = len(re.findall(r"^Found a", g_cpd, re.M))
first = g_cpd.split("=====")[0].strip()
first = "\n".join(l.rstrip() for l in first.split("\n") if l.strip())
asserts = capture("pmd-asserts-output.txt")

PLUG = [
    ("Unit tests", "maven-surefire-plugin <b>3.6.0</b>", "built-in <code>test</code> task", "<code>Test*</code>, <code>*Test</code>, <code>*Tests</code>, <code>*TestCase</code>"),
    ("Integration tests", "maven-failsafe-plugin <b>3.6.0</b>", "a second <code>Test</code> task", "<code>IT*</code>, <code>*IT</code>, <code>*ITCase</code>; fails in <code>verify</code>"),
    ("Extra test source dirs", "build-helper-maven-plugin <b>3.6.2</b>", "<code>sourceSets</code> (built-in)", "e.g. <code>src/it/java</code>"),
    ("Coverage", "jacoco-maven-plugin <b>0.8.15</b>", "<code>jacoco</code> (built-in)", "gate: <code>check</code> / <code>jacocoTestCoverageVerification</code>"),
    ("Mutation testing", "pitest-maven <b>1.30.0</b>", "<code>info.solidsoft.pitest</code> <b>1.19.0</b>", "gate: <code>mutationThreshold</code>"),
    ("Copy-paste in tests", "maven-pmd-plugin <b>3.28.0</b> · <code>cpd-check</code>", "<code>de.aaschmid.cpd</code> <b>3.5</b> · <code>cpdCheck</code>", "both use PMD’s CPD engine"),
    ("Tests that assert nothing", "maven-pmd-plugin · <code>check</code>", "<code>pmd</code> (built-in)", "rule <code>UnitTestShouldIncludeAssert</code>"),
    ("Bug patterns", "spotbugs-maven-plugin <b>4.10.5.0</b>", "<code>com.github.spotbugs</code> <b>6.5.13</b>", "null dereferences, bad <code>equals</code>, races"),
    ("Code style", "maven-checkstyle-plugin <b>3.6.0</b>", "<code>checkstyle</code> (built-in)", "keeps test code readable too"),
    ("Vulnerable dependencies", "dependency-check-maven <b>13.0.0</b>", "<code>org.owasp.dependencycheck</code> <b>13.0.0</b>", "OWASP Dependency-Check (SCA)"),
    ("Flaky-test retries", "Surefire <code>rerunFailingTestsCount</code>", "<code>org.gradle.test-retry</code> <b>1.6.6</b>", "reports a pass-on-retry as flaky"),
    ("Quality gate &amp; history", "sonar-maven-plugin <b>5.8.0.7211</b>", "<code>org.sonarqube</code> <b>7.5.0.8588</b>", "coverage and duplication on new code"),
]
CPDPOM = undent(cut(POM, "      <plugin>\n        <groupId>org.apache.maven.plugins</groupId>\n        <artifactId>maven-pmd-plugin", "      </plugin>"), 6)
CPDG = cut(GRADLE, "cpd {", "tasks.cpdCheck {\n  reports { text.required = true }\n}")

WHERE = [
    ("Every push", "unit tests, CPD, PMD, Checkstyle, SpotBugs", "seconds to a few minutes; fail fast"),
    ("Every pull request", "integration tests, coverage gate on new code, PIT on the changed module", "blocks the merge"),
    ("Nightly", "full PIT, Dependency-Check, duplicate-test report", "trends, not gates"),
]

page("plugins", f'''
{sub(CHAP, "Build plugins that guard test quality", C)}
<p class="lede-s">Everything in this chapter can run inside the build, so quality is checked on every change rather than when someone remembers. Versions are the latest releases at the time of writing.</p>
{table(["Concern", "Maven plugin", "Gradle plugin", "Notes"], PLUG, "xs")}
<h2>Copy-paste detection in test code — a real run</h2>
<div class="two top" style="grid-template-columns:1fr 1.1fr;gap:3mm">
  <div>
    {code(CPDPOM, "pom.xml · mvn generate-test-sources pmd:cpd-check", kind="xml", cls="xs")}
    <div style="height:2mm"></div>
    {code(CPDG, "build.gradle.kts · gradle cpdCheck", kind="plain", cls="xs")}
    <div style="height:2mm"></div>
    {code(asserts, "real output · PMD 7.17.0 · tests that assert nothing", kind="plain", cls="xs out wrap")}
  </div>
  <div>
    {code(first, f"real output · {g_found} duplications (Maven: {mvn_found})", kind="plain", cls="xs out")}
    {ticks([f"<b>The defaults miss test duplication.</b> Maven’s CPD skips tests unless <code>includeTests</code> is on, and needs 100 tokens; the Gradle plugin checks every source set at 50. On this project: <b>{cpd_n['100']}</b> duplications at 100 tokens, <b>{cpd_n['50']}</b> at 50, <b>{cpd_n['25']}</b> at 25.",
            "The finding above is real: our two singleton base classes (p.@@singleton@@) repeat <code>log()</code> and <code>uniqueId()</code> — a shared helper fixes it.",
            "Run alone, <code>pmd:cpd-check</code> skips the lifecycle, so folders added by build-helper are missed — our first run found 2, not 8. Run it after <code>generate-test-sources</code> or bind it to <code>verify</code>.",
            "Both fail the build on duplicates. PMD’s <code>UnitTestShouldIncludeAssert</code> rule (left) finds tests that check nothing.",
            "The Gradle CPD plugin (3.5, Nov 2024) prints Gradle 9 deprecation warnings."], C)}
  </div>
</div>
''', chapter=CHAP, color=C)

# ============================================================================
# parallel: threads for unit tests, JVMs for integration tests
# ============================================================================
def par_diagram():
    b = [ARROW.format(id="pp", c="#475569")]
    b.append('<rect x="4" y="16" width="200" height="104" rx="7" fill="#EFF6FF" stroke="#1D4ED8"/>')
    b.append('<text x="14" y="31" font-size="8.4" font-weight="700" fill="#1D4ED8">Surefire · unit tests</text>')
    b.append('<text x="14" y="43" font-size="7" fill="#334155">ONE JVM, many threads</text>')
    for i, n in enumerate(["MoneyTest", "ItemTest", "OrderServiceTest", "PasswordPolicyTest"]):
        y = 52 + i * 16
        b.append(f'<rect x="14" y="{y}" width="180" height="12" rx="3" fill="#fff" stroke="#93C5FD"/>')
        b.append(f'<text x="20" y="{y + 8.6}" font-size="6.8" fill="#1E3A8A">thread {i + 1} · {n}</text>')
    for k, (x, cls) in enumerate([(226, "OrderKeyIT · OrderSearchIT"), (384, "OrderTableIT")]):
        b.append(f'<rect x="{x}" y="16" width="150" height="104" rx="7" fill="#FFFBEB" stroke="#92400E"/>')
        b.append(f'<text x="{x + 10}" y="31" font-size="8.4" font-weight="700" fill="#92400E">Failsafe · fork {k + 1}</text>')
        b.append(f'<text x="{x + 10}" y="43" font-size="7" fill="#334155">its own JVM, -Dfork={k + 1}</text>')
        b.append(f'<rect x="{x + 10}" y="52" width="130" height="28" rx="4" fill="#fff" stroke="#B45309"/>')
        b.append(f'<text x="{x + 75}" y="64" text-anchor="middle" font-size="7.2" font-weight="700" fill="#78350F">singleton Postgres</text>')
        b.append(f'<text x="{x + 75}" y="74" text-anchor="middle" font-size="6.6" fill="#78350F">started once per JVM</text>')
        b.append(f'<line x1="{x + 75}" y1="98" x2="{x + 75}" y2="82" stroke="#475569" marker-end="url(#pp)"/>')
        b.append(f'<text x="{x + 75}" y="110" text-anchor="middle" font-size="6.8" fill="#334155">{cls}</text>')
    b.append('<text x="4" y="9" font-size="7" fill="#5B6474">mvn verify  →  test phase</text>')
    b.append('<text x="226" y="9" font-size="7" fill="#5B6474">→  integration-test phase (forkCount=2: both forks at once)</text>')
    return svg("".join(b), 540, 124, "Unit tests run in Surefire as several threads inside one JVM. Integration tests run in Failsafe as two separate JVMs at the same time; each JVM starts its own singleton Postgres container once and every integration test class in that JVM uses it.")


CMP = [
    ("Run side by side as", "threads in one JVM", "separate JVM processes (forks)"),
    ("What tests share", "nothing — objects live in memory", "containers, ports, database rows, Spring context, files"),
    ("Configure with", "JUnit <code>junit.jupiter.execution.parallel.*</code>", "Failsafe <code>forkCount</code>; Gradle <code>maxParallelForks</code>"),
    ("Isolation comes from", "no shared mutable state; <code>@ResourceLock</code> for the rest", "each fork has its own JVM, singletons and data"),
    ("Cost of one more", "a thread — almost free", "a JVM start and its own containers"),
    ("Usual setting", "on, for every build", "a few forks — measure, don’t guess (p.@@singleton@@)"),
]
SUREFIRE = cut(POM, "      <!-- UNIT tests", "      </plugin>")
SUREFIRE = re.sub(r"\n\s*<argLine>.*?</argLine>", "", SUREFIRE, flags=re.S)
FAILSAFE = cut(POM, "      <!-- INTEGRATION tests", "        </configuration>")
POMPAR = undent(SUREFIRE + "\n\n" + FAILSAFE + "\n        ...\n      </plugin>", 6)
GPAR = cut(GRADLE, "// INTEGRATION tests", "tasks.check { dependsOn(integrationTest) }")
fork_dbg = log("fork-number-debug.txt")

page("parallel", f'''
{sub(CHAP, "Parallel tests: threads for unit, JVMs for integration", C)}
<p class="lede-s">Unit tests share nothing, so they run as <b>threads in one JVM</b>. Integration tests share heavy, stateful resources — a database, a container, a port — so they run in <b>several JVMs</b>, each with its own copy of those resources.</p>
{par_diagram()}
{table(["", "Unit tests", "Integration tests"], CMP, "xs")}
<div class="two top" style="grid-template-columns:1.38fr 1fr;gap:3mm;margin-top:2.4mm">
  {code(POMPAR, "pom.xml — Surefire threads, Failsafe forks", kind="xml", cls="xs")}
  {code(GPAR, "build.gradle.kts — Gradle forks", kind="plain", cls="xs wrap")}
</div>
<div class="two top" style="gap:3mm;margin-top:2mm">
  {ticks(["<b>forkCount=2</b> runs up to two test JVMs at once; <code>2C</code> means two per CPU core. <b>reuseForks=true</b> (the default) keeps each JVM for many classes, so its singletons start once.",
          "<code>${surefire.forkNumber}</code> becomes 1…<i>forkCount</i>. <b>Our run:</b> a system property that was <em>only</em> the placeholder arrived empty, while <code>shop_${surefire.forkNumber}</code> and <code>argLine</code> worked. Print it once.",
          "Surefire’s own <code>parallel</code> parameter is for JUnit 4 and TestNG; for JUnit Jupiter pass JUnit’s settings, as above."], C)}
  {ticks(["Gradle: <code>maxParallelForks</code> (default 1). Each worker gets a unique <code>org.gradle.test.worker</code> property — unique, but <em>not</em> 1…N: our runs got workers 2 and 3.",
          "<code>reuseForks=false</code> (Maven) or <code>forkEvery</code> (Gradle) recycles JVMs — for leaky tests only; singletons restart too.",
          "Maven’s <code>-T</code> (parallel modules) multiplies the forks: 3 modules × <code>forkCount=2</code> can mean 6 JVMs and 6 containers."], C)}
</div>
''', chapter=CHAP, color=C)

# ============================================================================
# singleton containers
# ============================================================================
mv = log("maven/maven-verify.log")
it_part = mv.split("failsafe:3.6.0:integration-test")[1].split("failsafe:3.6.0:verify")[0]
lines = []
for l in it_part.split("\n"):
    if l.startswith("[fork") and ("Postgres" in l or "jdbc:" in l):
        lines.append(re.sub(r" uses jdbc:postgresql://localhost:(\d+)/test\?loggerLevel=OFF", r" uses port \1", l))
    elif re.search(r"Tests run: \d+.*-- in shop\.Order(Key|Table|Search)IT$", l):
        m = re.search(r"Time elapsed: ([\d.]+) s -- in shop\.(\w+)", l)
        lines.append(f"  ✔ {m.group(2)} — {m.group(1)} s")
MAVEN_OUT = "\n".join(lines)
key_t = {m.group(2): float(m.group(1)) for m in re.finditer(r"Time elapsed: ([\d.]+) s -- in shop\.(\w+IT)", it_part)}
containers = len(re.findall(r"\] Postgres ", it_part))

timing = log("maven/maven-timing.log") if (LOGS / "maven/maven-timing.log").exists() else ""
runs = re.findall(r"### it\.forks=(\d)\n.*?wall: (\d+) ms", timing, re.S)
w1 = sorted(int(w) for f, w in runs if f == "1"); w2 = sorted(int(w) for f, w in runs if f == "2")

SINGLE = jfile("src/it/java/shop/SharedPostgres.java", "abstract class SharedPostgres", "  static Connection connect() throws SQLException {\n    return DriverManager.getConnection(\n        DB.getJdbcUrl(), DB.getUsername(), DB.getPassword());\n  }")
SINGLE = re.sub(r"\n  static \{.*?\n  \}", "\n  static {\n    DB.start();                 // once per JVM, never stop() here\n    // … create the schema, log the container id\n  }", SINGLE, flags=re.S)
SINGLE += "\n  // log(), uniqueId(), insert() …\n}"
USE = jfile("src/it/java/shop/OrderKeyIT.java", "class OrderKeyIT", "\n}")

STRAT = [
    ("Singleton per JVM", "one container per fork, shared by its classes", "isolation for free; N forks = N containers", "<b class='yes'>Default choice</b>"),
    ("One shared database", "one DB; schema <code>shop_${surefire.forkNumber}</code> per fork", "fewer containers; isolate the data yourself", "large suites, heavy images"),
    ("<code>@Container</code> per class", "a new container for every test class", "simplest, slowest", "a few classes only"),
    ("Reusable containers", "<code>withReuse(true)</code> + <code>testcontainers.reuse.enable=true</code>", "survives across runs; experimental", "<b class='part'>local only</b>, not CI"),
]
timing_tick = (f"<b>Measure it.</b> Same build, warm Docker, two runs each on a {CPUS}-CPU runner: one IT JVM <b>{w1[0]/1000:.1f}–{w1[-1]/1000:.1f} s</b>, two JVMs <b>{w2[0]/1000:.1f}–{w2[-1]/1000:.1f} s</b> for the whole <code>mvn verify</code>. "
               + ("Two forks were slower here: two containers start at once on a small machine and our tests are short. Forks pay off when IT classes run for minutes." if w2[0] > w1[-1] else
                  "Forks paid off here." if w2[-1] < w1[0] else "No clear winner at this size — forks pay off when IT classes run for minutes.")) if runs else ""

page("singleton", f'''
{sub(CHAP, "Singleton containers: one per test JVM", C)}
<p class="lede-s">Testcontainers’ documented pattern for sharing a container is the <b>singleton container</b>: a <code>static</code> field in a base class, started in a static initialiser. It starts once when the first subclass loads, every IT class in that JVM reuses it, and the <b>Ryuk</b> container removes it when the JVM exits. With forks: <b>one container per fork</b>.</p>
<div class="two top" style="grid-template-columns:1.1fr 1fr;gap:3mm">
  {code(SINGLE, "src/it/java/shop/SharedPostgres.java (Testcontainers 2.0.5)", cls="xs")}
  <div>
    {code(USE, "an IT class just extends it", cls="xs")}
    {note("Don’t annotate the singleton with <code>@Container</code> and don’t call <code>stop()</code>: the JUnit extension stops a <code>static @Container</code> after the last test of its class, so the next class would find it gone.", "warn")}
  </div>
</div>
<h2>Real run: Failsafe, <code>forkCount=2</code>, Docker on GitHub Actions</h2>
<div class="two top" style="grid-template-columns:1.2fr 1fr;gap:3mm">
  {code(MAVEN_OUT, f"{MVN} · Failsafe 3.6.0 · {containers} containers for 4 database IT classes", kind="plain", cls="xs out wrap", right="10 tests ✔")}
  {ticks([f"<b>One container per JVM.</b> Fork 1 started a container for <code>OrderKeyIT</code> ({key_t.get('OrderKeyIT', 0):.1f} s, mostly start-up); <code>OrderSearchIT</code> reused it and took {key_t.get('OrderSearchIT', 0):.2f} s. Fork 2 started its own for <code>OrderTableIT</code>.",
          timing_tick,
          "<b>Spring:</b> the context cache is per JVM too, so each fork builds its own context; wire the container in with <code>@DynamicPropertySource</code>.",
          "Gradle with <code>maxParallelForks = 2</code>: the same, one container per worker."], C)}
</div>
<h2>Four ways to share a database</h2>
{table(["Strategy", "How", "Trade-off", "Use for"], STRAT, "xs")}
''', chapter=CHAP, color=C)
