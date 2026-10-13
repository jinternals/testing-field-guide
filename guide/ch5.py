from lib import *

C = CH["5"]

# ============================================================================
# CH5 · e2e
# ============================================================================
TOOLS = [("Playwright for Java", "Chromium, Firefox, WebKit", "Auto-waits for elements; traces with screenshots; one API for browsers and HTTP", "Microsoft · 1.63"),
         ("Selenium WebDriver", "Every major browser", "W3C WebDriver standard; Selenium Grid runs tests in parallel across machines", "4.51"),
         ("Cypress", "Chromium-family, Firefox, WebKit (exp.)", "Runs inside the browser; tests are JavaScript/TypeScript only — not Java", "JS/TS"),
         ("REST Assured", "— (HTTP)", "Java DSL for end-to-end API checks: <code>given().when().get().then()</code>", "6.1")]
_E2E = (JAVA / "ci-logs/extras/extras-verify.log").read_text()
_m = re.search(r"Tests run: (\d+), Failures: 0, Errors: 0, Skipped: 0, Time elapsed: ([\d.]+) s -- in shop.e2e.CheckoutE2EIT", _E2E)
PW_RUN = f"{_m.group(1)} ✔ · {_m.group(2)} s"
tools = "".join(f'<tr><td class="nm">{a}</td><td>{b}</td><td>{c}</td><td class="hn">{d}</td></tr>' for a, b, c, d in TOOLS)

PW = """class CheckoutPage {                       // a Page Object
  private final Page page;
  CheckoutPage(Page page) { this.page = page; }

  void addToCart(String product) {
    page.getByRole(AriaRole.BUTTON,
        new Page.GetByRoleOptions().setName("Add " + product)).click();
  }
  void checkout() { page.getByTestId("checkout").click(); }
  Locator total() { return page.getByTestId("order-total"); }
}

@Test
void bookOrderShowsDiscountedTotal() {
  var checkout = new CheckoutPage(page);
  checkout.addToCart("Book");
  checkout.checkout();
  assertThat(checkout.total()).hasText("₹1,140.00"); // retries until true
}"""

LOC = [("1", "Role + name", "<code>getByRole(BUTTON, name \"Checkout\")</code> — what users and screen readers see"),
       ("2", "Text", "<code>getByText(\"Order confirmed\")</code> — user-visible, but changes with copy"),
       ("3", "Label / placeholder", "<code>getByLabel(\"Email\")</code> for form fields"),
       ("4", "Test id", "<code>getByTestId</code> reads <code>data-testid</code> by default — stable, invisible to users"),
       ("5", "CSS / XPath", "<code>div.cart &gt; span:nth-child(3)</code> — last resort; breaks on any layout change")]
loc = "".join(f'<div><span>{a}</span><div><b>{b}</b> · {c}</div></div>' for a, b, c in LOC)

page("e2e", f'''
{head("05", "Chapter five", "Beyond correctness", "Passing unit and integration tests prove the parts are right. This chapter checks the whole system from the outside: real browsers clicking real pages, real load on real servers, and an attacker’s view of your code.", C)}
<h2>End-to-end &amp; UI testing</h2>
<table class="tbl xs"><thead><tr><th>Tool</th><th>Browsers</th><th>Notes</th><th>Latest</th></tr></thead><tbody>{tools}</tbody></table>
<div class="two top" style="grid-template-columns:1.45fr 1fr;gap:3.5mm;margin-top:2.6mm">
  <div>
    {code(jfile("extras/src/test/java/shop/e2e/CheckoutE2EIT.java", "  @Test\n  void twoBooks", "  }"), "CheckoutE2EIT — real Chromium, headless", cls="xs", right=PW_RUN)}
    <figure style="margin:1.6mm 0 0"><img src="img/playwright-checkout.png" alt="Screenshot taken by Playwright in CI after the test: the shop page with two books in the cart and the total ₹1,140.00." style="width:70%;border:1px solid var(--line);border-radius:5px;display:block">
    <figcaption class="small muted" style="margin-top:1mm">Playwright’s own screenshot from the CI run, after checkout</figcaption></figure>
  </div>
  <div>
    <h2 style="margin-top:0">Choosing locators (Playwright’s order)</h2>
    <div class="steps" style="--accent:{C}">{loc}</div>
  </div>
</div>
<p class="small muted" style="margin-top:1.2mm">Real run on GitHub Actions: Playwright for Java 1.63.0 drove Chromium against a small shop page; both journeys passed, and each test saved a screenshot and a trace (<code>target/*-trace.zip</code>, open with <code>playwright show-trace</code>). The total appears 300 ms after checkout — the assertion waited for it, no sleep.</p>
<div class="three top" style="margin-top:1.6mm">
  <div class="card"><b class="h">Page Objects</b>Wrap each page in a class with intent-revealing methods. When the HTML changes, you fix one class, not fifty tests.</div>
  <div class="card"><b class="h">Never sleep</b>Wait for a condition, not a duration. Playwright’s locators and web-first assertions retry automatically until a timeout.</div>
  <div class="card"><b class="h">Keep them few</b>Cover the journeys that make money or lose data — sign-up, checkout, payment — plus a few read-only smoke tests in production after each deploy.</div>
  <div class="card"><b class="h">Own your data</b>Create users and products through the API at the start of each test; don’t depend on what is already in the environment.</div>
  <div class="card"><b class="h">Accessibility</b>Run axe-core (Deque publishes Java bindings for Selenium and Playwright) on key pages; it flags missing labels and poor contrast automatically.</div>
  <div class="card"><b class="h">Traces, not guesses</b>Keep Playwright traces and screenshots as CI artefacts. Comparing screenshots also catches visual regressions — mask dates and other changing areas.</div>
</div>
''', chapter="05 · Beyond correctness", color=C, bm="05 · Beyond correctness")

# ============================================================================
# CH5 · perf
# ============================================================================
TYPES = [("Load", "Expected peak traffic, held steady", "Does it meet the latency target at normal peak?"),
         ("Stress", "Ramp beyond the peak until it breaks", "Where is the limit, and does it fail gracefully?"),
         ("Spike", "A sudden jump: 10× in seconds", "Do autoscaling, queues and pools cope?"),
         ("Soak", "Normal load for hours", "Memory leaks, connection leaks, growing queues"),
         ("Scalability", "Repeat with 1, 2, 4 instances", "Does capacity grow with hardware?")]
types = "".join(f'<tr><td class="nm">{a}</td><td>{b}</td><td>{c}</td></tr>' for a, b, c in TYPES)

PT = [("Gatling", "Java, Kotlin or Scala DSL; load tests as code; HTML reports", "3.16"),
      ("Apache JMeter", "GUI to build test plans, CLI to run them; many protocols", V("ApacheJMeter_core")),
      ("Grafana k6", "Tests in JavaScript; single binary; good CI fit", "2.3"),
      ("JMH", "Microbenchmarks for one method; handles JIT warm-up and dead-code elimination", V("jmh-core"))]
pt = "".join(f'<tr><td class="nm">{a}</td><td>{b}</td><td class="hn">{c}</td></tr>' for a, b, c in PT)

runs = capture("load-output.txt").strip().split("\n\n")
nd = capture("load-output-nodelay.txt").strip().split("\n\n")
def stat(block, key):
    for l in block.split("\n"):
        if l.startswith(key + " ") or l.startswith(key + "  "):
            return l.split()[1]
    m = re.search(key + r"=([\d,]+)", block)
    return m.group(1) if m else "?"
rows = []
for label, blk in [("1 user", runs[0]), ("10 users", runs[1]), ("50 users", runs[2]), ("1 user · TCP_NODELAY", nd[0]), ("50 users · TCP_NODELAY", nd[1])]:
    rows.append((label, stat(blk, "throughput"), stat(blk, "p50"), stat(blk, "p95"), stat(blk, "p99"), stat(blk, "max"), stat(blk, "mean")))
def num(blk, key):
    return float(stat(blk, key).replace(",", ""))
P50_SLOW, P50_FAST = num(runs[0], "p50"), num(nd[0], "p50")
T50, T50N = num(runs[2], "throughput"), num(nd[1], "throughput")
M50, M50N = num(runs[2], "mean"), num(nd[1], "mean")
lt = "".join(f'<tr><td class="nm">{a}</td><td class="c">{b}</td><td class="c">{c}</td><td class="c">{d}</td><td class="c">{e}</td><td class="c">{f}</td><td class="c">{g}</td></tr>' for a, b, c, d, e, f, g in rows)

page("perf", f'''
{sub("05 · Beyond correctness", "Performance testing", C)}
<div class="two top">
  <div>
    <h2 style="margin-top:0">Kinds of performance test</h2>
    <table class="tbl xs"><tbody>{types}</tbody></table>
  </div>
  <div>
    <h2 style="margin-top:0">Tools</h2>
    <table class="tbl xs"><tbody>{pt}</tbody></table>
    {note("Report <b>percentiles</b>, not averages. p99 = 99% of requests were at least this fast; the slowest 1% is what your busiest users feel on every page that makes many calls.", "rule")}
  </div>
</div>
<h2>A real load test — and what it found</h2>
<div class="two top" style="grid-template-columns:1.6fr 1fr;gap:3.5mm">
  {code(jfile("src/tools/shop/LoadSmoke.java", "    try (var pool", "      }\n    }", dedent=4), "LoadSmoke.java — virtual users against OrderApi", cls="xs")}
  {code(runs[2], "real output · 50 users · 2 CPUs", kind="plain", cls="xs out wrap")}
</div>
<table class="tbl xs" style="margin-top:2.4mm"><thead><tr><th>Run (10 s measured, after 3 s warm-up)</th><th class="c">req/s</th><th class="c">p50 ms</th><th class="c">p95 ms</th><th class="c">p99 ms</th><th class="c">max ms</th><th class="c">mean ms</th></tr></thead><tbody>{lt}</tbody></table>
<div class="two top" style="margin-top:2mm">
  <p class="small"><b>The finding.</b> Every request took about {P50_SLOW:.0f} ms — even with a single user, so it wasn’t load. Our handler sends the headers and the body as two separate small writes; with Nagle’s algorithm on, the second waits for the client’s delayed ACK — the classic Nagle/delayed-ACK stall. Starting the JVM with <code>-Dsun.net.httpserver.nodelay=true</code> (sets <code>TCP_NODELAY</code>) cut the single-user p50 from {P50_SLOW:.0f} ms to {P50_FAST:.2f} ms. No unit test could have found this.</p>
  <p class="small"><b>Little’s Law checks your numbers:</b> users in flight = throughput × time in system. 50 users ÷ {T50:,.0f} req/s = {50/T50*1000:.1f} ms (measured mean {M50:.1f} ms), and 50 ÷ {T50N:,.0f} = {50/T50N*1000:.1f} ms (measured {M50N:.1f} ms). If your tool’s numbers don’t satisfy it, the load generator itself is the bottleneck. These figures come from this guide’s 2-CPU sandbox: compare runs, not absolute numbers.</p>
</div>
{note("<b>Coordinated omission:</b> a closed-loop tool like this one stops sending while the server stalls, so slow periods produce fewer samples and percentiles look better than reality. Open-model tools (Gatling’s <code>constantUsersPerSec</code>, k6 arrival-rate executors) keep sending at a fixed rate.", "warn")}
''', chapter="05 · Beyond correctness", color=C)

# ============================================================================
# CH5 · sec
# ============================================================================
SEC = [("SAST", "Reads source or bytecode for dangerous patterns", "SpotBugs + Find Security Bugs, Semgrep, CodeQL", "Every build"),
       ("SCA", "Finds libraries with known vulnerabilities (CVEs)", "OWASP Dependency-Check, Dependabot, Renovate", "Every build + daily"),
       ("Secrets", "Finds keys and passwords committed to git", "gitleaks, GitHub secret scanning", "Every push"),
       ("DAST", "Attacks the running app from outside", "ZAP (now “ZAP by Checkmarx”), Burp Suite", "Nightly, on staging"),
       ("Fuzzing", "Feeds generated, malformed input to find crashes", "Jazzer (coverage-guided, JUnit integration)", "Nightly / continuous"),
       ("Pen test", "Humans think like attackers", "Internal or external security team", "Before big releases")]
sec = "".join(f'<tr><td class="nm">{a}</td><td>{b}</td><td>{c}</td><td>{d}</td></tr>' for a, b, c, d in SEC)

IDEAS = [("Access control", "User A asks for <code>/orders/{id}</code> of user B → expect 403 or 404, never 200."),
         ("Injection", "Names like <code>' OR 1=1 --</code> and <code>&lt;script&gt;</code> are stored and shown as plain text."),
         ("Authentication", "Expired, tampered and missing tokens all get 401; lock-out after repeated failures."),
         ("Input limits", "Huge bodies, deep JSON, 10,000-item lists: rejected quickly, not crashing the server."),
         ("Error leakage", "Errors return a generic message — no stack traces, SQL or internal hostnames."),
         ("Headers", "Responses with personal data send <code>Cache-Control: no-store</code>; HTTPS-only cookies.")]
ideas = "".join(f'<div class="card"><b class="h">{a}</b>{b}</div>' for a, b in IDEAS)

CHAOS = [("Timeouts", "Point the client at a server that never answers; the call must give up in time."),
         ("Slow dependency", "Add latency with Toxiproxy (a Testcontainers module); check pools don’t exhaust."),
         ("Partial failure", "Kill one instance or the cache during a load test; errors should stay bounded."),
         ("Retries", "Make the dependency fail twice then succeed; assert exactly three calls and idempotent effects.")]
chaos = "".join(f'<div class="card"><b class="h">{a}</b>{b}</div>' for a, b in CHAOS)

page("sec", f'''
{sub("05 · Beyond correctness", "Security &amp; resilience testing", C)}
<p class="lede-s">Security testing is mostly automation you add to the pipeline once, plus security cases you write like any other test. The scanners find known problems; your own tests prove your rules — who may see what — actually hold.</p>
<table class="tbl xs"><thead><tr><th>Kind</th><th>What it does</th><th>Java-friendly tools</th><th>When</th></tr></thead><tbody>{sec}</tbody></table>
<h2>Security tests you write yourself</h2>
<div class="two top" style="grid-template-columns:1.45fr 1fr;gap:3.5mm;margin-bottom:2.4mm">
  {code(jfile("OrderApiTest.java", "  @Test void pathTricksAreJustNotFound", dedent=2).rstrip("}").rstrip(), "OrderApiTest.java — hostile inputs", cls="xs", right="✔ passes")}
  <p class="small">Path traversal, SQL-looking IDs and a 5,000-character ID all get the same plain 404 — no stack trace, no SQL error, no file contents. This is a normal JUnit test; it runs on every build with the rest of the suite. The cards below are more ideas to turn into tests like this one.</p>
</div>
<div class="three">{ideas}</div>
<div class="two top" style="margin-top:2.4mm">
  {note("OWASP ranks <b>broken access control</b> as the top web application risk — for example one user reading another’s data by changing an ID. Scanners rarely find it, because they don’t know who should see what. Write explicit tests for it on every endpoint that takes an ID.", "warn")}
  {note("Fail the build on <b>new</b> high-severity findings, not on the backlog — otherwise the first scan blocks everything and people switch it off.", "rule")}
</div>
<h2>Resilience: test the failure, not just the success</h2>
<div class="four">{chaos}</div>
<p class="small muted" style="margin-top:1.6mm">Chaos engineering takes the same idea to production-like environments: inject failures deliberately (kill pods, add latency) and check the system degrades the way you designed it to.</p>
''', chapter="05 · Beyond correctness", color=C)
