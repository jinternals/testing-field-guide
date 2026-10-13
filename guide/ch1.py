from lib import *

# ============================================================================
# COVER
# ============================================================================
wire = ('<span class="dm">$ mvn test</span>\n'
        '└─ JUnit Jupiter <span class="ok">✔</span>\n'
        '   ├─ OrderServiceTest <span class="ok">✔</span>\n'
        '   │  ├─ chargesDiscountedTotalSavesAndEmails() <span class="ok">✔</span>\n'
        '   │  └─ declinedPaymentSavesNothingAndSendsNoEmail() <span class="ok">✔</span>\n'
        '   └─ DiscountPolicyTest <span class="ok">✔</span>\n'
        '      └─ ₹1000 → 5% off <span class="ok">✔</span>\n'
        f'<span class="dm">[</span>        {N_TESTS} tests successful      <span class="dm">]</span>\n'
        '<span class="dm">[</span>         0 tests failed          <span class="dm">]</span><span class="caret"></span>')
chips1 = "".join(lv(k, l) for k, l in [("static", "static"), ("unit", "unit"), ("integration", "integration"), ("contract", "contract"),
                                       ("e2e", "end-to-end"), ("perf", "performance"), ("security", "security")])
chips2 = "".join(dbl(k) for k in ["dummy", "stub", "spy", "mock", "fake"])
page("cover", f'''
<div class="cover">
  <svg class="cover-grid" viewBox="0 0 210 297" preserveAspectRatio="none" aria-hidden="true">
    <defs><pattern id="g" width="10" height="10" patternUnits="userSpaceOnUse">
      <path d="M10 0H0V10" fill="none" stroke="rgba(255,255,255,.045)" stroke-width=".25"/></pattern></defs>
    <rect width="210" height="297" fill="url(#g)"/>
  </svg>
  <div class="cover-glow" aria-hidden="true"></div>
  <div class="cover-top"><span class="edition">Field Guide · October 2026</span><span class="edition">JUnit 6 · Mockito 5 · AssertJ 3 · Java 21</span></div>
  <div class="cover-wire" role="img" aria-label="JUnit console output: {N_TESTS} tests successful, 0 failed">{wire}</div>
  <div class="cover-title">
    <div class="pre">The complete reference to</div>
    <h1>Testing <em>Java</em><br>applications</h1>
    <p>Unit, integration, API, end-to-end, performance and security testing — with JUnit 6, Mockito and AssertJ. Every code example in this guide was compiled and run, and every output shown is real.</p>
  </div>
  <div class="cover-chips">
    <div class="chip-row">{chips1}</div>
    <div class="chip-row">{chips2}</div>
  </div>
  <div class="cover-foot">
    <div><b>6</b> chapters</div><div><b>{N_TESTS}</b> tests, all run</div><div><b>5</b> test doubles</div><div><b>1</b> cheat sheet</div>
  </div>
</div>''', cls="p-cover", bm="Cover")

# ============================================================================
# CONTENTS
# ============================================================================
TOC = [
    ("01", "Foundations", "Why we test, how much of each kind, and how to choose test cases", CH["1"],
        [("Why we test &amp; the kinds of tests", "why"), ("Pyramid, trophy &amp; what makes a good test", "pyramid"), ("What to test — and what to leave out", "whattotest"), ("Designing test cases", "design")]),
    ("02", "Unit testing with JUnit 6", "Annotations, lifecycle, assertions and parameterized tests", CH["2"],
        [("Setup, architecture &amp; JUnit 6", "setup"), ("Your first test &amp; the lifecycle", "junit"), ("Assertions &amp; AssertJ", "assert"), ("Parameterized, nested &amp; more", "params"), ("Writing your own extensions", "extensions"), ("Testing logs and metrics", "observe")]),
    ("03", "Test doubles &amp; Mockito", "Replacing collaborators — and when not to", CH["3"],
        [("The five test doubles", "doubles"), ("Mockito in practice", "mockito"), ("Failure paths, call order &amp; the API", "mockito2"), ("Spies, statics, errors &amp; pitfalls", "mockpit"), ("Legacy code: characterization tests &amp; seams", "legacy")]),
    ("04", "Integration &amp; API testing", "Real HTTP, Spring Boot slices, containers and flaky tests", CH["4"],
        [("Testing a real HTTP API", "integ"), ("Spring Boot, Testcontainers &amp; contracts", "spring"), ("The @Transactional test trap", "txtrap"), ("Database migrations on real data", "migrations"), ("Messaging &amp; async with Kafka", "messaging"), ("E-mail with GreenMail", "email"), ("AWS and Azure emulators", "cloud"), ("Secured APIs: mock auth server", "authmock"), ("Other services: WireMock &amp; retries", "wiremock"), ("Contract testing with Pact", "contract"), ("Time, randomness, threads &amp; flaky tests", "tricky")]),
    ("05", "Beyond correctness", "End-to-end, performance and security testing", CH["5"],
        [("End-to-end &amp; UI testing", "e2e"), ("Performance testing", "perf"), ("Security &amp; resilience testing", "sec")]),
    ("06", "Quality &amp; process", "TDD, measuring test quality, CI and a self-check", CH["6"],
        [("Test-driven development", "tdd"), ("Coverage &amp; mutation testing", "cov"), ("Mutation testing with PIT — for real", "pit"), ("PIT in your build and CI", "pitci"), ("Coverage for unit and integration tests", "itcov"), ("Finding duplicate &amp; redundant tests", "dupes"), ("Build plugins for test quality", "plugins"), ("Architecture tests with ArchUnit", "archunit"), ("Parallel tests: threads vs JVMs", "parallel"), ("Singleton containers per JVM", "singleton"), ("Faster builds: cache &amp; shards", "speed"), ("Build tools &amp; CI pipelines", "ci"), ("Team testing conventions", "conventions"), ("Check your understanding", "interview")]),
]
toc_html = ""
for num, title, subt, col, items in TOC:
    rows = "".join(f'<a class="toc-item" href="#p-{k}"><span>{t}</span><span class="dl"></span><span class="pg">@@{k}@@</span></a>' for t, k in items)
    toc_html += f'''<div class="toc-ch" style="--accent:{col}"><div class="toc-num">{num}</div>
      <div class="toc-body"><a href="#p-{items[0][1]}" class="toc-title">{title}</a><div class="toc-sub">{subt}</div>{rows}</div></div>'''

legend = "".join(f'<div class="lg-row">{lv(k, l)}<span>{v}</span></div>' for k, l, v in [
    ("static", "static", "checked without running"), ("unit", "unit", "one class, in memory"), ("integration", "integration", "real parts together"),
    ("contract", "contract", "agreed API shape"), ("e2e", "end-to-end", "the whole system"), ("perf", "performance", "speed under load"),
    ("security", "security", "attacks &amp; weaknesses")])

page("toc", f'''
<div class="toc-wrap">
  <div class="toc-left">
    <div class="kicker">Inside</div>
    <h1 class="toc-h">Contents</h1>
    {toc_html}
    <a class="toc-item toc-extra" href="#p-cheat"><span><b>Cheat sheet</b> — one page to pin above your desk</span><span class="dl"></span><span class="pg">@@cheat@@</span></a>
    <a class="toc-item toc-extra" href="#p-check"><span><b>Testing checklist, references &amp; how this guide was verified</b></span><span class="dl"></span><span class="pg">@@check@@</span></a>
    <a class="toc-item toc-extra" href="#p-index"><span><b>Index A–Z</b></span><span class="dl"></span><span class="pg">@@index@@</span></a>
    <div class="toc-hint">Versions and facts as of October 2026. Every entry, page reference and footer link is clickable.</div>
  </div>
  <aside class="toc-right">
    <div class="side-card">
      <div class="side-h">Colour language</div>
      <p class="small">Each kind of test keeps one colour on every page. Test doubles have their own: {dbl("stub")} {dbl("mock")}</p>
      <div style="margin-top:2mm">{legend}</div>
    </div>
    <div class="side-card">
      <div class="side-h">Callouts</div>
      {note("Practical advice you can apply today.", "tip")}
      {note("A mistake that shows up in real code bases.", "warn")}
      {note("A default that is right most of the time.", "rule")}
    </div>
    <div class="side-card quote">
      <p>“Program testing can be used to show the presence of bugs, but never to show their absence!”</p>
      <span>— Edsger W. Dijkstra</span>
    </div>
  </aside>
</div>''', chapter="Contents", bm="Contents")

# ============================================================================
# CH1 · why
# ============================================================================
KINDS = [
    (lv("static", "static"), "Code style, likely bugs, types — without running anything", "Whole code base", "Seconds", "javac -Xlint, Error Prone, SpotBugs, Checkstyle" + " · " + ", ".join(ref(x) for x in ['plugins', 'archunit'])),
    (lv("unit", "unit"), "One class or function; collaborators replaced by doubles", "Single process, no I/O", "Milliseconds", "JUnit, AssertJ, Mockito" + " · " + ", ".join(ref(x) for x in ['junit', 'mockito'])),
    (lv("integration", "integration"), "Your code with real neighbours: DB, HTTP, queue, framework", "Process + real dependencies", "Sub-second to seconds", "Spring Boot test slices, Testcontainers, WireMock" + " · " + ", ".join(ref(x) for x in ['spring', 'wiremock'])),
    (lv("contract", "contract"), "Consumer and provider agree on the API shape", "Two services, one at a time", "Seconds", "Pact, Spring Cloud Contract" + " · " + ", ".join(ref(x) for x in ['contract'])),
    (lv("e2e", "end-to-end"), "A user journey through the deployed system", "Browser / client → all services", "Seconds to minutes", "Playwright, Selenium, REST Assured" + " · " + ", ".join(ref(x) for x in ['e2e'])),
    (lv("perf", "performance"), "Latency, throughput and limits under load", "Production-like environment", "Minutes to hours", "Gatling, JMeter, k6, JMH" + " · " + ", ".join(ref(x) for x in ['perf'])),
    (lv("security", "security"), "Known weaknesses, vulnerable libraries, attack paths", "Code, dependencies, running app", "Minutes", "ZAP, OWASP Dependency-Check, Jazzer" + " · " + ", ".join(ref(x) for x in ['sec', 'authmock'])),
]
kinds = "".join(f'<tr><td>{a}</td><td>{b}</td><td>{c}</td><td>{d}</td><td>{e}</td></tr>' for a, b, c, d, e in KINDS)

gloss = [("SUT", "System under test — the class or system being tested."), ("Fixture", "Everything set up so a test can run."),
         ("Assertion", "A check that fails the test if it is false."), ("Test double", "A stand-in for a real collaborator."),
         ("Regression", "Something that used to work and broke."), ("Flaky test", "Passes and fails without any code change."),
         ("Test oracle", "How you know the expected answer."), ("Smoke test", "A quick check that the build basically works."),
         ("Acceptance test", "Checks a requirement from the user’s view."), ("Coverage", "Which code the tests executed."),
         ("Mutation score", "Share of injected bugs the tests caught."), ("Test suite", "A group of tests run together.")]
gl = "".join(f'<div class="gl"><b>{a}</b>{b}</div>' for a, b in gloss)

page("why", f'''
{head("01", "Chapter one", "Foundations", "A test is code that runs your code and checks the answer. Good tests let you change software quickly without breaking it; bad ones slow you down and still let bugs through. This chapter covers what to test, how much of each kind, and how to pick the cases.", CH["1"])}
<h2>What tests buy you</h2>
<div class="four">
  <div class="concept-card" style="--accent:{CH['1']}"><div class="cc-h">Fast feedback</div><p>Find a mistake seconds after you make it, not weeks later in production.</p></div>
  <div class="concept-card" style="--accent:{CH['1']}"><div class="cc-h">Safe change</div><p>Refactor or upgrade a library and know at once whether behaviour changed.</p></div>
  <div class="concept-card" style="--accent:{CH['1']}"><div class="cc-h">Living docs</div><p>A test named <code>declinedPaymentSavesNothing</code> states a rule that can’t go out of date.</p></div>
  <div class="concept-card" style="--accent:{CH['1']}"><div class="cc-h">Better design</div><p>Code that is hard to test is usually too coupled. Tests push you to inject dependencies.</p></div>
</div>
<h2>The kinds of tests</h2>
<table class="tbl sm"><thead><tr><th>Kind</th><th>What it checks</th><th>Scope</th><th>Speed</th><th>Java tools</th></tr></thead><tbody>{kinds}</tbody></table>
{note("Google’s <em>Software Engineering at Google</em> sorts tests by <b>size</b> instead of name: <b>small</b> tests run in one process, <b>medium</b> tests on one machine (they may call localhost), <b>large</b> tests anywhere. Size predicts speed and flakiness better than labels like “integration”, which teams define differently.", "info")}
<h2>Vocabulary</h2>
<div class="gloss">{gl}</div>
''', chapter="01 · Foundations", color=CH["1"], bm="01 · Foundations")

# ============================================================================
# CH1 · pyramid
# ============================================================================
def pyramid():
    b = []
    # pyramid
    tiers = [("E2E", LV["e2e"], 0.30), ("Integration", LV["integration"], 0.62), ("Unit", LV["unit"], 1.0)]
    top, H, cx, W = 22, 46, 120, 200
    for i, (name, c, wf) in enumerate(tiers):
        y0 = top + i * H; y1 = y0 + H - 3
        w0 = W * (tiers[i - 1][2] if i else 0.0) + (6 if i else 0); w1 = W * wf
        b.append(f'<path d="M{cx - w0/2:.0f},{y0} L{cx + w0/2:.0f},{y0} L{cx + w1/2:.0f},{y1} L{cx - w1/2:.0f},{y1} Z" fill="{c}" fill-opacity=".14" stroke="{c}"/>')
        b.append(f'<text x="{cx}" y="{y0 + H/2 + 3:.0f}" text-anchor="middle" font-size="10" font-weight="700" fill="{c}">{name}</text>')
    b.append(f'<text x="{cx}" y="12" text-anchor="middle" font-size="9" font-weight="700" fill="#334155" letter-spacing="1">TEST PYRAMID · COHN, 2009</text>')
    b.append('<text x="235" y="40" font-size="7.5" fill="#5B6474">slower, costlier,</text><text x="235" y="50" font-size="7.5" fill="#5B6474">more realistic</text>')
    b.append('<text x="235" y="140" font-size="7.5" fill="#5B6474">faster, cheaper,</text><text x="235" y="150" font-size="7.5" fill="#5B6474">more isolated</text>')
    b.append('<line x1="228" y1="58" x2="228" y2="128" stroke="#94A3B8" marker-start="url(#pa)" marker-end="url(#pa)"/>')
    # trophy
    ox = 330
    parts = [("E2E", LV["e2e"], 70, 18), ("Integration", LV["integration"], 140, 52), ("Unit", LV["unit"], 96, 26), ("Static", LV["static"], 120, 16)]
    y = 22
    b.append(f'<text x="{ox + 75}" y="12" text-anchor="middle" font-size="9" font-weight="700" fill="#334155" letter-spacing="1">TESTING TROPHY · DODDS, 2018</text>')
    for name, c, w, h in parts:
        b.append(f'<rect x="{ox + 75 - w/2}" y="{y}" width="{w}" height="{h}" rx="5" fill="{c}" fill-opacity=".14" stroke="{c}"/>')
        b.append(f'<text x="{ox + 75}" y="{y + h/2 + 3.5:.0f}" text-anchor="middle" font-size="{10 if h > 20 else 8.5}" font-weight="700" fill="{c}">{name}</text>')
        y += h + 4
    b.append(f'<rect x="{ox + 55}" y="{y}" width="40" height="8" fill="#94A3B8" fill-opacity=".3"/><rect x="{ox + 40}" y="{y + 8}" width="70" height="8" rx="2" fill="#94A3B8" fill-opacity=".3"/>')
    return svg(ARROW.format(id="pa", c="#94A3B8") + "".join(b), 520, 176,
               "The test pyramid: many unit tests at the base, fewer integration tests, few end-to-end tests at the top. "
               "The testing trophy: static analysis base, some unit tests, the most integration tests, few end-to-end tests.")

FIRST = [("F", "Fast", "Milliseconds. Slow tests stop being run."), ("I", "Independent", "No shared state; any order, in parallel."),
         ("R", "Repeatable", "Same result anywhere: no real clock, network or randomness."), ("S", "Self-validating", "Pass or fail by itself; nobody reads logs."),
         ("T", "Timely", "Written with (or before) the code, not months later.")]
first = "".join(f'<div class="card" style="text-align:center"><b class="h" style="font-family:var(--serif);font-size:20pt;color:{CH["1"]};margin:0">{a}</b><b class="h">{b}</b>{c}</div>' for a, b, c in FIRST)

page("pyramid", f'''
{sub("01 · Foundations", "Pyramid, trophy &amp; what makes a good test", CH["1"])}
{pyramid()}
<div class="two" style="margin-top:1.5mm">
  <p class="small"><b>The pyramid</b> says: write many fast unit tests, fewer integration tests and only a handful of end-to-end tests, because cost and flakiness grow as you go up. It came from Mike Cohn’s <em>Succeeding with Agile</em> (2009).</p>
  <p class="small"><b>The trophy</b> moves the weight to integration tests, arguing they give the most confidence per test, with static analysis as the base. Both agree on the real rule: <b>push each check down to the cheapest level that can catch the bug.</b></p>
</div>
<h2>FIRST: five properties of a good unit test</h2>
<div class="five" style="display:grid;grid-template-columns:repeat(5,1fr);gap:2.4mm">{first}</div>
<p class="small muted" style="margin-top:1mm">Acronym by Tim Ottinger and Brett Schuchert, popularised in Robert C. Martin’s <em>Clean Code</em>.</p>
<div class="two top">
  <div>
    <h2>Arrange · Act · Assert</h2>
    {code(jfile("MoneyTest.java", "  @Test\n  @DisplayName", "discounted); // Assert\n  }", dedent=2), "MoneyTest.java", right="✔ passes", cls="sm")}
    <p class="small" style="margin-top:1.4mm">Three blocks, separated by blank lines. <b>Given / When / Then</b> is the same idea in BDD words. If “Act” needs more than one line, the API under test is probably awkward.</p>
  </div>
  <div>
    <h2>Naming tests</h2>
    {table(["Style", "Example"], [
        ("Behaviour sentence", "<code>declinedPaymentSavesNothingAndSendsNoEmail</code>"),
        ("method_state_result", "<code>placeOrder_emptyItems_throws</code>"),
        ("should…", "<code>shouldRejectNegativeAmounts</code>"),
        ("@DisplayName", "<code>\"10% off ₹999.99 rounds half-up\"</code>")], "sm")}
    {dd("Do", ["Test <b>behaviour</b> through the public API", "One reason to fail per test", "Make failures explain themselves"],
        "Don’t", ["Assert on private fields or call order you don’t care about", "Share mutable state between tests", "Put <code>if</code> or loops with logic in a test"])}
  </div>
</div>
''', chapter="01 · Foundations", color=CH["1"])

# ============================================================================
# CH1 · design
# ============================================================================
def number_line():
    b = []
    x0, x1, y = 20, 500, 52
    zones = [(20, 60, "invalid", "#B91C1C", "&lt; 0 → error"), (60, 220, "0 %", LV["static"], "₹0 – ₹999.99"),
             (220, 380, "5 %", LV["unit"], "₹1000 – ₹4999.99"), (380, 500, "10 %", CH["6"], "≥ ₹5000")]
    for a, z, name, c, sub_ in zones:
        b.append(f'<rect x="{a}" y="{y - 26}" width="{z - a}" height="20" fill="{c}" fill-opacity=".07" stroke="{c}"/>')
        b.append(f'<text x="{(a + z)/2}" y="{y - 12.5}" text-anchor="middle" font-size="{8 if name == "invalid" else 9}" font-weight="700" fill="{c}">{name}</text>')
        b.append(f'<text x="{(a + z)/2}" y="{y + 34}" text-anchor="middle" font-size="7.5" fill="#334155">{sub_}</text>')
    b.append(f'<line x1="{x0}" y1="{y}" x2="{x1}" y2="{y}" stroke="#334155" stroke-width="1.2"/>')
    pts = [(60, "0"), (206, "999.99"), (220, "1000"), (234, "1000.01"), (368, "4999.99"), (380, "5000"), (470, "250000")]
    for x, l in pts:
        b.append(f'<circle cx="{x}" cy="{y}" r="3.2" fill="#0F172A"/>')
    labels = [(60, "0", 0), (206, "999.99", -1), (234, "1000.01", 1), (220, "1000", 0), (368, "4999.99", -1), (380, "5000", 1), (470, "250000", 0)]
    for x, l, side in labels:
        anchor = "end" if side < 0 else ("start" if side > 0 else "middle")
        dx = -3 if side < 0 else (3 if side > 0 else 0)
        b.append(f'<text x="{x + dx}" y="{y + (12 if side == 0 else 21)}" text-anchor="{anchor}" font-size="7" class="mn" fill="#0F172A" font-weight="700">{l}</text>')
    b.append(f'<text x="{x0}" y="10" font-size="7.5" fill="#5B6474">● = a value tested in DiscountPolicyTest — one inside each partition plus both sides of every boundary</text>')
    return svg("".join(b), 520, 92, "Number line of order subtotals split into four partitions: below zero is invalid, 0 to 999.99 gets 0 percent, 1000 to 4999.99 gets 5 percent, 5000 and above gets 10 percent. Tested values sit at each boundary.")

dt = table(["Rule", "1", "2", "3", "4"], [
    ("Items present?", "no", "yes", "yes", "yes"),
    ("Payment approved?", "—", "no", "yes", "yes"),
    ("Subtotal ≥ ₹1000?", "—", "—", "no", "yes"),
    ("<b>Outcome</b>", "reject, call nobody", "throw, save nothing", "save, email, 0%", "save, email, 5–10%"),
    ("<b>Test</b>", "<code>emptyOrderIsRejected…</code>", "<code>declinedPayment…</code>", "<code>chargesBeforeSaving</code>", "<code>chargesDiscounted…</code>"),
], "xs")

TECH = [("Equivalence partitioning", "Split inputs into groups the code treats the same; test one value from each.", "Fewer tests, same coverage of behaviour"),
        ("Boundary value analysis", "Test on and either side of every edge: 999.99, 1000, 1000.01.", "Catches off-by-one and <code>&gt;</code> vs <code>&gt;=</code>"),
        ("Decision table", "List every combination of conditions and the expected action.", "Business rules with several inputs"),
        ("State transition", "Test each allowed move between states — and the forbidden ones.", "Orders, payments, workflows"),
        ("Pairwise", "Cover every <em>pair</em> of option values instead of every combination.", "Config and browser/OS matrices"),
        ("Property-based", "State a rule (“total ≥ 0”) and let a tool generate hundreds of inputs.", "Parsers, maths, serialisation (jqwik)"),
        ("Error guessing", "Use experience: null, empty, huge, Unicode, duplicates, time zones.", "Finds what specs forget")]
page("design", f'''
{sub("01 · Foundations", "Designing test cases", CH["1"])}
<p class="lede-s">You can’t test every input, so pick the few that are most likely to find bugs. The rule: <code>DiscountPolicy</code> gives 0% below ₹1000, 5% from ₹1000 and 10% from ₹5000.</p>
{number_line()}
<div class="two top" style="margin-top:2mm;grid-template-columns:1.32fr 1fr;gap:3mm">
  {code(jfile("DiscountPolicyTest.java", "  @ParameterizedTest", "\n  }", dedent=2), "DiscountPolicyTest.java", cls="xs")}
  {code(capture("suite-output.txt").split("├─ DiscountPolicyTest ✔")[1].split("├─ PasswordPolicyTest")[0].replace("   │  ", "").replace("   │", "").strip(), "test output · JUnit 6.1.3", kind="out", cls="xs", right="7 / 7 passed")}
</div>
<p class="small muted" style="margin-top:1.2mm">Mistype <code>&gt;=</code> as <code>&gt;</code> and only the <b>₹1000</b> row fails — see the mutation demo on {ref("cov")}. Middle-of-range values like ₹2000 would never notice.</p>
<h2>Decision table for <code>placeOrder</code></h2>
{dt}
<h2>Test design techniques</h2>
{table(["Technique", "How", "Best for"], TECH, "xs")}
<h2>Inputs worth trying on almost anything</h2>
<div class="four">
  <div class="card"><b class="h">Empty &amp; missing</b><code>null</code>, <code>""</code>, empty list, missing JSON field, zero items.</div>
  <div class="card"><b class="h">Extremes</b><code>0</code>, <code>-1</code>, <code>Integer.MAX_VALUE</code>, 10 MB strings, 10,000 rows.</div>
  <div class="card"><b class="h">Text</b>Unicode (₹, emoji, Hindi), leading spaces, mixed case, SQL and HTML characters.</div>
  <div class="card"><b class="h">Time</b>Midnight, 29 Feb, month end, DST change, a different time zone.</div>
</div>
''', chapter="01 · Foundations", color=CH["1"])
