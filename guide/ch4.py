from lib import *

C = CH["4"]

# ============================================================================
# CH4 · integ
# ============================================================================
def it_diagram():
    b = [ARROW.format(id="ia", c="#475569")]
    boxes = [(10, "OrderApiTest", "JUnit test", LV["unit"]), (150, "HttpClient", "java.net.http", "#334155"),
             (290, "OrderApi", "JDK HttpServer · port 0", LV["integration"]), (430, "InMemory repo", "a fake", DB["fake"])]
    for x, t, s_, c in boxes:
        b.append(f'<rect x="{x}" y="12" width="110" height="36" rx="6" fill="{c}" fill-opacity=".07" stroke="{c}"/>')
        b.append(f'<text x="{x + 55}" y="28" text-anchor="middle" font-size="9" font-weight="700" fill="{c}">{t}</text>')
        b.append(f'<text x="{x + 55}" y="40" text-anchor="middle" font-size="7" fill="#334155">{s_}</text>')
    for x in (120, 260, 400):
        b.append(f'<line x1="{x}" y1="30" x2="{x + 28}" y2="30" stroke="#475569" stroke-width="1.2" marker-end="url(#ia)"/>')
    return svg("".join(b), 550, 54, "Integration test setup: the JUnit test uses Java's HttpClient to call the OrderApi running on the JDK HttpServer on a free port, which reads from an in-memory fake repository.")

page("integ", f'''
{head("04", "Chapter four", "Integration &amp; API testing", "Unit tests prove each class works alone; integration tests prove they work <em>together</em> — with real HTTP, serialisation, SQL and configuration. They are slower, so keep them focused.", C)}
<h2>Testing a real HTTP API</h2>
{it_diagram()}
<div class="two top" style="grid-template-columns:1.45fr 1fr;gap:3.5mm;margin-top:1.5mm">
  {code(jfile("OrderApiTest.java", end="hasValue(\"GET\");\n  }") + "\n\n  // pathTricksAreJustNotFound() → p.@@sec@@\n}", "OrderApiTest.java", cls="xs")}
  <div>
    {code(suite_tree("OrderApiTest"), "real output", kind="out", cls="xs", right="4 / 4 passed")}
    {ticks(["<b>Port 0</b> lets the OS pick a free port, so tests never clash with each other or with a running app.",
            "<b>@BeforeAll / @AfterAll</b> start the server once per class — starting it per test would be slow.",
            "Check the <b>status, headers and body</b>: a 200 with the wrong <code>Content-Type</code> is still a bug.",
            "Test the <b>unhappy paths</b> too: 404 for a missing order, 405 plus an <code>Allow</code> header for a wrong method.",
            "JDK <code>HttpServer</code> + <code>HttpClient</code> keep it dependency-free; Spring Boot’s <code>RANDOM_PORT</code> gives the same shape."], C)}
  </div>
</div>
<h2>Narrow or broad?</h2>
<div class="vs-grid">
  <div class="vs"><div class="vs-pair">
    <div class="vs-side"><b>Narrow integration test</b><p>Exercises <em>one</em> boundary — repository vs real database, client vs stubbed HTTP server.</p></div>
    <div class="vs-mid">vs</div>
    <div class="vs-side"><b>Broad integration test</b><p>Starts most of the application and checks a whole flow through several boundaries.</p></div>
  </div><div class="vs-rule">Prefer many narrow tests: their failures point straight at the broken boundary.</div></div>
  <div class="vs"><div class="vs-pair">
    <div class="vs-side"><b>In-memory stand-in</b><p>H2 for PostgreSQL, a map for Redis. Fast, but dialects and locking differ.</p></div>
    <div class="vs-mid">vs</div>
    <div class="vs-side"><b>The real thing in a container</b><p>Testcontainers runs production’s PostgreSQL version in Docker.</p></div>
  </div><div class="vs-rule">Fakes for <em>unit</em> tests; the real engine when the database is what you’re testing.</div></div>
</div>
''', chapter="04 · Integration &amp; API testing", color=C, bm="04 · Integration &amp; API testing")

# ============================================================================
# CH4 · spring
# ============================================================================
SLICES = [("@WebMvcTest", "Controllers, filters, JSON, validation; no services or DB", "spring-boot-webmvc-test"),
          ("@WebFluxTest", "The same for reactive WebFlux controllers", "spring-boot-webflux-test"),
          ("@DataJpaTest", "JPA repositories, entities, transactions (rolled back)", "spring-boot-data-jpa-test"),
          ("@JdbcTest", "<code>JdbcTemplate</code> / <code>JdbcClient</code> code", "spring-boot-jdbc-test"),
          ("@JsonTest", "Jackson / Gson (de)serialisation only", "spring-boot-test-autoconfigure"),
          ("@RestClientTest", "Your HTTP clients against a mock server", "spring-boot-restclient-test"),
          ("@SpringBootTest", "The whole application context — the broad test", "spring-boot-test")]
sl = "".join(f'<tr><td class="hn" style="color:{C}">{a}</td><td>{b}</td><td class="hn" style="font-weight:500">{c}</td></tr>' for a, b, c in SLICES)

SPLOG = (JAVA / "ci-logs" / "spring" / "spring-verify.log").read_text(errors="replace")
SPDEPS = (JAVA / "ci-logs" / "spring" / "spring-deps.txt").read_text(errors="replace")
def _v(art):
    return re.search(art + r":jar:([^:]+):", SPDEPS).group(1)
SPV = {k: _v(a) for k, a in [("boot", "org.springframework.boot:spring-boot"), ("spring", "org.springframework:spring-test"),
       ("junit", "org.junit.jupiter:junit-jupiter"), ("mockito", "org.mockito:mockito-core"), ("hibernate", "org.hibernate.orm:hibernate-core"),
       ("tc", "org.testcontainers:testcontainers-postgresql")]}
SPRUNS = re.findall(r"Tests run: (\d+), Failures: 0, Errors: 0, Skipped: 0, Time elapsed: ([\d.]+) s -- in shop\.(\w+)", SPLOG)
WEBMVC = jfile("spring/src/test/java/shop/OrderControllerTest.java", "@WebMvcTest", "\n}")
TC = jfile("spring/src/test/java/shop/TestcontainersConfiguration.java", "@TestConfiguration", "\n}")
TCUSE = jfile("spring/src/test/java/shop/OrderFlowIT.java", "@SpringBootTest", "  @Autowired OrderRepository repository;") + "\n  // … tests: p.@@txtrap@@\n}"
SPOUT = "\n".join(f"✔ {c:<20} {n} tests  {t} s" for n, t, c in SPRUNS)

page("spring", f'''
{sub("04 · Integration &amp; API testing", "Spring Boot, Testcontainers &amp; contracts", C)}
<p class="lede-s">In a Spring Boot application, a <b>test slice</b> starts only the part of the context one layer needs, so it is far faster than <code>@SpringBootTest</code>. Spring Boot 4.0 (November 2025) moved each slice into its own test module.</p>
<table class="tbl xs"><thead><tr><th>Annotation</th><th>Loads</th><th>Boot 4 module</th></tr></thead><tbody>{sl}</tbody></table>
<div class="two top" style="margin-top:2.6mm;gap:3mm;grid-template-columns:1fr 1fr">
  {code(WEBMVC, "OrderControllerTest — controller slice", cls="xs")}
  <div>
    {code(TC, "TestcontainersConfiguration — PostgreSQL as a bean", cls="xs")}
    <div style="height:1.6mm"></div>
    {code(SPOUT, f"real run · Spring Boot {SPV['boot']} on GitHub Actions", kind="plain", cls="xs out")}
  </div>
</div>
<p class="small muted" style="margin-top:1.2mm">Versions managed by Boot {SPV['boot']}: Spring Framework {SPV['spring']}, JUnit {SPV['junit']}, Mockito {SPV['mockito']}, Hibernate {SPV['hibernate']}, Testcontainers {SPV['tc']}. Project: <code>spring/</code> in the example code. Our first version used <code>static @Container</code> fields per class; that run’s test JVM took 30 s to exit and Failsafe had to kill it. With the container as a Spring bean it closes with the context, and the JVM exited at once.</p>
<div class="three top" style="margin-top:1.6mm">
  <div class="card"><b class="h">@MockitoBean, not @MockBean</b>Spring Framework 6.2 added <code>@MockitoBean</code> and <code>@MockitoSpyBean</code>. Boot 3.4 deprecated <code>@MockBean</code>/<code>@SpyBean</code>, and Boot 4.0 removed them.</div>
  <div class="card"><b class="h">@ServiceConnection</b>Since Boot 3.1: Boot sees the container’s type and wires the connection details for you — no <code>spring.datasource.url</code> juggling.</div>
  <div class="card"><b class="h">Testcontainers 2.0</b>October 2025. Module artifacts gained a prefix: <code>testcontainers-postgresql</code>, <code>testcontainers-junit-jupiter</code>.</div>
</div>
<h2>Calling other services: stubs and contracts</h2>
<div class="two top">
  <div>
    <p class="small"><b>WireMock</b> runs a real HTTP server that returns canned responses, so your client code sends real requests over a socket. Stub the slow, the broken and the odd: timeouts, 500s, malformed JSON, redirects.</p>
    <p class="small"><b>The risk:</b> your stub and the real provider drift apart, and both sides stay green while production breaks.</p>
  </div>
  <div>
    <p class="small"><b>Consumer-driven contract tests</b> (Ian Robinson, 2006) close that gap. The consumer records what it needs from the API; the provider’s build replays those expectations against the real service. Tools: <b>Pact</b> (many languages, a broker to share contracts) and <b>Spring Cloud Contract</b> (JVM, contracts generate stubs and provider tests).</p>
  </div>
</div>
''', chapter="04 · Integration &amp; API testing", color=C)

# ============================================================================
# CH4 · tricky
# ============================================================================
FLAKY = [("Real time", "<code>LocalDate.now()</code> breaks at midnight, month end, DST", "Inject a <code>Clock</code>; use <code>Clock.fixed</code>"),
         ("Randomness", "UUIDs, shuffles, random test data", "Seed it, or inject the generator"),
         ("Sleeping", "<code>Thread.sleep(500)</code> is too short on a busy CI box", "Wait for a condition (Awaitility) with a timeout"),
         ("Shared state", "Static fields, a shared DB row, a singleton cache", "Fresh fixtures per test; unique IDs; reset in <code>@AfterEach</code>"),
         ("Test order", "Test B only passes after test A", "Each test sets up its own data; run in random order to find these"),
         ("Time zone / locale", "Passes in Bengaluru, fails on a UTC build agent", "Set zone and locale explicitly in code and tests"),
         ("Network", "Calls to real external services", "Stub at the boundary; containers for owned dependencies"),
         ("Concurrency", "Races appear one run in a hundred", "Latches to line threads up; repeat; stress in a separate job")]
fl = "".join(f'<tr><td class="nm">{a}<div class="small muted" style="font-weight:400;font-size:6.6pt">{b}</div></td><td>{c}</td></tr>' for a, b, c in FLAKY)

page("tricky", f'''
{sub("04 · Integration &amp; API testing", "Time, randomness, threads &amp; flaky tests", C)}
<p class="lede-s">A test that passes and fails without any code change is <b>flaky</b>. Flaky tests are worse than none: people learn to press “re-run”, and real failures get ignored. Almost every cause is something the test doesn’t control.</p>
<div class="two top" style="grid-template-columns:1.45fr 1fr;gap:3.5mm">
  {code(jfile("TrickyThingsTest.java"), "TrickyThingsTest.java", cls="xs")}
  <div>
    {code(suite_tree("TrickyThingsTest"), "real output", kind="out", cls="xs", right="5 / 5 passed")}
    <h2 style="margin-top:2.4mm">Where flakiness comes from</h2>
    <table class="tbl xs"><thead><tr><th>Cause</th><th>Fix</th></tr></thead><tbody>{fl}</tbody></table>
  </div>
</div>
<div class="two" style="margin-top:2mm">
  {ticks(["<b>Clock.fixed</b> makes “now” a constant; production passes <code>Clock.systemUTC()</code>.",
          "<b>new Random(42)</b> gives the same sequence on every run and every machine.",
          "<b>@TempDir</b> — no leftovers between runs, no clashes between parallel tests."], C)}
  {ticks(["<b>CountDownLatch</b> releases 16 threads together so they really overlap: 8,000 concurrent saves, none lost.",
          "<b>assertTimeoutPreemptively</b> stops a hung test instead of hanging the whole build.",
          "For async code, poll for a condition with <b>Awaitility</b> (<code>await().atMost(5, SECONDS).until(…)</code>) instead of sleeping."], C)}
</div>
{note("Treat a flaky test like a bug. Quarantine it (a separate, non-blocking job), open a ticket, and fix or delete it within days — never add an automatic “retry until green” to the main build.", "rule")}
''', chapter="04 · Integration &amp; API testing", color=C)
