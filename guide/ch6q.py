from lib import *
import csv, collections

C = CH["6"]
_foot = re.search(r"<tfoot>.*?</tfoot>", (JAVA / "coverage/html-unit/shop/index.html").read_text()).group(0)
UNIT_INSTR, UNIT_BR = re.findall(r'class="ctr2">(\d+)%', _foot)[:2]

# ----------------------------------------------------------------------------
# data from the real PIT and JaCoCo runs
# ----------------------------------------------------------------------------
def pit_rows(path):
    rows = list(csv.reader(open(JAVA / path)))
    by = collections.OrderedDict()
    for r in rows:
        m = r[2].rsplit(".", 1)[1].replace("Mutator", "")
        d = by.setdefault(m, collections.Counter())
        d[r[5]] += 1
    return rows, by

before_rows, before = pit_rows("pit-mutations-before.csv")
after_rows, after = pit_rows("pit-reports/mutations.csv")
MUTNAME = {"ConditionalsBoundary": "CONDITIONALS_BOUNDARY", "NegateConditionals": "NEGATE_CONDITIONALS", "Math": "MATH",
           "VoidMethodCall": "VOID_METHOD_CALLS", "NullReturnVals": "NULL_RETURNS", "EmptyObjectReturnVals": "EMPTY_RETURNS",
           "PrimitiveReturns": "PRIMITIVE_RETURNS", "BooleanTrueReturnVals": "TRUE_RETURNS", "BooleanFalseReturnVals": "FALSE_RETURNS",
           "Increments": "INCREMENTS", "InvertNegs": "INVERT_NEGS"}
def mt_table():
    rows = []
    for m in sorted(set(before) | set(after), key=lambda k: -sum(before.get(k, {}).values())):
        b, a = before.get(m, collections.Counter()), after.get(m, collections.Counter())
        n = sum(b.values())
        rows.append(f'<tr><td class="hn" style="color:{C}">{MUTNAME.get(m, m)}</td><td class="c">{n}</td><td class="c">{b["KILLED"]}</td>'
                    f'<td class="c">{b["TIMED_OUT"]}</td><td class="c">{"<b class=part>" + str(b["SURVIVED"]) + "</b>" if b["SURVIVED"] else 0}</td>'
                    f'<td class="c">{a["SURVIVED"]}</td></tr>')
    return "".join(rows)

import xml.etree.ElementTree as ET
_mx = {(m.findtext("mutatedClass").replace("shop.", ""), m.findtext("lineNumber"), m.findtext("description")): m
       for m in ET.parse(JAVA / "pit-reports/mutations.xml").getroot()}
PICK = [("DiscountPolicy", "7", "changed conditional boundary"), ("Money", "19", "Replaced integer subtraction with addition"),
        ("OrderService", "32", "removed call to shop/EmailSender::send"), ("PasswordPolicy", "16", "replaced return value with Collections.emptyList for shop/PasswordPolicy::problems"),
        ("InMemoryOrderRepository", "15", "replaced return value with Optional.empty for shop/InMemoryOrderRepository::findById"),
        ("OrderApi", "20", "removed call to com/sun/net/httpserver/HttpServer::start"), ("OrderApi", "24", "removed call to com/sun/net/httpserver/HttpServer::stop")]
SAMPLE = []
for k in PICK:
    m = _mx[k]
    d = re.sub(r" for shop/\w+::\w+", "", k[2]).replace("com/sun/net/httpserver/", "").replace("shop/", "")
    stt = m.get("status") + (" (run 2)" if k == ("OrderApi", "24", "removed call to com/sun/net/httpserver/HttpServer::stop") else "")
    SAMPLE.append((f"{k[0]} · {k[1]}", d, m.get("numberOfTestsRun"), f"<b class='{'yes' if m.get('status') in ('KILLED','TIMED_OUT') else 'no'}'>{stt}</b>"))

PIT_SECS = re.search(r"> Total\s*:\s*(\d+) seconds", capture("pit-output.txt")).group(1)
surv = [r for r in before_rows if r[5] == "SURVIVED"][0]
tot_b = len(before_rows); det_b = sum(1 for r in before_rows if r[5] in ("KILLED", "TIMED_OUT"))
tot_a = len(after_rows); det_a = sum(1 for r in after_rows if r[5] in ("KILLED", "TIMED_OUT"))
stronger = re.search(r"Generated (\d+) mutations Killed (\d+) \((\d+)%\)", capture("pit-output-stronger.txt")).groups()
stats_b = re.search(r">> Line Coverage.*?Test strength \d+%", capture("pit-output-before.txt"), re.S).group(0)

PITPOM = """<plugin>
  <groupId>org.pitest</groupId>
  <artifactId>pitest-maven</artifactId>
  <version>1.30.0</version>
  <dependencies>
    <dependency>  <!-- runs JUnit 5/6 tests -->
      <groupId>org.pitest</groupId>
      <artifactId>pitest-junit5-plugin</artifactId>
      <version>1.2.3</version>
    </dependency>
  </dependencies>
  <configuration>
    <targetClasses><param>shop.*</param></targetClasses>
    <targetTests><param>shop.*Test</param></targetTests>
    <mutators><mutator>DEFAULTS</mutator></mutators>
    <mutationThreshold>90</mutationThreshold>  <!-- fail below 90% -->
    <coverageThreshold>85</coverageThreshold>
    <withHistory>true</withHistory>            <!-- incremental -->
    <threads>4</threads>
    <outputFormats><param>HTML</param><param>XML</param></outputFormats>
  </configuration>
</plugin>"""

STATUS = [("KILLED", "a test failed — the bug was caught", "yes"), ("TIMED_OUT", "mutant made the code hang (e.g. a removed <code>start()</code>); counted as detected", "yes"),
          ("SURVIVED", "every covering test still passed — a gap in your assertions", "no"), ("NO_COVERAGE", "no test even runs this line", "no"),
          ("NON_VIABLE", "the mutated bytecode was invalid", "—"), ("MEMORY_ERROR / RUN_ERROR", "the test JVM crashed", "yes")]
st = "".join(f'<tr><td class="hn">{a}</td><td>{b}</td><td class="c {"yes" if c == "yes" else ("no" if c == "no" else "")}">{c}</td></tr>' for a, b, c in STATUS)

page("pit", f'''
{sub("06 · Quality &amp; process", "Mutation testing with PIT — for real", C)}
<p class="lede-s">We ran <b>PIT 1.30.0</b> with <b>pitest-junit5-plugin 1.2.3</b> on the shop example: every production class mutated with the DEFAULTS group, every unit and integration test run against each mutant. Below is what it found and how we fixed it.</p>
<div class="two top" style="grid-template-columns:1fr 1.1fr;gap:3.5mm">
  <div>
    <h2 style="margin-top:0">Run 1 — what PIT reported</h2>
    {code(stats_b.replace(">> ", ""), "real PIT summary · run 1", kind="plain", cls="xs out wrap", right=f"{det_b}/{tot_b} detected")}
    <p class="small" style="margin-top:1.6mm">“22 tests examined” counts test <em>classes</em>; PIT ran each mutant against only the tests that cover its line. <b>Run 2</b>, after the fix: {det_a}/{tot_a} detected — <b>100%</b>. With the larger STRONGER group: {stronger[1]}/{stronger[0]} ({stronger[2]}%).</p>
    {note("Before writing a test for a survivor, ask whether the behaviour matters. Some mutants are <b>equivalent</b> — the change can’t alter any observable result — and no test can kill them. Accept those rather than writing a meaningless test.", "info")}
  </div>
  <div>
    <h2 style="margin-top:0">The survivor</h2>
    <p class="small"><b>{surv[1].replace("shop.", "")}.{surv[3]}()</b>, line {surv[4]}: PIT deleted the call <code>server.stop(0)</code> and <b>all {N_TESTS - 1} tests still passed</b>. Nothing checked that stopping the API actually frees its port — a resource leak would ship unnoticed.</p>
    {code(jfile("OrderApiLifecycleTest.java", "/**"), "the test we added to kill it", cls="xs", right="✔ passes")}
  </div>
</div>
<h2>Results by mutator</h2>
<table class="tbl xs"><thead><tr><th>Mutator</th><th class="c">made</th><th class="c">killed</th><th class="c">timed out</th><th class="c">survived · run 1</th><th class="c">survived · run 2</th></tr></thead><tbody>{mt_table()}</tbody></table>
<h2>What PIT actually changed — a sample of the {tot_a} mutants</h2>
{table(["Class · line", "PIT’s description", "Tests run", "Result"], SAMPLE, "xs")}
<p class="small muted" style="margin-top:1.2mm">Note what is <em>not</em> there: <code>payments.charge(…)</code> returns a value, so the DEFAULTS group never removes it — only void calls are removed. Larger groups (STRONGER, ALL) add mutators for those cases.</p>
''', chapter="06 · Quality &amp; process", color=C)

page("pitci", f'''
{sub("06 · Quality &amp; process", "PIT in your build and CI", C)}
<div class="two top" style="grid-template-columns:1.35fr 1fr;gap:3.5mm">
  {code(PITPOM, "pom.xml — the same settings as our run, as Maven config", kind="xml", cls="xs")}
  <div>
    <h2 style="margin-top:0">Run it</h2>
    {table(["Command", "Does"], [
        ("<code>mvn test-compile pitest:mutationCoverage</code>", "full analysis; HTML report in <code>target/pit-reports</code>"),
        ("<code>-DtargetClasses=shop.pricing.*</code>", "narrow the run to one package"),
        ("<code>-DwithHistory</code>", "reuse the last run’s results (incremental)"),
        ("<code>-Dmutators=STRONGER</code>", "more mutators; slower, finds more gaps")], "xs")}
    <h2>Making it fast enough for CI</h2>
    {ticks(["<b>Incremental:</b> with history on, only changed code and tests are re-analysed.",
            "<b>Pull requests:</b> PIT 1.30 has no git-diff goal. Narrow <code>targetClasses</code> to the changed module (or use Arcmutate’s commercial add-ons); run everything nightly.",
            "<b>Target it:</b> modules with money, permissions and business rules first.",
            f"Our run: {PIT_SECS} s for {tot_a} mutants on 2 CPUs, because PIT re-runs only the tests covering each mutant."], C)}
  </div>
</div>
<h2>Reading a mutant’s status</h2>
<table class="tbl xs"><thead><tr><th>Status</th><th>Meaning</th><th class="c">Detected?</th></tr></thead><tbody>{st}</tbody></table>
<h2>Unit or integration tests?</h2>
<div class="two top">
  <p class="small">PIT runs whatever tests you point it at. Ours included the HTTP integration tests, which is how it could detect mutants in <code>OrderApi</code> at all — no unit test touches that class. The cost: mutants that broke <code>start()</code> or the handler made tests hang until PIT’s timeout (the {sum(1 for r in after_rows if r[5] == "TIMED_OUT")} <b>TIMED_OUT</b> results).</p>
  <p class="small"><b>A practical split:</b> run PIT on every pull request with unit tests only (fast, precise), and nightly with integration tests included for the modules where wiring matters. Keep those tests quick — random ports, fakes, no sleeps.</p>
</div>
<h2>A workflow for survivors</h2>
<div class="four">
  <div class="card"><b class="h">1 · Read it</b>Open the HTML report: the line, the change PIT made, and which tests covered it.</div>
  <div class="card"><b class="h">2 · Does it matter?</b>Would a user, caller or log notice the change? If not, it may be equivalent or the code may be dead.</div>
  <div class="card"><b class="h">3 · Test or delete</b>Write the assertion that fails on the mutant — or delete code that nothing depends on.</div>
  <div class="card"><b class="h">4 · Gate the trend</b>Fail the build when the score drops below the threshold, so it can’t quietly erode.</div>
</div>
''', chapter="06 · Quality &amp; process", color=C)

# ============================================================================
# JaCoCo for unit + integration
# ============================================================================
covtxt = capture("coverage-output.txt")
def cov_block(name):
    blk = covtxt.split(f"== {name}\n")[1].split("\n\n")[0].strip()
    rows = {}
    for l in blk.split("\n")[1:]:
        name = l.split()[0]
        cells = re.findall(r"\d+/\d+\s+\d+%|n/a", l)
        rows[name] = [name] + cells
    return rows
U, I, M = cov_block("UNIT"), cov_block("INTEGRATION"), cov_block("MERGED")
def pct(cell):
    m = re.search(r"(\d+)%", cell)
    return (m.group(1) + "%") if m else "n/a"
cov_rows = ""
for cls in ["OrderService", "DiscountPolicy", "Money", "PasswordPolicy", "Item", "OrderApi", "TOTAL"]:
    u, i_, m = U[cls], I[cls], M[cls]
    style = ' style="font-weight:700"' if cls == "TOTAL" else ""
    cov_rows += (f'<tr{style}><td class="nm">{cls}</td><td class="c">{pct(u[1])}</td><td class="c">{pct(i_[1])}</td><td class="c">{pct(m[1])}</td>'
                 f'<td class="c">{pct(u[2])}</td><td class="c">{pct(i_[2])}</td><td class="c">{pct(m[2])}</td></tr>')
counts = re.findall(r"\[\s+(\d+) tests successful", covtxt)

JACOCOPOM = """<plugin>
  <groupId>org.jacoco</groupId>
  <artifactId>jacoco-maven-plugin</artifactId>
  <version>0.8.15</version>
  <configuration>  <!-- report and check read the merged file -->
    <dataFile>${project.build.directory}/jacoco-merged.exec</dataFile>
  </configuration>
  <executions>
    <execution><id>unit</id>      <!-- for Surefire -->
      <goals><goal>prepare-agent</goal></goals></execution>
    <execution><id>it</id>        <!-- for Failsafe -->
      <goals><goal>prepare-agent-integration</goal></goals></execution>
    <execution><id>merge</id><phase>verify</phase>
      <goals><goal>merge</goal></goals>
      <configuration>
        <fileSets><fileSet>
          <directory>${project.build.directory}</directory>
          <includes><include>jacoco.exec</include>
                    <include>jacoco-it.exec</include></includes>
        </fileSet></fileSets>
        <destFile>${project.build.directory}/jacoco-merged.exec</destFile>
      </configuration></execution>
    <execution><id>report</id><phase>verify</phase>
      <goals><goal>report</goal></goals></execution>
    <execution><id>gate</id><phase>verify</phase>
      <goals><goal>check</goal></goals>
      <configuration>
        <rules><rule><element>BUNDLE</element><limits><limit>
          <counter>BRANCH</counter><value>COVEREDRATIO</value>
          <minimum>0.80</minimum>
        </limit></limits></rule></rules>
      </configuration></execution>
  </executions>
</plugin>"""

page("itcov", f'''
{sub("06 · Quality &amp; process", "Coverage for unit <em>and</em> integration tests", C)}
<p class="lede-s">By default most builds measure coverage for unit tests only, so code exercised only by integration tests looks untested. We ran the <b>JaCoCo 0.8.15</b> agent twice — once for the {counts[0]} unit tests, once for the {counts[1]} API integration tests — and merged the results (real numbers from <code>coverage.sh</code>; classes without branches left out).</p>
<div>
  <div>
    <table class="tbl xs"><thead><tr><th>Class</th><th class="c">unit<br>lines</th><th class="c">IT<br>lines</th><th class="c">merged<br>lines</th><th class="c">unit<br>branches</th><th class="c">IT<br>branches</th><th class="c">merged<br>branches</th></tr></thead><tbody>{cov_rows}</tbody></table>
  </div>
  <div class="two top" style="gap:3.5mm;margin-top:2mm;grid-template-columns:1.45fr 1fr">
    {ticks([f"<b>Unit tests alone: {pct(U['TOTAL'][1])} of lines</b> — <code>OrderApi</code> looks completely untested.",
            f"<b>Integration tests alone: {pct(I['TOTAL'][1])}</b> — they never touch the pricing or password rules.",
            "<b>Merged: 100% of lines and branches.</b> Each level covers what the other can’t.",
            "Coverage is a floor, not a goal: PIT (p.@@pit@@) is what showed the tests also <em>check</em> what they run."], C)}
  <div>
    <figure><img src="img/jacoco-unit-index-crop.png" alt="JaCoCo HTML report for unit tests only: OrderApi at 0 percent instruction and branch coverage, every other class at 100 percent, total {UNIT_INSTR} percent of instructions and {UNIT_BR} percent of branches." style="width:100%;border:1px solid var(--line);border-radius:5px;display:block">
    <figcaption class="small muted" style="margin:1mm 0 2mm">JaCoCo’s own HTML report, unit tests only</figcaption></figure>
    <figure><img src="img/jacoco-unit-orderapi-crop.png" alt="JaCoCo source view of OrderApi.java from the unit-test run: the request-handling lines are highlighted red, meaning never executed by unit tests." style="width:100%;border:1px solid var(--line);border-radius:5px;display:block">
    <figcaption class="small muted" style="margin-top:1mm">Red lines: never executed by unit tests — only the HTTP integration tests reach them</figcaption></figure>
  </div>
  </div>
</div>
<div class="two top" style="grid-template-columns:1.5fr 1fr;gap:3.5mm;margin-top:2.6mm">
  {code(JACOCOPOM, "pom.xml — unit + IT coverage, merged, with a gate", kind="xml", cls="xs")}
  <div>
    <h2 style="margin-top:0">How the pieces fit</h2>
    {ticks(["<b>prepare-agent</b> sets <code>argLine</code> for Surefire; <b>prepare-agent-integration</b> does the same for Failsafe, writing <code>jacoco-it.exec</code>.",
            "<b>merge</b> combines the <code>.exec</code> files; <b>report</b> turns them into HTML, XML and CSV.",
            "<b>check</b> fails the build when a rule isn’t met — here 80% of branches.",
            "Multi-module builds: <b>report-aggregate</b> in a separate reporting module.",
            "Other agents in <code>argLine</code> (like the Mockito agent on p.@@mockpit@@) must keep JaCoCo’s value: write <code>@{argLine} -javaagent:…</code>."], C)}
    {note("Gate coverage on <b>new or changed code</b> (SonarQube’s “new code” quality gate, or a diff-coverage tool) rather than the whole code base. Old, untested code then can’t block every merge, but nothing new arrives untested.", "rule")}
  </div>
</div>
''', chapter="06 · Quality &amp; process", color=C)

