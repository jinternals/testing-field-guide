from lib import *
import lib

# ============================================================================
# CHEAT SHEET
# ============================================================================
def hl(pairs):
    return "".join(f'<div><code>{a}</code><span>{b}</span></div>' for a, b in pairs)

ann = hl([("@Test", "a test"), ("@ParameterizedTest", "one run per argument set"), ("@BeforeEach / @AfterEach", "around every test"),
          ("@BeforeAll / @AfterAll", "once per class (static)"), ("@Nested", "group related tests"), ("@Tag(\"slow\")", "filter what runs"),
          ("@Disabled(\"why\")", "skip, with a reason"), ("@TempDir", "fresh temp folder"), ("@ExtendWith", "plug in extensions")])
asr = hl([("assertEquals(exp, act)", "expected first"), ("assertThrows(X.class, …)", "returns the exception"), ("assertAll(…)", "report every failure"),
          ("assertThat(x).isEqualTo(y)", "AssertJ"), (".containsExactly(…)", "order matters"), (".extracting(Order::total)", "map, then check"),
          ("assertThatThrownBy(…)", "then .hasMessage(…)")])
mok = hl([("when(m.f()).thenReturn(v)", "stub"), ("doReturn(v).when(spy).f()", "stub a spy"), ("doThrow(e).when(m).voidF()", "stub a void"),
          ("verify(m).f(eq(1), any())", "all matchers or none"), ("verify(m, never()).f()", "not called"), ("verifyNoInteractions(m)", "untouched"),
          ("@Captor ArgumentCaptor&lt;T&gt;", "grab the argument"), ("mockStatic(X.class)", "try-with-resources")])

page("cheat", f'''
<div class="cheat">
  <div class="cheat-top">
    <div><div class="kicker light">Pin this page</div><h1 class="cheat-h">Cheat sheet</h1></div>
    <div class="cheat-sub">Testing Java at a glance</div>
  </div>
  <div class="cheat-grid three">
    <div class="cbox"><div class="cbox-h">JUnit 6 annotations</div><div class="hd-list">{ann}</div></div>
    <div class="cbox"><div class="cbox-h">Assertions</div><div class="hd-list">{asr}</div></div>
    <div class="cbox"><div class="cbox-h">Mockito</div><div class="hd-list">{mok}</div></div>
  </div>
  <div class="cheat-grid three">
    <div class="cbox"><div class="cbox-h">Test doubles</div>
      <ul class="cl"><li><b>Dummy</b> — fills a parameter, never used</li><li><b>Stub</b> — canned answers</li><li><b>Spy</b> — stub that records calls</li><li><b>Mock</b> — expectations, verified</li><li><b>Fake</b> — working shortcut (in-memory repo)</li></ul></div>
    <div class="cbox"><div class="cbox-h">Which level?</div>
      <ul class="cl"><li><b>Unit</b> — rules, calculations, orchestration</li><li><b>Integration</b> — SQL, HTTP, JSON, config</li><li><b>Contract</b> — agreements between services</li><li><b>End-to-end</b> — a few money-making journeys</li><li>Push each check to the <b>cheapest level</b> that catches it</li></ul></div>
    <div class="cbox"><div class="cbox-h">Flaky? Control the input</div>
      <ul class="cl"><li>Time → inject <code>Clock</code></li><li>Random → seed it</li><li>Sleep → wait for a condition</li><li>Shared state → fresh fixtures, unique IDs</li><li>Network → stub or container</li></ul></div>
  </div>
  <div class="cheat-grid">
    <div class="cbox"><div class="cbox-h">Commands</div><div class="hd-list">{hl([
        ("mvn test", "unit tests (Surefire)"), ("mvn verify", "+ integration tests (Failsafe)"), ("mvn test -Dtest=MoneyTest", "one class"),
        ("mvn test -Dtest='MoneyTest#rejects*'", "matching methods"), ("mvn test -Dgroups=fast", "only @Tag(\"fast\")"),
        ("./gradlew test --tests '*MoneyTest'", "Gradle filter"), ("mvn test-compile pitest:mutationCoverage", "mutation testing (PIT)"), ("target/site/jacoco/index.html", "JaCoCo report after mvn verify")])}</div></div>
    <div class="cbox"><div class="cbox-h">Golden rules</div>
      <ul class="cl"><li>Watch every new test <b>fail first</b></li><li>One behaviour per test, named as a sentence</li><li>Arrange · Act · Assert — and nothing else</li><li>Test behaviour through the <b>public API</b></li><li>Don’t mock values or what you don’t own</li><li>Boundaries: test on and either side of every edge</li><li>Coverage finds gaps; <b>PIT</b> measures strength — merge unit + IT coverage</li><li>A flaky test is a bug — quarantine and fix it</li></ul></div>
  </div>
  <div class="cheat-grid three">
    <div class="cbox"><div class="cbox-h">Versions used here</div><ul class="cl"><li>JUnit <b>6.1.3</b> · Java 17+</li><li>Mockito <b>5.24.0</b> · AssertJ <b>3.27.7</b></li><li>Run on OpenJDK <b>21</b></li></ul></div>
    <div class="cbox"><div class="cbox-h">Performance</div><ul class="cl"><li>Report <b>p50 / p95 / p99</b>, not the mean</li><li>Warm up the JVM before measuring</li><li>Little’s Law: users = rate × time</li></ul></div>
    <div class="cbox"><div class="cbox-h">Security in CI</div><ul class="cl"><li><b>SAST</b> + <b>SCA</b> + secrets on every build</li><li><b>DAST</b> (ZAP) nightly on staging</li><li>Write access-control tests yourself</li></ul></div>
  </div>
</div>''', chapter="Cheat sheet", color="#0F172A", cls="p-cheat", bm="Cheat sheet")

# ============================================================================
# CHECKLIST + REFERENCES + VERIFICATION
# ============================================================================
checks = [("Unit tests", ["Business rules tested at every boundary", "Each test checks one behaviour, named as a sentence", "No real clock, randomness, network or files"]),
          ("Doubles", ["Mocks only at the edges (ports you own)", "No mocked value objects", "No unused stubs (strict stubs on)"]),
          ("Integration", ["Real database engine in a container", "HTTP status, headers and body checked", "Unhappy paths: 4xx, 5xx, timeouts"]),
          ("Suite health", ["Runs in random order and in parallel", "No flaky tests in the main build", "Main build under ~10 minutes"]),
          ("Strength", ["Coverage reviewed for untested code", "Mutation testing on critical modules", "Every bug fix starts with a failing test"]),
          ("Beyond", ["A few end-to-end journeys + prod smoke", "Load test with percentile targets", "SAST, SCA, DAST and access-control tests"])]
ck = "".join(f'<div class="ck"><div class="ck-h">{t}</div>' + "".join(f'<div class="ck-i"><span class="box" aria-hidden="true"></span>{i}</div>' for i in items) + '</div>' for t, items in checks)
refs = [("Beck 2002", "Test-Driven Development: By Example"), ("Meszaros 2007", "xUnit Test Patterns — the test double names"),
        ("Fowler 2007", "Mocks Aren’t Stubs — martinfowler.com"), ("Cohn 2009", "Succeeding with Agile — the test pyramid"),
        ("Dodds 2018", "The Testing Trophy — kentcdodds.com"), ("Robinson 2006", "Consumer-Driven Contracts — martinfowler.com"),
        ("DeMillo et al. 1978", "Hints on Test Data Selection — mutation testing"), ("Winters et al. 2020", "Software Engineering at Google, ch. 11–14"),
        ("docs.junit.org", "JUnit 6 user guide &amp; release notes"), ("site.mockito.org", "Mockito javadoc (incl. agent setup)"),
        ("assertj.github.io", "AssertJ core documentation"), ("docs.spring.io", "Spring Boot 4 testing reference"),
        ("java.testcontainers.org", "Testcontainers for Java"), ("pitest.org · jacoco.org", "Mutation and coverage tools")]
rf = "".join(f'<div class="rf"><b>{a}</b><span>{b}</span></div>' for a, b in refs)

import json
def verify_table():
    f = lib.ROOT / "verify.json"
    rows = json.loads(f.read_text()) if f.exists() else [["(pending)", "", ""]]
    return table(["Criterion", "How it was checked", "Result"], rows, "xs")

page("check", f'''
{sub("Before you ship", "Testing checklist", "#0F172A")}
<div class="cks">{ck}</div>
<h2>References &amp; further reading</h2>
<div class="refs">{rf}</div>
<h2>How this guide was verified</h2>
{verify_table()}
''', chapter="Checklist, references &amp; verification", color="#0F172A", bm="Checklist, references &amp; verification")

# ============================================================================
# INDEX
# ============================================================================
IDX = {
 "AAA (Arrange · Act · Assert)": ["pyramid"], "Acceptance test": ["why"], "Access control tests": ["sec"], "ArgumentCaptor": ["mockito", "mockito2"],
 "assertAll": ["assert"], "AssertJ": ["assert", "params"], "assertThrows": ["assert"], "assertTimeoutPreemptively": ["tricky"], "Assumptions": ["params"],
 "Awaitility": ["tricky", "messaging", "scheduled"], "BDD / Gherkin": ["tdd"], "BDDMockito": ["mockito2"], "Boundary value analysis": ["design", "cov"], "Branch coverage": ["cov"],
 "Chaos engineering": ["sec"], "Classicist vs mockist": ["mockito"], "Clock (java.time)": ["tricky", "mockito", "scheduled"], "Code coverage": ["cov"],
 "Consumer-driven contracts": ["contract"], "Contract testing": ["contract", "interview"], "Coordinated omission": ["perf"], "CountDownLatch": ["tricky"],
 "@CsvSource": ["design", "params"], "Cucumber": ["tdd"], "Cypress": ["e2e"], "DAST": ["sec"], "@DataJpaTest": ["spring", "txtrap"], "Decision table": ["design"],
 "Dependency-Check (OWASP)": ["sec", "plugins"], "@DisplayName": ["junit"], "doReturn": ["mockpit", "mockito2"], "Dummy": ["doubles"], "End-to-end tests": ["e2e"],
 "Equivalence partitioning": ["design"], "@ExtendWith": ["junit", "params"], "Fake": ["doubles", "integ"], "Failsafe (Maven)": ["ci", "parallel"], "Failure messages": ["assert", "mockpit"],
 "FastCSV": ["setup"], "@FieldSource": ["params"], "FIRST principles": ["pyramid"], "Flaky tests": ["tricky", "ci", "cacheasync"], "Fuzzing (Jazzer)": ["sec"],
 "Gatling": ["perf"], "Given / When / Then": ["pyramid", "mockito2", "tdd"], "Gradle": ["setup", "ci"], "@InjectMocks": ["interview"], "InOrder": ["mockito2"],
 "Integration tests": ["integ"], "JaCoCo": ["cov"], "JMeter": ["perf"], "JMH": ["perf"], "JSpecify": ["setup"], "JUnit 4 migration": ["setup"],
 "JUnit 6 changes": ["setup", "params"], "JUnit Platform": ["setup"], "k6": ["perf"], "Lifecycle": ["junit"], "Little’s Law": ["perf"],
 "Load testing": ["perf"], "Locators": ["e2e"], "Maven setup": ["setup"], "@MethodSource": ["params"], "Mock": ["doubles", "mockito"],
 "Mockito": ["mockito", "mockito2", "mockpit"], "Mockito as -javaagent": ["mockpit"], "@MockitoBean": ["spring"], "MockitoExtension": ["mockito"],
 "MockMvcTester": ["spring"], "mockStatic": ["mockpit"], "Mutation testing (PIT)": ["cov"], "Nagle’s algorithm": ["perf"], "Naming tests": ["pyramid"],
 "@Nested": ["params"], "Pact": ["spring", "contract"], "Page Object": ["e2e"], "Parallel execution": ["ci", "parallel"], "@ParameterizedTest": ["design", "params"],
 "Percentiles (p95, p99)": ["perf"], "Playwright": ["e2e"], "Property-based testing": ["design"], "quoteTextArguments": ["params", "setup"],
 "REST Assured": ["e2e"], "SAST": ["sec"], "SCA": ["sec"], "Selenium": ["e2e"], "@ServiceConnection": ["spring"], "Smoke test": ["why", "e2e"],
 "Spring Boot test slices": ["spring", "ci"], "Spy": ["doubles", "mockpit"], "State vs behaviour verification": ["doubles"], "Strict stubs": ["mockpit"],
 "Stub": ["doubles"], "Surefire (Maven)": ["ci", "setup"], "@Tag": ["params"], "TDD": ["tdd"], "@TempDir": ["tricky"], "Test data builders": ["conventions"],
 "Test doubles": ["doubles"], "Test pyramid": ["pyramid"], "Test sizes (Google)": ["why"], "Test smells": ["cov"], "Testcontainers": ["spring", "integ", "singleton"],
 "@TestInstance": ["junit"], "@TestMethodOrder": ["junit"], "Testing trophy": ["pyramid"], "thenAnswer": ["mockito"], "Timeouts": ["params", "tricky", "sec"],
 "Toxiproxy": ["sec"], "verify": ["mockito", "mockito2"], "@WebMvcTest": ["spring", "ci"], "WireMock": ["spring", "wiremock"], "ZAP": ["sec"],
}

IDX.update({
 "Mutation score": ["cov", "pit"], "Surviving mutant": ["pit", "pitci"], "Equivalent mutant": ["pit"], "TIMED_OUT (PIT)": ["pit", "pitci"],
 "fullMutationMatrix": ["dupes"], "withHistory (PIT)": ["pitci"], "mutationThreshold": ["pitci"],
 "Mutator groups (DEFAULTS, STRONGER)": ["cov", "pit", "pitci"], "pitest-junit5-plugin": ["pit", "pitci"], "pitest-maven": ["pitci", "cov"],
 "JaCoCo merge / report": ["itcov"], "prepare-agent-integration": ["itcov"], "report-aggregate": ["itcov"], "JaCoCo check (gate)": ["itcov"],
 "Coverage: unit vs integration": ["itcov"], "Quality gate": ["itcov", "pitci"], "New-code coverage": ["itcov"], "Duplicate tests": ["dupes"],
 "Redundant tests": ["dupes"], "PMD CPD": ["plugins"], "SonarQube": ["itcov", "plugins"], "Kill matrix": ["dupes"], "argLine": ["itcov", "mockpit"], "Resource leak tests": ["pit"], "JUnit extensions": ["extensions"], "ParameterResolver": ["extensions"], "@RepeatedTest": ["extensions"], "Composed annotations": ["extensions"], "Log assertions": ["observe"], "Micrometer": ["observe"], "OutputCaptureExtension": ["observe"], "Legacy code": ["legacy"], "Characterization tests": ["legacy"], "Seams": ["legacy"], "Golden master / approval": ["legacy"], "Kafka": ["messaging"], "ArchUnit": ["archunit"], "Retries (Resilience4j)": ["wiremock"], "Timeouts": ["wiremock"], "Database migrations": ["migrations"], "Risk-based testing": ["whattotest"], "Four pillars of a good test": ["whattotest"], "What not to test": ["whattotest"], "Pact Broker / can-i-deploy": ["contract"], "GreenMail": ["email"], "E-mail tests": ["email"], "Mailpit": ["email"], "Idempotent consumer": ["messaging"], "@EmbeddedKafka": ["messaging"], "LocalStack": ["cloud"], "Moto (AWS)": ["cloud"], "Azurite": ["cloud"], "OAuth2 / JWT tests": ["authmock"], "MockOAuth2Server": ["authmock"], "Keycloak": ["authmock"], "Build cache": ["speed"], "Test sharding": ["speed"], "@Transactional in tests": ["txtrap"], "LazyInitializationException": ["txtrap"], "Team conventions": ["conventions"],  "forkCount / reuseForks": ["parallel"], "maxParallelForks (Gradle)": ["parallel"], "surefire.forkNumber": ["parallel", "singleton"], "Singleton container": ["singleton"], "SpotBugs": ["plugins"],  "HttpServer (JDK)": ["integ", "perf"],
 "HttpClient (JDK)": ["integ"], "Port 0 (free port)": ["integ"], "Hostile input tests": ["sec"], "Little’s Law": ["perf"],
 "TCP_NODELAY": ["perf"], "Virtual threads": ["perf"], "Self-check questions": ["interview"], "Cheat sheet": ["cheat"],
 "BigDecimal money": ["assert"], "Record (Java)": ["junit", "mockpit"], "Lenient stubs": ["mockpit"], "MockitoSettings": ["mockpit"],
 "Flyway / Liquibase": ["migrations"], "Accessibility testing": ["e2e"], "Visual regression": ["e2e"],
 "@Cacheable / @CacheEvict": ["caches"], "Redis": ["caches", "cacheasync"], "Cache TTL": ["caches"], "Self-invocation (proxies)": ["caches"],
 "@Scheduled": ["scheduled"], "Spring Batch": ["batch"], "@SpringBatchTest": ["batch"], "JobOperatorTestUtils": ["batch"], "Skip / filter (Batch)": ["batch"],
 "jcstress": ["jcstress"], "Lost update (race)": ["jcstress"], "Feature flags": ["prod"], "Synthetic checks": ["prod"], "Canary release": ["prod"],
 "ApplicationContextRunner": ["prod"], "immediateWrites (Redis cache)": ["cacheasync"], "Repeating a flaky test": ["cacheasync"], "Testing in production": ["prod"],
})

def idx_html():
    keyf = lambda t: re.sub(r"^[@.]", "", t).lower()
    out, cur = [], None
    for term in sorted(IDX, key=keyf):
        L = keyf(term)[0].upper()
        if L != cur:
            out.append(f'<div class="L">{L}</div>'); cur = L
        pages = ", ".join(f'<a href="#p-{k}">@@{k}@@</a>' for k in IDX[term])
        out.append(f'<div class="e"><span>{term}</span><span class="pgs">{pages}</span></div>')
    return "".join(out)

page("index", f'''
{sub("Find anything", "Index A–Z", "#0F172A")}
<div class="idx" style="--accent:#1D4ED8">{idx_html()}</div>
<h2>Three ways to read this guide</h2>
<div class="three">
  <div class="card"><b class="h">New to testing</b>Foundations {ref("why")}, first test {ref("junit")}, assertions {ref("assert")}, test doubles {ref("doubles")}, Mockito {ref("mockito")}, then the cheat sheet {ref("cheat")}.</div>
  <div class="card"><b class="h">Improving an existing suite</b>Team conventions {ref("conventions")}, flaky tests {ref("tricky")}, mutation testing {ref("pit")}, unit + IT coverage {ref("itcov")}, duplicates {ref("dupes")}, plugins {ref("plugins")}, parallel ITs {ref("parallel")}, CI {ref("ci")}.</div>
  <div class="card"><b class="h">Quick refresher</b>Pyramid {ref("pyramid")}, doubles {ref("doubles")}, Mockito pitfalls {ref("mockpit")}, Spring slices {ref("spring")}, TDD {ref("tdd")}, Q&amp;A {ref("interview")}.</div>
</div>
''', chapter="Index", color="#0F172A", bm="Index")
