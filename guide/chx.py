"""New pages: JUnit extensions, logs & metrics, legacy code, messaging, cloud emulators, mock auth server, faster builds.
Every output comes from the GitHub Actions logs in java/ci-logs/."""
from lib import *

LOGS = JAVA / "ci-logs"


def log(path):
    return (LOGS / path).read_text(errors="replace")


EX = log("extras/extras-verify.log")
AU = log("extras/auth-verify.log")
RUN = {}
for m in re.finditer(r"Tests run: (\d+), Failures: 0, Errors: 0, Skipped: (\d+), Time elapsed: ([\d.]+) s -- in shop\.(?:[a-z]+\.)?(\w+)", EX + AU):
    RUN[m.group(4)] = (m.group(1), m.group(2), m.group(3))


def ran(cls):
    n, skipped, secs = RUN[cls]
    return f"{n} tests, {skipped} skipped" if skipped != "0" else f"{n} ✔ · {secs} s"


def jx(path, start=None, end=None, dedent=0):
    return jfile(path, start, end, dedent=dedent)


def started(image):
    m = re.search(r"Container " + re.escape(image) + r" started in PT([\d.]+)S", EX)
    return f"{float(m.group(1)):.1f}"


# ============================================================================
# CH2 · writing your own JUnit extensions
# ============================================================================
C2 = CH["2"]
timing = "\n".join(l for l in EX.split("\n") if l.startswith("[timing]"))
EXT_POINTS = [
    ("<code>BeforeAllCallback</code>, <code>BeforeEachCallback</code>, <code>…TestExecutionCallback</code>, <code>After…</code>", "set up and tear down around tests — like <code>@BeforeEach</code>, but reusable"),
    ("<code>ParameterResolver</code>", "inject arguments into test methods and constructors"),
    ("<code>ExecutionCondition</code>", "decide whether a test runs at all"),
    ("<code>TestExecutionExceptionHandler</code>", "react to — or swallow — exceptions thrown by tests"),
    ("<code>TestWatcher</code>", "hear about results: passed, failed, aborted, disabled"),
    ("<code>InvocationInterceptor</code>", "wrap the call itself, e.g. run it on another thread"),
]
page("extensions", f'''
{sub("02 · Unit testing with JUnit 6", "Writing your own JUnit extensions", C2)}
<p class="lede-s">When the same setup appears in many test classes — a fixed clock, a timer, a test database — turn it into an <b>extension</b>. Extensions plug into the test lifecycle through small interfaces; a composed annotation then gives the whole team one line to write.</p>
<div class="two top" style="grid-template-columns:1fr 1fr;gap:3mm">
  <div>
    {code(jx("extras/src/test/java/shop/junitext/FixedClockExtension.java", "/** Resolves", "\n}"), "FixedClockExtension — a ParameterResolver", cls="xs")}
    <div style="height:1.6mm"></div>
    {code(jx("extras/src/test/java/shop/junitext/TimingExtension.java", "/** Reports", "\n}"), "TimingExtension — lifecycle callbacks + the Store", cls="xs")}
  </div>
  <div>
    {code(jx("extras/src/test/java/shop/junitext/ShopTest.java", "/** One annotation", "\n"), "ShopTest — a composed annotation", cls="xs")}
    <div style="height:1.6mm"></div>
    {code(jx("extras/src/test/java/shop/junitext/DeliveryDateTest.java", "@ShopTest", "  @Test\n  @FixedClock") .rsplit("\n  @Test", 1)[0] + "\n  // … @RepeatedTest(3), TestInfo — see the repo\n}", "DeliveryDateTest — using it", cls="xs")}
    <div style="height:1.6mm"></div>
    {code(timing + f"\nTests run: {RUN['DeliveryDateTest'][0]}, Failures: 0", "real output · Surefire 3.6.0", kind="plain", cls="xs out")}
  </div>
</div>
<h2>Extension points you will use</h2>
<div class="two top" style="grid-template-columns:1.35fr 1fr;gap:3mm">
  {table(["Interface", "Use it to"], EXT_POINTS, "xs")}
  {ticks(["<b>Register</b> with <code>@ExtendWith</code> (as above), a <code>static @RegisterExtension</code> field when you need to configure it, or automatically through <code>ServiceLoader</code> with <code>junit.jupiter.extensions.<wbr>autodetection.enabled=true</code>.",
          "<b>Keep state in the <code>ExtensionContext.Store</code></b>, never in fields: one extension instance serves many tests, possibly in parallel.",
          "<code>TestInfo</code> and <code>RepetitionInfo</code> are built-in parameter resolvers — that is how <code>@RepeatedTest</code> tells you which run it is.",
          "Look for an existing extension first: Mockito, Spring, Testcontainers and many libraries ship one."], C2)}
</div>
''', chapter="02 · Unit testing with JUnit 6", color=C2)

# ============================================================================
# CH2 · asserting logs and metrics
# ============================================================================
page("observe", f'''
{sub("02 · Unit testing with JUnit 6", "Testing logs and metrics", C2)}
<p class="lede-s">On-call engineers read your log lines, and alerts fire on your metrics. If a refactoring silently drops a warning or renames a counter, production monitoring goes blind — so assert on them like any other output.</p>
<div class="two top" style="grid-template-columns:1fr 1fr;gap:3mm">
  {code(jx("extras/src/main/java/shop/observe/PaymentService.java", "public class PaymentService", "\n}"), "PaymentService.java", cls="xs")}
  <div>
    {code(jx("extras/src/test/java/shop/observe/PaymentServiceTest.java", "class PaymentServiceTest", "\n}"), "PaymentServiceTest — Logback ListAppender + Micrometer", cls="xs", right=ran("PaymentServiceTest"))}
  </div>
</div>
<div class="two top" style="margin-top:2.4mm">
  <div class="card"><b class="h">Logs: capture, don’t parse files</b>Attach Logback’s <code>ListAppender</code> to the logger under test and assert on level and message. Detach it afterwards so tests stay independent.</div>
  <div class="card"><b class="h">Metrics: a real registry</b>Micrometer’s <code>SimpleMeterRegistry</code> is an in-memory registry made for tests. Assert on the meter name and tags your dashboards and alerts use.</div>
</div>
<h2>Tools for each signal</h2>
{table(["Signal", "Test tool", "Assert on"], [
    ("Logs (Logback)", "<code>ListAppender</code> attached to the logger", "level, message or key, MDC values"),
    ("Logs (Spring Boot)", "<code>OutputCaptureExtension</code> → <code>CapturedOutput</code>", "text written to stdout / stderr"),
    ("Metrics (Micrometer)", "<code>SimpleMeterRegistry</code>", "meter name, tags, count or total"),
    ("Traces (OpenTelemetry)", "<code>InMemorySpanExporter</code> from opentelemetry-sdk-testing", "span names, attributes, parent/child links")], "xs")}
{note("Assert on what operators depend on — level, a stable message or key, metric name and tags — not on whole formatted lines with timestamps. Otherwise every log-format change breaks tests.", "rule")}
''', chapter="02 · Unit testing with JUnit 6", color=C2)

# ============================================================================
# CH3 · legacy code
# ============================================================================
C3 = CH["3"]
approved = (JAVA / "extras/src/test/resources/approved/invoice.txt").read_text()
STEPS = [("1 · Find the change point", "Where must the new behaviour go?"),
         ("2 · Find a test point", "Where can a test observe what that code does — a return value, a file, a call?"),
         ("3 · Break dependencies", "Open a <b>seam</b> — a place to change behaviour without editing the code there: a constructor parameter, an overridable method."),
         ("4 · Pin current behaviour", "Write <b>characterization tests</b>: they assert what the code does today, right or wrong."),
         ("5 · Change and refactor", "Now change the code; the tests tell you what else moved.")]
page("legacy", f'''
{sub("03 · Test doubles &amp; Mockito", "Testing legacy code: characterization tests &amp; seams", C3)}
<p class="lede-s">Code without tests is hard to change safely, and often hard to test without changing it first. Michael Feathers’ <i>Working Effectively with Legacy Code</i> (2004) is a book about that problem; its chapters include “The Seam Model” and “Dependency-Breaking Techniques”. The way out: make the <b>smallest</b> safe change that lets a test in, record what the code does, then improve it.</p>
<div class="five-steps" style="display:grid;grid-template-columns:repeat(5,1fr);gap:2mm">{"".join(f'<div class="card"><b class="h">{a}</b>{b}</div>' for a, b in STEPS)}</div>
<div class="two top" style="grid-template-columns:1fr 1fr;gap:3mm;margin-top:2.4mm">
  {code(jx("extras/src/main/java/shop/legacy/InvoiceReport.java", "/**", "\n}"), "InvoiceReport.java — the only change: a Clock seam", cls="xs")}
  <div>
    {code(jx("extras/src/test/java/shop/legacy/InvoiceReportCharacterizationTest.java", "  @Test", "  }"), "characterization test — a “golden master”", cls="xs", right=ran("InvoiceReportCharacterizationTest"))}
    <div style="height:1.6mm"></div>
    {code(approved.rstrip(), "src/test/resources/approved/invoice.txt", kind="plain", cls="xs out")}
  </div>
</div>
<div class="two top" style="grid-template-columns:1.1fr 1fr;gap:3mm;margin-top:2mm">
  {code(jx("extras/src/test/java/shop/legacy/InvoiceReportCharacterizationTest.java", "  @ParameterizedTest", "  })"), "probing the edges — and pinning today’s answers", cls="xs")}
  {ticks(["<b>Record, don’t judge.</b> “Totals over ₹1,000 lose ₹50” looks like a bug — but someone may rely on it. Pin it, then ask.",
          "<b>The seam:</b> <code>LocalDate.now()</code> made the output change daily. A constructor taking a <code>Clock</code> — old callers keep the no-argument one — made it testable without touching the logic.",
          "<b>Other seams:</b> subclass and override a method that does I/O; extract an interface for a static call; pass a function instead of calling a singleton.",
          "<b>Tools:</b> ApprovalTests automates the received/approved file workflow; Mockito <code>mockStatic</code> (p.@@mockpit@@) is a last-resort seam for statics."], C3)}
</div>
''', chapter="03 · Test doubles &amp; Mockito", color=C3)

# ============================================================================
# CH4 · messaging
# ============================================================================
C4 = CH["4"]
kafka_start = started("apache/kafka-native:4.3.1")
page("messaging", f'''
{sub("04 · Integration &amp; API testing", "Messaging &amp; async: Kafka with Testcontainers", C4)}
<p class="lede-s">Kafka (like most brokers) delivers <b>at least once</b>: after a consumer crash or rebalance, a message can arrive again. So the test that matters is not “can I send and receive” but “does a <b>duplicate</b> do any harm?”. A real broker in a container answers that.</p>
<div class="two top" style="grid-template-columns:1fr 1fr;gap:3mm">
  {code(jx("extras/src/main/java/shop/events/OrderEventConsumer.java", "/**", "\n}"), "OrderEventConsumer.java — idempotent by event id", cls="xs")}
  <div>
    {code(jx("extras/src/test/java/shop/events/OrderEventsIT.java", "class OrderEventsIT", "\n}"), "OrderEventsIT — real Kafka 4.3.1 broker", cls="xs", right=ran("OrderEventsIT"))}
    <div style="height:1.6mm"></div>
    {code(jx("extras/src/main/java/shop/events/OrderEventPublisher.java", "  public void publish", "  }"), "OrderEventPublisher.java (excerpt)", cls="xs")}
  </div>
</div>
<div class="two top" style="grid-template-columns:1fr 1fr;gap:3mm;margin-top:2.4mm">
  {ticks([f"<b>Real run:</b> the <code>apache/kafka-native</code> container started in {kafka_start} s; three messages arrived, two were applied.",
          "<b>Wait, don’t sleep.</b> Awaitility polls until the assertion holds or the timeout expires — fast when things work, a clear failure when they don’t.",
          "<b>Isolate tests:</b> a unique topic or consumer group per test, so leftovers from one test can’t satisfy another.",
          "<b>Test the unhappy paths:</b> a poison message, a consumer that crashes mid-batch, a redelivery after restart."], C4)}
  {table(["Option", "What it is", "Use for"], [
      ("Kafka in Testcontainers", "the real broker image, one per JVM", "the default"),
      ("<code>@EmbeddedKafka</code>", "spring-kafka-test starts a broker inside the JVM", "Spring Kafka apps"),
      ("<code>MockProducer</code> / <code>MockConsumer</code>", "kafka-clients’ in-memory test doubles", "unit tests of your own logic"),
      ("Contract tests", "the event’s schema agreed with consumers", "events crossing team lines")], "xs")}
</div>
''', chapter="04 · Integration &amp; API testing", color=C4)

# ============================================================================
# CH4 · e-mail with GreenMail
# ============================================================================
MAIL_OPTS = [
    ("Mock the port", "Mockito mock of your <code>EmailSender</code> interface (p.@@mockito@@)", "unit tests: was an e-mail requested?"),
    ("<b>GreenMail</b> in-process", "<code>greenmail-junit5</code> 2.1.14: real SMTP, IMAP, POP3 inside the test JVM", "the default: real SMTP, no Docker"),
    ("GreenMail in a container", "the <code>greenmail/standalone</code> image", "non-Java services, shared test environments"),
    ("Mailpit", "SMTP server with a web UI and REST API, in a container", "end-to-end and manual checks of real HTML mails"),
]
page("email", f'''
{sub("04 · Integration &amp; API testing", "E-mail: testing with GreenMail", C4)}
<p class="lede-s">Customers notice e-mails more than most features: a wrong total, a missing confirmation, a mail sent twice. <b>GreenMail</b> (Apache-2.0) runs a real SMTP server inside the test JVM, so your code sends real mail over a real socket — and the test reads it back.</p>
<div class="two top" style="grid-template-columns:1fr 1fr;gap:3mm">
  {code(jx("extras/src/main/java/shop/mail/OrderMailer.java", "/** Sends", "\n}"), "OrderMailer.java — plain Jakarta Mail (Angus Mail 2.0.5)", cls="xs")}
  <div>
    {code(jx("extras/src/test/java/shop/mail/OrderMailerTest.java", "/** GreenMail", "\n}"), "OrderMailerTest — GreenMail JUnit 5 extension", cls="xs", right=ran("OrderMailerTest"))}
  </div>
</div>
<div style="margin-top:2mm">
  {table(["Check in every e-mail test", "Why"], [
      ("Recipient and sender", "a wrong address is a privacy incident"),
      ("Subject and body text", "order number, total, links — what the customer reads"),
      ("Encoding", "the ₹ sign survived here because subject and body are sent as UTF-8"),
      ("Failure path", "server down or rejected: retry, queue, or tell the user")], "xs")}
</div>
<h2>Four ways to test e-mail</h2>
<div class="two top" style="grid-template-columns:1.3fr 1fr;gap:3mm">
  {table(["Option", "What it is", "Use for"], MAIL_OPTS, "xs")}
  {ticks(["<b>Assert what the customer sees:</b> recipient, subject, body — and that the server being down is an error you handle, not a lost mail.",
          "<b>Free ports:</b> <code>ServerSetupTest.SMTP</code> is a fixed port (3025); <code>.dynamicPort()</code> picks a free one, so parallel forks never clash.",
          "<b>Spring Boot:</b> point <code>spring.mail.host</code> and <code>spring.mail.port</code> at GreenMail with <code>@DynamicPropertySource</code>; <code>JavaMailSender</code> needs no change.",
          "Never let tests reach a real mail server: one wrong address and a customer gets a test mail."], C4)}
</div>
''', chapter="04 · Integration &amp; API testing", color=C4)

# ============================================================================
# CH4 · AWS + Azure emulators
# ============================================================================
moto_t, azur_t = started("motoserver/moto:5.2.4"), started("mcr.microsoft.com/azure-storage/azurite:3.37.0")
EMU = [
    ("AWS", "<b>Moto</b> (<code>motoserver/moto</code>)", "S3, SQS, DynamoDB, SNS and many more", "Apache-2.0; no account. Ran here."),
    ("AWS", "<b>LocalStack</b>", "broad AWS coverage, high fidelity", "Since 23 Mar 2026 needs a LocalStack account and <code>LOCALSTACK_AUTH_TOKEN</code>, also in CI. Skipped here."),
    ("Azure", "<b>Azurite</b>", "Blob, Queue, Table storage", "Microsoft, MIT licence. Ran here."),
    ("Azure", "Service Bus / Event Hubs emulators", "messaging", "Testcontainers modules; you must <code>acceptLicense()</code>; Service Bus needs SQL Server, Event Hubs needs Azurite"),
    ("Azure", "Cosmos DB emulator", "NoSQL database", "Testcontainers module; Linux image"),
]
page("cloud", f'''
{sub("04 · Integration &amp; API testing", "Cloud services: AWS and Azure emulators", C4)}
<p class="lede-s">Code that talks to S3, SQS or Azure Storage can be tested against <b>emulators</b> in containers: the real SDK, real HTTP, no cloud account and no bill. One abstract test class runs the same checks against every AWS emulator; Azure gets the same two tests.</p>
<div class="two top" style="grid-template-columns:1fr 1fr;gap:3mm">
  {code(jx("extras/src/test/java/shop/cloud/AwsStorageContract.java", "  @Test\n  void storesAndReadsAnInvoice", "  }\n  }\n}").rsplit("\n}", 1)[0] + "\n  // queuesAndReceivesAMessage(): SQS create / send / receive\n}", "AwsStorageContract — AWS SDK v2 (excerpt)", cls="xs")}
  <div>
    {code(jx("extras/src/test/java/shop/cloud/MotoAwsIT.java", "class MotoAwsIT", "\n}"), "MotoAwsIT — free, open source", cls="xs", right=ran("MotoAwsIT"))}
    <div style="height:1.6mm"></div>
    {code(jx("extras/src/test/java/shop/cloud/LocalStackAwsIT.java", "@EnabledIfEnvironmentVariable", "class LocalStackAwsIT extends AwsStorageContract {") + "\n  // … same tests, LocalStack endpoint\n}", "LocalStackAwsIT — only with a token", cls="xs", right=ran("LocalStackAwsIT"))}
  </div>
</div>
<div class="two top" style="grid-template-columns:1.12fr 1fr;gap:3mm;margin-top:2mm">
  {code(jx("extras/src/test/java/shop/cloud/AzureStorageIT.java", "class AzureStorageIT", "  @Test\n  void queuesAndReceivesAMessage").rsplit("\n  @Test", 1)[0] + "\n  // queuesAndReceivesAMessage(): QueueClient send / receive\n}", "AzureStorageIT — Azure SDK + Azurite", cls="xs", right=ran("AzureStorageIT"))}
  {table(["Cloud", "Emulator", "Covers", "Notes"], EMU, "xs")}
</div>
<p class="small muted" style="margin-top:1.2mm">Container start-up in our run: Moto {moto_t} s, Azurite {azur_t} s. Emulators are not the cloud: IAM policies, quotas, latency and some API details differ — keep a few smoke tests against a real account.</p>
''', chapter="04 · Integration &amp; API testing", color=C4)

# ============================================================================
# CH4 · mock auth server
# ============================================================================
LEVELS = [
    ("1 · No server", "<code>jwt()</code> from spring-security-test builds the token in memory", "controller tests: 401, 403, 200", "milliseconds"),
    ("2 · In-process server", "<code>MockOAuth2Server</code> as a library: real signed tokens, real JWKS, no Docker", "full-app tests of issuer, audience, signature", "milliseconds"),
    ("3 · Server in a container", "the same server as an image; tokens fetched over HTTP (client_credentials)", "the real token flow end to end", "seconds"),
    ("4 · Keycloak", "a full identity provider via Testcontainers (community module)", "login flows, realms, roles as configured in prod", "slowest"),
]
def _auth_out():
    out = []
    for c in ("ReportControllerTest", "InProcessAuthServerIT", "MockAuthServerIT"):
        n, _, t = RUN[c]
        out.append(f"✔ {c:<22} {n} tests  {t} s")
    m = re.search(r"mock-oauth2-server:6.0.7 started in PT([\d.]+)S", AU)
    out.append(f"\nmock-oauth2-server container started in {float(m.group(1)):.1f} s")
    for c in ("MockAuthServerIT", "InProcessAuthServerIT"):
        m = re.search(r"Started " + c + r" in ([\d.]+) seconds", AU)
        out.append(f"Spring context for {c}: {m.group(1)} s")
    return "\n".join(out)
AUTH_OUT = _auth_out()

page("authmock", f'''
{sub("04 · Integration &amp; API testing", "Secured APIs: testing with a mock auth server", C4)}
<p class="lede-s">An OAuth2 resource server checks every token’s <b>signature, issuer, audience and scope</b>. Tests need tokens that pass — and tokens that must fail. Pick the lightest level that exercises what you are checking:</p>
{table(["Level", "How", "Tests", "Speed"], LEVELS, "xs")}
<div class="two top" style="grid-template-columns:1fr 1fr;gap:3mm;margin-top:2.4mm">
  {code(jx("spring-auth/src/test/java/shop/ReportControllerTest.java", "  @Test\n  void tokenWithoutTheScopeIs403", "\n}"), "1 · @WebMvcTest + jwt()", cls="xs", right=ran("ReportControllerTest"))}
  {code(jx("spring-auth/src/test/java/shop/InProcessAuthServerIT.java", "class InProcessAuthServerIT", "  @LocalServerPort") .rsplit("\n", 1)[0] + "\n  // report(token): GET /reports/daily with the bearer token\n\n" + jx("spring-auth/src/test/java/shop/InProcessAuthServerIT.java", "  @Test\n  void tokenWithScopeIsAccepted", "  }"), "2 · in-process server (lightweight)", cls="xs", right=ran("InProcessAuthServerIT"))}
</div>
<div class="two top" style="grid-template-columns:1.12fr 1fr;gap:3mm;margin-top:2mm">
  {code(jx("spring-auth/src/test/java/shop/MockAuthServerIT.java", "  static final GenericContainer", "  static { AUTH.start(); }"), "3 · server in a container", cls="xs", right=ran("MockAuthServerIT"))}
  {ticks(["<b>Always test the failures:</b> no token (401), wrong scope (403), another issuer or audience (401). A filter chain that lets everything through passes every happy-path test.",
          "<code>mock-oauth2-server</code> 6.0.7 (navikt, MIT) puts client_credentials scopes in <code>aud</code> by default — the JSON config above adds a <code>scope</code> claim."], C4)}
</div>
<div class="two top" style="grid-template-columns:1fr 1fr;gap:3mm;margin-top:2mm">
  {code(jx("spring-auth/src/test/java/shop/MockAuthServerIT.java", "  /** client_credentials", "  }"), "3 · fetching a real token over HTTP", cls="xs")}
  {code(AUTH_OUT, "real run · Spring Boot 4.1.1 · GitHub Actions", kind="plain", cls="xs out wrap")}
</div>
''', chapter="04 · Integration &amp; API testing", color=C4)

# ============================================================================
# CH6 · faster builds
# ============================================================================
C6 = CH["6"]
cache = log("gradle/gradle-cache.log")
shard1, shard2 = log("shard-1/shard.log"), log("shard-2/shard.log")
n1 = int(re.search(r"tests run in this shard: (\d+)", shard1).group(1))
n2 = int(re.search(r"tests run in this shard: (\d+)", shard2).group(1))
wf = capture(".github/workflows/build.yml")
SHARD_YML = wf[wf.index("  shard:"):wf.index("      - name: Publish logs", wf.index("  shard:"))].rstrip()
SHARD_YML = SHARD_YML.split("          python3 - <<'PY'")[0].rstrip() + "\n          # … then count the tests this shard ran"
cache_s = re.findall(r"BUILD SUCCESSFUL in (\w+)", cache)
cache_out = "\n".join(l for l in cache.split("\n") if l.startswith(("###", "> Task", "BUILD", "3 actionable", "2 actionable", "1 actionable")) or "actionable" in l)

page("speed", f'''
{sub("06 · Quality &amp; process", "Faster builds: build cache &amp; test shards", C6)}
<p class="lede-s">When the suite gets slow, don’t delete tests — stop re-running what didn’t change, and split what must run across machines. Both below are real runs on GitHub Actions.</p>
<div class="two top" style="grid-template-columns:1fr 1fr;gap:3mm">
  <div>
    <h2 style="margin-top:0">1 · Build cache: skip unchanged work</h2>
    {code(cache_out, "real output · clean test, without and with the cache", kind="plain", cls="xs out")}
  </div>
  {ticks(["Gradle hashes every task’s inputs — sources, dependencies, JVM arguments. With <code>--build-cache</code> (or <code>org.gradle.caching=true</code>), a task whose inputs were seen before is restored <b>FROM-CACHE</b> instead of run — tests included.",
          f"<b>Real run:</b> {cache_s[0]} with the cache off, every task executed; {cache_s[1]} with it on — compiled classes and test results came from the cache that <code>gradle/actions/setup-gradle</code> keeps between CI runs.",
          "Share a <b>remote cache</b> between CI and laptops so a branch built once is cheap everywhere.",
          "Maven has no built-in build cache; the Apache Maven Build Cache Extension adds one."], C6)}
</div>
<h2>2 · Shards: split test classes across machines</h2>
{code(SHARD_YML, ".github/workflows/build.yml — two shards", kind="plain", cls="xs")}
<div class="two top" style="gap:3mm;margin-top:1.6mm">
  {ticks([f"<b>Real run:</b> shard 1 ran {n1} tests and shard 2 ran {n2} — all {n1 + n2}, on two machines at once.",
          "Split by class, never by method: <code>@BeforeAll</code> setup and shared fixtures stay together."], C6)}
  {ticks(["Balance by duration, not count, once the suite grows: the slowest shard decides the total time.",
          "Collect every shard’s JUnit XML report in one place, so a failure is visible without opening each job."], C6)}
</div>
<h2>More ways to spend less time</h2>
{table(["Technique", "How", "Watch out"], [
    ("Tags: fast vs slow", "<code>@Tag(&quot;slow&quot;)</code>; Surefire <code>groups</code>/<code>excludedGroups</code>, Gradle <code>includeTags</code>", "slow tests still need a home — nightly"),
    ("Run one module or class", "<code>mvn -pl orders -am test</code>; <code>-Dtest=OrderServiceTest</code>; Gradle <code>--tests</code>", "for the inner loop, not for CI gates"),
    ("Parallel forks", "threads for unit tests, forks for ITs (p.@@parallel@@)", "measure first — it was slower for us"),
    ("Test selection", "run only tests affected by a change (e.g. Develocity Predictive Test Selection, commercial)", "keep a full run nightly")], "xs")}
''', chapter="06 · Quality &amp; process", color=C6)
