"""Chapter 4: the @Transactional test trap — real Spring Boot tests against PostgreSQL (CI logs)."""
from lib import *

C = CH["4"]
CHAP = "04 · Integration &amp; API testing"
SP = JAVA / "ci-logs" / "spring"


def slog(name):
    return (SP / name).read_text(errors="replace")


SV = slog("spring-verify.log")
runs = dict((m.group(2), m.group(1)) for m in re.finditer(r"Tests run: (\d+), Failures: 0, Errors: 0, Skipped: 0, Time elapsed: [\d.]+ s -- in shop\.(\w+)", SV))
times = dict((m.group(2), m.group(1)) for m in re.finditer(r"Tests run: \d+, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: ([\d.]+) s -- in shop\.(\w+)", SV))
dup_err = re.search(r"ERROR: duplicate key value violates unique constraint \"(\w+)\"", SV).group(0)

RB = jfile("spring/src/test/java/shop/OrderRepositoryIT.java", "@DataJpaTest\n@Import", "\n}")
CM = jfile("spring/src/test/java/shop/OrderFlowIT.java", "  @Autowired OrderRepository repository;", "        .isInstanceOf(LazyInitializationException.class);\n  }")
FIX = jfile("spring/src/main/java/shop/OrderService.java", "  /** Map to a view", "\n  }", test=False)

OUT = [
    ("Duplicate <code>reference</code>", "<code>save()</code> succeeds; the error appears only at <code>flush()</code> — and a test that never flushes stays green", "<code>save()</code> commits and throws <code>DataIntegrityViolationException</code>"),
    ("Lazy <code>lines</code> collection", "<code>getLines()</code> loads, because the test’s transaction is still open", "<code>LazyInitializationException</code> — the real behaviour with <code>open-in-view=false</code>"),
    ("Data left behind", "none — rolled back after each test", "rows stay: clean up in <code>@BeforeEach</code>"),
]

page("txtrap", f'''
{sub(CHAP, "<code>@Transactional</code> in tests: what the rollback hides", C)}
<p class="lede-s"><code>@DataJpaTest</code> — and any test class annotated <code>@Transactional</code> — runs each test inside a transaction that is <b>rolled back</b>. That keeps the database clean, but nothing is ever committed, so two kinds of production bug can’t happen in the test. The same code, run both ways against real PostgreSQL:</p>
<div class="two top" style="grid-template-columns:1fr 1fr;gap:3mm">
  {code(RB, "rolled back · OrderRepositoryIT", cls="xs", right=f"{runs.get('OrderRepositoryIT', '?')} ✔")}
  {code(CM, "committed · OrderFlowIT (@SpringBootTest, no @Transactional)", cls="xs", right=f"{runs.get('OrderFlowIT', '?')} ✔")}
</div>
<h2>Same code, two outcomes</h2>
{table(["", "Inside a rolled-back test transaction", "Committed, as in production"], OUT, "xs")}
<p class="small muted" style="margin-top:1.2mm">PostgreSQL’s message in both runs: <code>{esc(dup_err)}</code>. Spring translates it to <code>DataIntegrityViolationException</code>. Every test above passes — each one asserts what really happens.</p>
<div class="two top" style="grid-template-columns:1.12fr 1fr;gap:3mm;margin-top:2mm">
  <div>
    <h2 style="margin-top:0">The fix the committed test protects</h2>
    {code(FIX, "OrderService.java — map to plain data inside the transaction", cls="xs")}
  </div>
  {ticks(["<b>No <code>@Transactional</code> on <code>@SpringBootTest</code> tests.</b> Let each call commit as it would in production; clean up in <code>@BeforeEach</code>.",
          "<b>In <code>@DataJpaTest</code>, flush.</b> Testing a constraint or a mapping? Call <code>flush()</code> or <code>saveAndFlush()</code> so the SQL actually runs.",
          "<b>Turn off open-in-view</b> (<code>spring.jpa.open-in-view=false</code>) so lazy loading can’t silently happen while JSON is written.",
          "<b>Return DTOs, not entities,</b> from transactional services — then no lazy proxy can escape.",
          "Keep the fast rolled-back tests; add <b>one committed-path test</b> per repository or flow."], C)}
</div>
<div class="two top" style="grid-template-columns:1.12fr 1fr;gap:3mm;margin-top:2mm">
  {code(f"✔ OrderRepositoryIT  {runs['OrderRepositoryIT']} tests  {times['OrderRepositoryIT']} s  (starts PostgreSQL)\n✔ OrderFlowIT        {runs['OrderFlowIT']} tests  {times['OrderFlowIT']} s\n\nWARN  org.hibernate.orm.jdbc.error : {dup_err}", "real run · Spring Boot 4.1.1 · GitHub Actions", kind="plain", cls="xs out wrap")}
  {note("Rolled-back tests are still the right default for queries, mappings and repository methods — they are fast and leave nothing behind. Call <code>flush()</code> and <code>clear()</code> on the <code>EntityManager</code> (or <code>TestEntityManager</code>) before reading back, so the data really comes from the database.", "info")}
</div>
''', chapter=CHAP, color=C)
