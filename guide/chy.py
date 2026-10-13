"""Foundations: what to test. Plus WireMock, Pact contracts, Flyway migrations and ArchUnit — all from CI logs."""
from lib import *

LOGS = JAVA / "ci-logs"
EX = (LOGS / "extras/extras-verify.log").read_text(errors="replace")
SPL = (LOGS / "spring/spring-verify.log").read_text(errors="replace")
RUN = {}
for m in re.finditer(r"Tests run: (\d+), Failures: 0, Errors: 0, Skipped: (\d+), Time elapsed: ([\d.]+) s -- in shop\.(?:[a-z]+\.)?(\w+)", EX + SPL):
    RUN[m.group(4)] = (m.group(1), m.group(3))


def ran(cls):
    n, secs = RUN[cls]
    return f"{n} ✔ · {secs} s"


def jx(path, start=None, end=None, dedent=0):
    return jfile(path, start, end, dedent=dedent)


# ============================================================================
# CH1 · what to test — and what to leave out
# ============================================================================
C1 = CH["1"]
PILLARS = [("Catches regressions", "Fails when behaviour breaks. More real code exercised, more bugs caught."),
           ("Survives refactoring", "Stays green when behaviour <em>doesn’t</em> change. Tests tied to internals fail for nothing — and get ignored."),
           ("Fast feedback", "Runs in milliseconds, so it runs on every change."),
           ("Cheap to keep", "Easy to read, small setup, one reason to fail.")]
RISK = [("Money, permissions, personal data", "high", "unit tests for every rule and boundary, mutation testing, an integration test per path, a contract per consumer"),
        ("Core business rules", "high", "unit tests with boundaries and decision tables; PIT on the module"),
        ("Wiring: SQL, HTTP, messaging, config", "medium", "integration tests with the real thing in a container"),
        ("User journeys that earn money", "medium", "a few end-to-end tests: sign-up, checkout, payment"),
        ("Glue code that only delegates", "low", "covered by the integration test above it — no unit test of its own"),
        ("Getters, generated code, the framework itself", "none", "don’t test; it is someone else’s job or has no logic")]
MAP = [("A rule computes the wrong number", "unit test", "design"), ("SQL or mapping is wrong", "integration test", "spring"),
       ("Schema change breaks old data", "migration test", "migrations"), ("Another service is slow or down", "WireMock stub", "wiremock"),
       ("An API change breaks a consumer", "contract test", "contract"), ("A duplicate message is applied twice", "integration test", "messaging"),
       ("The wrong user can see an order", "security + auth tests", "authmock"), ("Layers get tangled over time", "architecture test", "archunit"),
       ("The checkout button stops working", "end-to-end test", "e2e"), ("It is too slow under load", "performance test", "perf")]
risk_rows = "".join(f'<tr><td class="nm">{a}</td><td class="c"><b style="color:{ {"high": "#B91C1C", "medium": "#92400E", "low": "#047857", "none": "#5B6474"}[b] }">{b}</b></td><td>{c}</td></tr>' for a, b, c in RISK)
map_rows = "".join(f'<tr><td>{a}</td><td class="nm">{b}</td><td class="c">{ref(k)}</td></tr>' for a, b, k in MAP)

page("whattotest", f'''
{sub("01 · Foundations", "What to test — and what to leave out", C1)}
<p class="lede-s">Testing everything equally is the most expensive way to get mediocre safety. Spend tests where a bug would hurt most, write each one so it is worth keeping, and pick the cheapest kind of test that can catch the bug you are worried about.</p>
<h2>Four properties of a valuable test</h2>
<div class="four">{"".join(f'<div class="card"><b class="h">{a}</b>{b}</div>' for a, b in PILLARS)}</div>
<p class="small muted" style="margin-top:1.2mm">From Vladimir Khorikov, <i>Unit Testing: Principles, Practices, and Patterns</i> (2020). You can’t max all four: end-to-end tests catch much but are slow; tests of a tiny function are fast but catch little. <b>Survives refactoring</b> is the one never to trade away — so <b>assert on outcomes</b> (return values, saved state, messages sent), not on which private steps produced them.</p>
<div class="two top" style="grid-template-columns:1.25fr 1fr;gap:3mm;margin-top:2mm">
  <div>
    <h2 style="margin-top:0">Test by risk</h2>
    <table class="tbl xs"><thead><tr><th>Code</th><th class="c">Risk</th><th>How much testing</th></tr></thead><tbody>{risk_rows}</tbody></table>
  </div>
  <div>
    <h2 style="margin-top:0">Which test catches which bug</h2>
    <table class="tbl xs"><thead><tr><th>The bug you fear</th><th>Cheapest test</th><th class="c">Page</th></tr></thead><tbody>{map_rows}</tbody></table>
  </div>
</div>
<h2>Assert the outcome, not the steps</h2>
{table(["Behaviour", "Fragile: tied to how it works", "Robust: checks what it does"], [
    ("Order total", "verify <code>discountPolicy.percentFor()</code> was called once", "assert the total is ₹1,140.00"),
    ("Order saved", "verify the exact SQL string sent to the database", "read the order back and check its fields"),
    ("E-mail sent", "verify a private <code>formatBody()</code> helper ran", "assert the received mail’s recipient and subject"),
    ("Payment before saving", "— (here the <em>order</em> of calls is the rule)", "<code>InOrder</code>: charge, then save (p.@@mockito2@@)")], "xs")}
<p class="small muted" style="margin-top:1.2mm">Interaction checks are right when the interaction <em>is</em> the behaviour — a payment charged, an e-mail requested, a message published — and wrong when they pin down internal steps.</p>
{note("Before writing a test, ask: <b>what bug would this catch</b>, and is there a cheaper test that catches it already? If you can’t name the bug, the test is probably testing the framework, the language — or nothing.", "rule")}
''', chapter="01 · Foundations", color=C1)

# ============================================================================
# CH4 · migrations
# ============================================================================
C4 = CH["4"]
MIG = [(f.name, (JAVA / "extras/src/main/resources/db/migration" / f.name).read_text().strip())
       for f in sorted((JAVA / "extras/src/main/resources/db/migration").iterdir())]
BROKEN = (JAVA / "extras/src/test/resources/db/broken/V3__status_required.sql").read_text().strip()
mig_code = "\n\n".join(f"-- {n}\n{t}" for n, t in MIG)

page("migrations", f'''
{sub("04 · Integration &amp; API testing", "Database migrations: test them on real data", C4)}
<p class="lede-s">A migration that works on an empty database can still fail on production’s rows. Run every migration in tests against the <b>same database engine</b>, and for risky ones, against data written by the <b>previous</b> version.</p>
<div class="two top" style="grid-template-columns:1fr 1fr;gap:3mm">
  <div>
    {code(mig_code, "src/main/resources/db/migration — Flyway 13.10", kind="plain", cls="xs")}
    <div style="height:1.6mm"></div>
    {code("-- V3__status_required.sql (first draft)\n" + BROKEN.split(chr(10), 1)[1], "the draft someone wrote first — no backfill", kind="plain", cls="xs")}
  </div>
  {code(jx("extras/src/test/java/shop/migrations/MigrationsIT.java", "  @Test\n  void allMigrations", "\n}"), "MigrationsIT — real PostgreSQL 17", cls="xs", right=ran("MigrationsIT"))}
</div>
<div class="two top" style="gap:3mm;margin-top:2.4mm">
  {ticks(["<b>Empty database:</b> all three migrations apply, and <code>validate()</code> confirms no applied file was edited afterwards.",
          "<b>Yesterday’s data:</b> migrate to V2 with <code>target(&quot;2&quot;)</code>, insert a row as the old app would, then deploy V3. The backfill sets <code>PLACED</code>.",
          "<b>The draft without backfill fails</b> on that row, with PostgreSQL’s own error — in CI, not during the release."], C4)}
  {ticks(["Let Hibernate <b>validate</b> the schema (<code>spring.jpa.hibernate.ddl-auto=validate</code>) instead of creating it, so entity/column mismatches fail at startup.",
          "Never edit an applied migration — add a new one. Flyway’s checksums catch edits.",
          "Same idea with Liquibase: <code>update</code> to a tag, insert data, then <code>update</code> again."], C4)}
</div>
<h2>Changing a live schema without downtime: expand, then contract</h2>
{table(["Change", "Release 1 (expand)", "Release 2", "Release 3 (contract)"], [
    ("Make a column required", "add it nullable; app writes it", "backfill old rows, then <code>SET NOT NULL</code> — our V2 → V3", "—"),
    ("Rename a column", "add the new column; app writes both", "backfill; app reads the new one", "drop the old column"),
    ("Drop a column", "app stops reading and writing it", "drop it", "—"),
    ("Index a big table", "PostgreSQL <code>CREATE INDEX CONCURRENTLY</code>, which can’t run in a transaction: set <code>executeInTransaction=false</code> in the script’s <code>.conf</code> file", "—", "—")], "xs")}
<p class="small muted" style="margin-top:1.2mm">During a rolling deploy the old and the new app run against the same schema, so every step must work with both. Test each step the way <code>MigrationsIT</code> does: migrate to the previous version, write data like the old app, then apply the next step.</p>
''', chapter="04 · Integration &amp; API testing", color=C4)

# ============================================================================
# CH4 · WireMock + Resilience4j
# ============================================================================
page("wiremock", f'''
{sub("04 · Integration &amp; API testing", "Calling other services: WireMock &amp; retries", C4)}
<p class="lede-s">Your code will meet slow, failing and strange responses from the services it calls. <b>WireMock</b> (Apache-2.0) is a real HTTP server you script per test, so you can produce those failures on demand — and prove your timeouts and retries (here <b>Resilience4j</b>) behave.</p>
<div class="two top" style="grid-template-columns:1fr 1fr;gap:3mm">
  <div>
    {code(jx("extras/src/main/java/shop/http/PriceClient.java", "  public BigDecimal priceOf", "\n}"), "PriceClient.java — timeout, error mapping (excerpt)", cls="xs")}
    <div style="height:1.6mm"></div>
    {code(jx("extras/src/main/java/shop/http/Retries.java", "  /** 3 attempts", "  }"), "Retries.java — Resilience4j 2.4.0", cls="xs")}
  </div>
  {code(jx("extras/src/test/java/shop/http/PriceClientTest.java", "/** WireMock", "  @Test\n  void unknownProductIsNotRetried").rsplit("\n  @Test", 1)[0] + "\n  // … unknownProductIsNotRetried, malformedJsonIsAClearError\n}", "PriceClientTest — WireMock 3.13.2", cls="xs", right=ran("PriceClientTest"))}
</div>
<h2>What each stub proves</h2>
{table(["Stub", "Expected behaviour", "Checked with"], [
    ("503, then 500, then 200 (a scenario)", "two retries, then the price", "<code>verify(3, getRequestedFor(…))</code>"),
    ("200 after a 2-second delay", "500 ms timeout, three attempts, then <code>UpstreamException</code>", "<code>withFixedDelay(2_000)</code>, 3 requests"),
    ("404", "<b>no</b> retry — retrying can’t make a missing product appear", "exactly 1 request"),
    ("HTML instead of JSON", "a clear error naming the bad body", "<code>hasMessageStartingWith</code>")], "xs")}
<div class="two top" style="gap:3mm;margin-top:2mm">
  {ticks(["<b>Retry only what can succeed next time:</b> timeouts and 5xx yes; 4xx and bad data no.",
          "<b>Always set a timeout.</b> Java’s <code>HttpClient</code> waits forever by default; one slow service then ties up every thread."], C4)}
  {ticks(["<b>Verify the number of calls,</b> not just the result — a retry loop that silently fires 50 times is a bug too.",
          "Stubs drift from the real service; pair them with a contract test (p.@@contract@@)."], C4)}
</div>
''', chapter="04 · Integration &amp; API testing", color=C4)

# ============================================================================
# CH4 · contract testing with Pact
# ============================================================================
pb = (LOGS / "extras/pact-breaking.log").read_text(errors="replace")
pact_fail = pb[pb.index("Verifying a pact between"):pb.index("Failures:")]
pact_fail = re.sub(r"\d\d:\d\d:\d\d\.\d+ WARN .*?\n(\s+.*\n)+?\s*\n", "", pact_fail)
pact_fail += pb[pb.index("1.1) body:"):pb.index("}", pb.index("1.1) body:")) + 1]
pact_fail = "\n".join(l.rstrip() for l in pact_fail.split("\n") if l.strip())
pact_json = (LOGS / "extras/shop-orders.json").read_text()
pj = re.search(r'"request": \{.*?\n      \},\n      "response": \{\n        "body": \{\n          "content": \{.*?\}', pact_json, re.S).group(0)

page("contract", f'''
{sub("04 · Integration &amp; API testing", "Contract testing with Pact", C4)}
<p class="lede-s">A WireMock stub says what <i>you think</i> the other service returns. A <b>consumer-driven contract</b> makes that belief checkable: the consumer’s test records what it needs, and the provider’s build replays it against the real API. Break the contract and the <b>provider’s</b> build goes red — before anything ships.</p>
<div class="two top" style="grid-template-columns:1fr 1fr;gap:3mm">
  {code(jx("extras/src/test/java/shop/contract/OrderStatusConsumerPactTest.java", "@ExtendWith", "\n}"), "consumer test", cls="xs", right=ran("OrderStatusConsumerPactTest"))}
  {code(jx("extras/src/test/java/shop/contract/OrderStatusProviderPactIT.java", "@Provider", "\n}"), "provider test", cls="xs", right=ran("OrderStatusProviderPactIT"))}
</div>
<div class="two top" style="grid-template-columns:1fr 1.1fr;gap:3mm;margin-top:2mm">
  {code(pj + "\n  … }", "the contract: target/pacts/shop-orders.json", kind="plain", cls="xs out")}
  {code(pact_fail, "real output · provider renamed status → state", kind="plain", cls="xs out")}
</div>
<div class="two top" style="gap:3mm;margin-top:2.4mm">
  {ticks(["<b>The consumer asks only for what it uses:</b> <code>id</code> and <code>status</code>. The provider’s extra <code>total</code> field didn’t matter — providers stay free to add.",
          "<b><code>stringType</code></b> matches any string; <code>stringValue</code> requires that exact value. Match on shape unless the value matters."], C4)}
  {ticks(["<b>In real life</b> contracts travel through a <b>Pact Broker</b>, and <code>can-i-deploy</code> blocks a release whose contracts aren’t verified.",
          "Pact JVM 4.7.5 on GitHub Actions: green on the current API, red once the field was renamed. <code>@State</code> methods set up each interaction’s data.",
          "Spring Cloud Contract works the other way round: the provider writes the contract and publishes stubs for consumers."], C4)}
</div>
<h2>Stub, contract or end-to-end?</h2>
{table(["", "WireMock stub (p.@@wiremock@@)", "Contract test", "End-to-end test (p.@@e2e@@)"], [
    ("Catches", "your handling of errors, timeouts, odd data", "the provider changing what consumers rely on", "broken wiring across the whole system"),
    ("Misses", "the real service changing", "behaviour beyond the request/response shape", "rare failures — and it is slow to find the cause"),
    ("Runs", "consumer build, milliseconds", "both builds, seconds", "a deployed environment, minutes")], "xs")}
''', chapter="04 · Integration &amp; API testing", color=C4)

# ============================================================================
# CH6 · ArchUnit
# ============================================================================
C6 = CH["6"]
arch_out = SPL[SPL.index("Architecture Violation"):SPL.index("[INFO] Tests run", SPL.index("Architecture Violation"))].strip()
arch_out = "\n".join(l.replace("shop.archdemo.", "").replace("shop.", "") for l in arch_out.split("\n"))

page("archunit", f'''
{sub("06 · Quality &amp; process", "Architecture tests with ArchUnit", C6)}
<p class="lede-s">Design rules written on a wiki erode one shortcut at a time. <b>ArchUnit</b> (Apache-2.0) turns them into JUnit tests over your compiled classes: a controller that reaches into a repository fails the build, with the exact line that broke the rule.</p>
<div class="two top" style="grid-template-columns:1.1fr 1fr;gap:3mm">
  {code(jx("spring/src/test/java/shop/ArchitectureTest.java", "/** Design rules", "\n}"), "ArchitectureTest — ArchUnit 1.5.1, on the Spring project", cls="xs", right=ran("ArchitectureTest"))}
  <div>
    {code(jx("spring/src/test/java/shop/archdemo/ShortcutController.java", "/** A deliberate", "\n}"), "a deliberate violation (test sources only)", cls="xs")}
    <div style="height:1.6mm"></div>
    {code(jx("spring/src/test/java/shop/ArchitectureRulesCatchViolationsTest.java", "  @Test", "  }"), "proving the rule bites", cls="xs", right=ran("ArchitectureRulesCatchViolationsTest"))}
  </div>
</div>
{code(arch_out, "real output · the violation ArchUnit reported", kind="plain", cls="xs out wrap")}
<div class="two top" style="gap:3mm;margin-top:2.4mm">
  {ticks(["<b>Rules worth having:</b> layer direction, no cycles between packages (<code>slices().matching(&quot;..shop.(*)..&quot;).should().beFreeOfCycles()</code>), naming, and “no <code>java.util.Date</code>” style bans.",
          "<b>Add <code>.because(…)</code></b> — the reason appears in the failure, so the next developer learns the rule instead of fighting it."], C6)}
  {ticks(["<b>Prove each rule can fail</b> once, as above; a rule with a typo in a package name passes forever.",
          "<b>Existing violations?</b> <code>FreezingArchRule</code> records today’s and fails only on new ones — adopt rules without a big-bang clean-up."], C6)}
</div>
<h2>Rules worth having — ArchUnit API reference</h2>
{table(["Rule", "ArchUnit"], [
    ("Layers only call downwards", "<code>layeredArchitecture().consideringAllDependencies().layer(…).definedBy(…).whereLayer(…).mayOnlyBeAccessedByLayers(…)</code>"),
    ("No cycles between feature packages", "<code>slices().matching(&quot;..shop.(*)..&quot;).should().beFreeOfCycles()</code>"),
    ("Domain code stays framework-free", "<code>noClasses().that().resideInAPackage(&quot;..domain..&quot;).should().dependOnClassesThat().resideInAPackage(&quot;org.springframework..&quot;)</code>"),
    ("No field injection", "<code>GeneralCodingRules.NO_CLASSES_SHOULD_USE_FIELD_INJECTION</code>"),
    ("No <code>System.out</code> or generic exceptions", "<code>NO_CLASSES_SHOULD_ACCESS_STANDARD_STREAMS</code>, <code>NO_CLASSES_SHOULD_THROW_GENERIC_EXCEPTIONS</code>"),
    ("Naming", "<code>classes().that().areAnnotatedWith(RestController.class).should().haveSimpleNameEndingWith(&quot;Controller&quot;)</code>")], "xs")}
<p class="small muted" style="margin-top:1.2mm">The three rules in <code>ArchitectureTest</code> above ran in CI. The rows in this table come from ArchUnit’s user guide and its <code>GeneralCodingRules</code> library — not run here.</p>
''', chapter="06 · Quality &amp; process", color=C6)
