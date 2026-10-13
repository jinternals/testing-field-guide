"""New pages: caches (Redis), scheduled jobs, Spring Batch, jcstress, testing in production.
Every output comes from the ops job's GitHub Actions logs in java/ci-logs/ops/."""
from lib import *
import os

OPSDIR = JAVA / "ci-logs" / "ops"


def olog(name):
    return (OPSDIR / name).read_text(errors="replace")


OPS = olog("ops-verify.log")
RUN = {}
for m in re.finditer(r"Tests run: (\d+), Failures: 0, Errors: 0, Skipped: 0, Time elapsed: ([\d.]+) s -- in shop\.\w+\.(\w+)", OPS):
    RUN[m.group(3)] = (m.group(1), m.group(2))


def ran(cls):
    if cls not in RUN:
        if os.environ.get("GITHUB_ACTIONS"):
            raise SystemExit(f"{cls}: no result in ops-verify.log")
        return "not run yet"                  # local preview only; CI fails above
    n, secs = RUN[cls]
    return f"{n} ✔ · {secs} s"


def sx(path, start=None, end=None, test=True, dedent=0):
    return jfile(f"spring-ops/src/{'test' if test else 'main'}/java/shop/{path}", start, end, dedent=dedent)


C4, C5 = CH["4"], CH["5"]
K4, K5 = "04 · Integration &amp; API testing", "05 · Beyond correctness"

# ============================================================================
# caches
# ============================================================================
redis_starts = [f"{float(x):.1f}" for x in re.findall(r"Container redis:8-alpine started in PT([\d.]+)S", OPS)]
SER_MSG = " ".join(re.findall(r'"([^"]+)"', re.search(r'hasMessage\((.*?)\);', (JAVA / "spring-ops/src/test/java/shop/cache/PriceCacheIT.java").read_text(), re.S).group(1))).replace("  ", " ")
CACHE_BUGS = [
    ("Cache never used", "two calls, <code>fetch()</code> ran once; the key <code>prices::book-1</code> is in Redis"),
    ("Stale after a change", "after <code>@CacheEvict</code> the next call fetches again"),
    ("Self-invocation", "<code>priceWithTax()</code> calls <code>price()</code> on <code>this</code>, not on the proxy: fetched twice, nothing in Redis"),
    ("Value can’t be stored", f"<code>Quote</code> isn’t <code>Serializable</code>: <code>IllegalStateException: {esc(SER_MSG)}</code> — on the first put, at runtime"),
    ("Never expires", "<code>getExpire()</code> is between 1 and 600 s: <code>time-to-live=10m</code> reached Redis"),
]
page("caches", f'''
{sub(K4, "Caches: Redis and <code>@Cacheable</code>", C4)}
<p class="lede-s">A cache is a second copy of the truth. Test what can go wrong: the second call must not reach the source, a change must evict, entries must expire — against a <b>real Redis</b>, where the serializer and the expiry live.</p>
<div class="two top" style="grid-template-columns:1fr 1fr;gap:3mm">
  <div>
    {code(sx("cache/PriceService.java", "@Service", test=False), "PriceService.java", cls="xs")}
    {code(sx("RedisContainer.java", "@TestConfiguration"), "RedisContainer.java — Redis 8 in Docker", cls="xs")}
    <h2 style="margin-top:1mm">Five cache bugs the tests catch</h2>
    {table(["Bug", "What the test showed"], CACHE_BUGS, "xs")}
  </div>
  {code(sx("cache/PriceCacheIT.java", "@SpringBootTest"), "PriceCacheIT — real Redis", cls="xs", right=ran("PriceCacheIT"))}
</div>
<div class="two top" style="grid-template-columns:1fr 1fr;gap:3mm;margin-top:2mm">
  {note("Tests that are not about caching set <code>spring.cache.type=none</code>, so they can’t pass by reading a value an earlier test left behind.", "rule")}
  {note(f"Our two Redis test classes use different Spring configurations, so each got its own context — and its own container (started in {redis_starts[0]} s and {redis_starts[-1]} s). Same configuration, one context, one container.", "info")}
</div>
''', chapter=K4, color=C4)

# ============================================================================
# scheduled jobs
# ============================================================================
page("scheduled", f'''
{sub(K4, "Scheduled jobs: the rule and the wiring", C4)}
<p class="lede-s">A scheduled job is two things: a <b>rule</b> (which carts are abandoned?) and <b>wiring</b> (does it really run every ten minutes?). Test the rule as a plain method with a fixed clock — fast, exact, every boundary. Test the wiring once, with the schedule shortened and Awaitility waiting for the effect.</p>
<div class="two top" style="grid-template-columns:1fr 1fr;gap:3mm">
  {code(sx("jobs/CartCleanup.java", "@Component", test=False), "CartCleanup.java", cls="xs")}
  {code(sx("jobs/CartCleanupTest.java", "/** The rule"), "CartCleanupTest — unit, fixed clock", cls="xs", right=ran("CartCleanupTest"))}
</div>
<div class="two top" style="grid-template-columns:1fr 1fr;gap:3mm;margin-top:2mm">
  {code(sx("jobs/CartCleanupScheduleIT.java", "/** The wiring"), "CartCleanupScheduleIT — real scheduler", cls="xs", right=ran("CartCleanupScheduleIT"))}
  <div>
    {code(sx("jobs/NightlyReport.java", "  /** 02:00", "zone = ZONE)", test=False, dedent=2), "NightlyReport.java — a cron schedule", cls="xs")}
    {code(sx("jobs/NightlyReportCronTest.java", "/** A cron"), "NightlyReportCronTest", cls="xs", right=ran("NightlyReportCronTest"))}
  </div>
</div>
<div class="two top" style="grid-template-columns:1fr 1fr;gap:3mm;margin-top:2mm">
  {ticks(["<b>Inject a <code>Clock</code></b>, never call <code>Instant.now()</code>: the unit test pins time and tests “exactly 24 hours” both ways.",
          "<b>Keep the rule a plain public method.</b> The <code>@Scheduled</code> method only calls it, so the rule needs no Spring.",
          "<b>The schedule is a property</b> (<code>${shop.cleanup.every:PT10M}</code>), so one test can run it every 0.2 s."], C4)}
  {ticks(["<b>A cron expression is code.</b> <code>CronExpression.parse(…).next(…)</code> answers “when next?” without waiting; pin the <code>zone</code>.",
          "<b>Wait for the effect</b> with <code>await().atMost(…)</code>; never <code>Thread.sleep</code> and hope.",
          "A <code>fixedDelay</code> job also runs once as soon as the context starts — in every <code>@SpringBootTest</code>. If it changes shared data, put it behind <code>@ConditionalOnProperty</code> and switch it off in tests."], C4)}
</div>
''', chapter=K4, color=C4)

# ============================================================================
# Spring Batch
# ============================================================================
CSV = (JAVA / "spring-ops/src/main/resources/prices.csv").read_text().strip()
step_ms = re.search(r"Step: \[importStep\] executed in (\d+)ms", OPS).group(1)
BATCH_LINES = [
    ("2", "book-1,499.00", "read, processed, <b>written</b>: 49,900 paise", "write count"),
    ("3", "book-2,1299.50", "read, processed, <b>written</b>: 129,950 paise", "write count"),
    ("4", "pen-1,-5.00", "read; the processor returns <code>null</code>: <b>filtered</b>", "filter count"),
    ("5", "book-4", "one field instead of two: <code>FlatFileParseException</code>, <b>skipped</b>", "read skip count"),
    ("6", "book-5,250", "read, processed, <b>written</b>: 25,000 paise", "write count"),
]
page("batch", f'''
{sub(K4, "Batch jobs: Spring Batch 6", C4)}
<p class="lede-s">A batch job reads, processes and writes in chunks, and must decide what to do with bad records. Test the processor as plain Java; test the whole job with <code>@SpringBatchTest</code> on a <b>small file in which every line has a purpose</b> — then the counts prove the job did the right thing with each one.</p>
<div class="two top" style="grid-template-columns:1fr 1fr;gap:3mm">
  <div>
    {code(sx("batch/ImportPricesJob.java", "  @Bean\n  Step importStep", "\n  }", test=False, dedent=2), "ImportPricesJob.java — the step", cls="xs")}
    {code(sx("batch/ToPaise.java", "/** Rupees", test=False), "ToPaise.java — the processor", cls="xs")}
  </div>
  {code(sx("batch/ImportPricesJobIT.java", "/** prices.csv"), "ImportPricesJobIT — the whole job", cls="xs", right=ran("ImportPricesJobIT"))}
</div>
<h2>prices.csv: five lines, five cases <span class="muted small" style="font-weight:400">(line 1 is the header, skipped by <code>linesToSkip(1)</code>)</span></h2>
{table(["Line", "Content", "What the job did", "Counted in"], BATCH_LINES, "xs")}
<div class="two top" style="grid-template-columns:1fr 1fr;gap:3mm;margin-top:2mm">
  {code(sx("batch/ToPaiseTest.java", "/** The processor"), "ToPaiseTest — no Batch needed", cls="xs", right=ran("ToPaiseTest"))}
  {ticks([f"The job <b>completed</b>: read 4, filtered 1, skipped 1, wrote 3 — the step ran in {step_ms} ms in CI.",
          "<code>JobOperatorTestUtils</code> (Batch 6; formerly <code>JobLauncherTestUtils</code>) starts the job with unique parameters, so it can run again.",
          "<code>spring.batch.job.enabled=false</code>: Boot otherwise runs the job when the application starts.",
          "No database needed: with <code>spring-boot-starter-batch</code> the job repository is in memory; <code>spring-boot-starter-batch-jdbc</code> stores it in tables.",
          "Batch 6 builds a step with <code>chunk(100)</code>; the transaction manager is optional (the <code>chunk(int, PlatformTransactionManager)</code> form is deprecated).",
          "Also test the <b>skip limit</b>: one more bad line than allowed must fail the job, not import half a file."], C4)}
</div>
''', chapter=K4, color=C4)

# ============================================================================
# jcstress
# ============================================================================
JC = re.sub(r"\n[ \t]*(?=\n)", "", olog("jcstress.log"))      # drop blank lines


def across(test):
    m = re.search(r"\[OK\] shop\." + test + r"\n  Results across all configurations:\n  RESULT.*?\n((?:\s+\d.*\n)+)", JC)
    return m.group(1).rstrip() if m else None


RACY_ALL = across("RacyCounterTest")
ATOMIC_ALL = across("AtomicCounterTest")
lost = re.search(r"^\s+1\s+([\d,]+)\s+([\d.]+)%", RACY_ALL, re.M)
total_racy = sum(int(x.replace(",", "")) for x in re.findall(r"^\s+\d\s+([\d,]+)", RACY_ALL, re.M))
cfg = []
for b in re.finditer(r"\[OK\] shop\.RacyCounterTest\n(?:(?!\[OK\]).)*?Compilation: split\n    first: (\S+)\n    second: (\S+)\n  JVM args: \[(.*?)\]\n(?:(?!\[OK\]).)*?\n\s+1\s+[\d,]+\s+([\d.]+)%", JC, re.S):
    cfg.append((b.group(1), b.group(2), "stress" if "Stress" in b.group(3) else "–", float(b.group(4))))
cfg = sorted(set(cfg), key=lambda r: r[3])
lo, hi = cfg[0], cfg[-1]
jc_secs = re.search(r"Total time:\s+([\d.]+) s", JC).group(1)
nproc = olog("jcstress-nproc.txt").strip()
CFG_ROWS = [(a, b, s, f"{p:.2f}%") for a, b, s, p in cfg]
atomic_out = ATOMIC_ALL if ATOMIC_ALL else "(not in this log)"
page("jcstress", f'''
{sub(K4, "Concurrency bugs: jcstress", C4)}
<p class="lede-s"><code>count++</code> looks like one step; it is three — read, add, write. Two threads can both read 0 and both write 1. An ordinary test almost never sees it: the window is nanoseconds. <b>jcstress</b> (OpenJDK) runs a tiny test hundreds of millions of times, with the interpreter, C1 and C2 and compiler stress modes, and counts every outcome.</p>
<div class="two top" style="grid-template-columns:1fr 1fr;gap:3mm">
  {code(jfile("concurrency/src/main/java/shop/RacyCounterTest.java", "/** Two"), "RacyCounterTest.java", cls="xs")}
  {code(jfile("concurrency/src/main/java/shop/AtomicCounterTest.java", "/** The fix"), "AtomicCounterTest.java", cls="xs")}
</div>
<div style="margin-top:2mm">
  {code("RacyCounterTest — results across all configurations\n  RESULT      SAMPLES     FREQ       EXPECT  DESCRIPTION\n" + RACY_ALL + "\n\nAtomicCounterTest — results across all configurations\n  RESULT      SAMPLES     FREQ       EXPECT  DESCRIPTION\n" + atomic_out, f"real output · jcstress 0.16 · mvn compile exec:exec (-m quick) · GitHub Actions, {nproc} CPUs · {jc_secs} s", kind="plain", cls="xs out")}
</div>
<div class="two top" style="grid-template-columns:1fr 1.1fr;gap:3mm;margin-top:2mm">
  <div>
    <h2 style="margin-top:0">Lost updates by how each actor was compiled</h2>
    {table(["Actor 1", "Actor 2", "Stress", "Lost"], CFG_ROWS, "xs")}
  </div>
  {ticks([f"<b>{lost.group(1)} lost updates</b> in {total_racy:,} runs ({lost.group(2)}%). The rate depended on how each actor was compiled: from {lo[3]:.2f}% to {hi[3]:.2f}%.",
          "<code>ACCEPTABLE_INTERESTING</code> reports an outcome but passes; <code>FORBIDDEN</code> fails the run — so the atomic version guards the fix.",
          "“Stress” runs add C2’s randomizing flags (<code>-XX:+StressLCM</code> and others) to shake out more orderings.",
          "Use it for code that shares memory without locks: custom counters and caches, lazy initialisation, publishing objects to other threads.",
          "For ordinary code, prefer no shared mutable state, or <code>java.util.concurrent</code>; test your logic with normal unit tests.",
          "Run <code>-m quick</code> in CI; <code>default</code> or <code>tough</code> before a release. Tests live in <code>src/main</code>, by jcstress convention."], C4)}
</div>
''', chapter=K4, color=C4)

# ============================================================================
# testing in production
# ============================================================================
syn_ok, syn_down = olog("synthetic.log").strip(), olog("synthetic-redis-down.log").strip()
page("prod", f'''
{sub(K5, "Testing in production: flags and synthetic checks", C5)}
<p class="lede-s">Tests before release can’t see the real network, data and load. Two habits make what happens after a deploy safer: every <b>feature flag</b> is tested both ways before it ships, and a <b>synthetic check</b> — the same code in a test and after every deploy — keeps asking “does it still work?”.</p>
<div class="two top" style="grid-template-columns:1fr 1fr;gap:3mm">
  {code(sx("flags/CheckoutPricingTest.java", "/** Every flag"), "CheckoutPricingTest — both sides of the flag", cls="xs", right=ran("CheckoutPricingTest"))}
  {code(sx("flags/FeatureWiringTest.java", "/** The property"), "FeatureWiringTest — the property reaches the bean", cls="xs", right=ran("FeatureWiringTest"))}
</div>
<div class="two top" style="grid-template-columns:1fr 1fr;gap:3mm;margin-top:2mm">
  {code(sx("synthetic/SyntheticCheck.java", "  public static List<String> run", "    }\n  }", test=False, dedent=2), "SyntheticCheck.java — what a user does", cls="xs")}
  <div>
    {code(sx("synthetic/SyntheticCheckIT.java", "/** The production"), "SyntheticCheckIT — before it ships", cls="xs", right=ran("SyntheticCheckIT"))}
    {code(syn_ok, "real output · CI · against the running jar", kind="out", cls="xs out wrap")}
    {code(syn_down, "real output · same app, Redis stopped", kind="out", cls="xs out wrap")}
  </div>
</div>
<div class="two top" style="grid-template-columns:1fr 1fr;gap:3mm;margin-top:2mm">
  {ticks(["<b>Every flag is two code paths.</b> Test both on every build; a flag that has been on everywhere for a release is deleted, with its tests.",
          "<b>One synthetic check, three places:</b> the test above before the app ships, CI against the packaged jar, and production on a schedule after each deploy.",
          "With Redis down the health endpoint said 503 and the check failed with exit code 1 — that is what pages someone."], C5)}
  {note("<b>Not run here — practice:</b> ship behind a flag that is off; turn it on for a <b>canary</b> (a small share of traffic); compare its error rate and latency with the old version; roll back automatically if they are worse; then turn it on for everyone.", "info")}
</div>
''', chapter=K5, color=C5)
