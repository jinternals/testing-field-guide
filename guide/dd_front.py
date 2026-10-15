"""Cover, contents and method of the deep-dive book. Imported after the chapters so it can quote their results."""
from dd_lib import *
import dd1


LOGS = sorted(p.name for p in DD.iterdir() if p.suffix in (".txt", ".log"))
N_LOGS = len(LOGS) + 1                                   # + the jcstress log from the ops job
N_JAVA = len(list((JAVA / "deepdive/src/main/java/deep").rglob("*.java"))) + 4   # + 4 jcstress tests

# the cover shows two real lines of output
nag = dlog("nagle.txt").splitlines()
wire = "\n".join(html.escape(re.sub(r"\s+p90.*?(?=p99)", "  ", l.split("  max")[0])) + " ms" for l in nag[:2])

CHAPTERS = [
    ("01", "Nagle, delayed ACK and TCP_NODELAY", "Why two small writes can cost 40 ms", CN, [("The mechanism, packet by packet", "nagle"), ("Measured; who sets TCP_NODELAY", "nagle2")]),
    ("02", "Connections", "Handshake, keep-alive, TIME_WAIT, ports", CN, [("A connection’s life", "conn"), ("Measured: reuse and close", "conn2")]),
    ("03", "Timeouts", "Which phase each timeout covers — and the defaults", CN, [("Phases and defaults", "timeouts"), ("Measured: three broken peers", "timeouts2")]),
    ("04", "Pools and Little’s Law", "Sizing a pool from arrival rate and latency", CQ, [("Little’s Law", "pools"), ("Measured: database and CPU pools", "pools2")]),
    ("05", "Measuring latency", "Coordinated omission and percentiles", CQ, [("Open and closed loops", "co"), ("Measured: the same server, three ways", "co2")]),
    ("06", "JIT and benchmarks", "Warm-up, tiers and JMH", CJ, [("Warm-up", "jit"), ("Dead code and constant folding, with JMH", "jit2")]),
    ("07", "GC pauses", "G1 and generational ZGC under one workload", CJ, [("Pauses and the G1 cycle", "gc"), ("Measured: the tail", "gc2")]),
    ("08", "Virtual threads", "Carriers, pinning and compensation", CJ, [("Measured: blocking and pinning", "vt")]),
    ("09", "Containers and CPUs", "What the JVM sizes from cgroup limits", CP, [("What the JVM sees", "box"), ("Sized from the CPU count; throttling", "box2")]),
    ("10", "The Java Memory Model", "Happens-before, measured with jcstress", CJ, [("What another thread may see", "jmm"), ("Visibility and lost updates", "jmm2")]),
    ("11", "Kafka", "Producer batching, consumer fetching, partitions", CQ, [("Producer batching: linger.ms and batch.size", "kafka"), ("Consumer fetching, partitions, max.poll.interval.ms", "kafka2")]),
]
HAS = {p[0] for p in PAGES}

page("dcover", f'''
<div class="cover">
  <svg class="cover-grid" viewBox="0 0 210 297" preserveAspectRatio="none" aria-hidden="true">
    <defs><pattern id="g" width="10" height="10" patternUnits="userSpaceOnUse">
      <path d="M10 0H0V10" fill="none" stroke="rgba(255,255,255,.045)" stroke-width=".25"/></pattern></defs>
    <rect width="210" height="297" fill="url(#g)"/>
  </svg>
  <div class="cover-glow" aria-hidden="true"></div>
  <div class="cover-top"><span class="edition">Deep Dives · October 2026</span><span class="edition">Java 21 · Linux {MACHINE["kernel"].split("-")[0]}</span></div>
  <div class="cover-wire" role="img" aria-label="Real output: two small writes with Nagle on, and with TCP_NODELAY">{wire}</div>
  <div class="cover-title">
    <div class="pre">A companion to the Testing Field Guide</div>
    <h1>Java <em>performance</em><br>deep dives</h1>
    <p>TCP_NODELAY and delayed ACKs, connections and timeouts, pools and Little’s Law, measuring latency, the JIT, GC pauses, virtual threads, containers, the memory model and Kafka — each explained from the specification or the source code, and each measured. Every number in this book is read from a log written in CI.</p>
  </div>
  <div class="cover-foot">
    <div><b>11</b> chapters</div><div><b>{N_JAVA}</b> experiments</div><div><b>{N_LOGS}</b> logs</div><div><b>1</b> runner, named</div>
  </div>
</div>''', cls="p-cover", bm="Cover")

toc_html = ""
for num, title, subt, col, items in CHAPTERS:
    items = [(t, k) for t, k in items if k in HAS]
    if not items:
        continue
    rows = "".join(f'<a class="toc-item" href="#p-{k}"><span>{t}</span><span class="dl"></span><span class="pg">@@{k}@@</span></a>' for t, k in items)
    toc_html += f'''<div class="toc-ch" style="--accent:{col}"><div class="toc-num">{num}</div>
      <div class="toc-body"><a href="#p-{items[0][1]}" class="toc-title">{title}</a><div class="toc-sub">{subt}</div>{rows}</div></div>'''

page("toc", f'''
<div class="toc-wrap">
  <div class="toc-left">
    <div class="kicker">Inside</div>
    <h1 class="toc-h">Contents</h1>
    <a class="toc-item toc-extra" href="#p-method"><span><b>How it was measured</b> — the runner, the experiments, the rules</span><span class="dl"></span><span class="pg">@@method@@</span></a>
    {toc_html}
    <a class="toc-item toc-extra" href="#p-dsources"><span><b>Sources</b> — every specification, source file and document cited</span><span class="dl"></span><span class="pg">@@dsources@@</span></a>
    <a class="toc-item toc-extra" href="#p-dindex"><span><b>Index A–Z</b></span><span class="dl"></span><span class="pg">@@dindex@@</span></a>
    <div class="toc-hint">Facts as of October 2026, for JDK 21 unless a page says otherwise. Every entry, page reference and footer link is clickable.</div>
  </div>
  <aside class="toc-right">
    <div class="side-card">
      <div class="side-h">Colour language</div>
      <p class="small"><b style="color:{CN}">Network</b> · <b style="color:{CQ}">queues and measurement</b> · <b style="color:{CJ}">the JVM</b> · <b style="color:{CP}">the platform</b></p>
    </div>
    <div class="side-card">
      <div class="side-h">Read with</div>
      <p class="small"><b>Testing Java applications — Field Guide</b> (Testing-Field-Guide.pdf, same repository). Its performance chapter introduces several of these topics in a page each; this book is the long version.</p>
    </div>
    <div class="side-card">
      <div class="side-h">On every page</div>
      <p class="small">The mechanism, from the specification or the source. The experiment’s code, as it ran. The real output. What to do about it. The sources, at the foot.</p>
    </div>
  </aside>
</div>''', chapter="Contents", bm="Contents")

MACH_ROWS = [("Runner", "GitHub Actions, <code>ubuntu-latest</code>"), ("CPU", f"{MACHINE['cpus']} CPUs" + (f" · {MACHINE['cpu']}" if MACHINE["cpu"] != "not recorded" else "")),
             ("Kernel", f"Linux {MACHINE['kernel']}, <code>CONFIG_HZ={MACHINE['hz']}</code>"), ("JDK", f"OpenJDK {MACHINE['java']} (Temurin)")] + \
            [(f"<code>{k}</code>", v) for k, v in MACHINE["sysctl"].items()]
EXPS = [
    ("1", "tcp/Nagle.java + tcpdump", "nagle.txt, nagle-trace.txt"), ("2", "tcp/Connections.java", "connections.txt"),
    ("3", "tcp/Timeouts.java, SynRetries.java + iptables", "timeouts.txt, syn*.txt"), ("4", "pool/PoolSize.java, CpuPool.java", "pool.txt, cpupool.txt"),
    ("5", "latency/CoordinatedOmission.java", "co.txt"), ("6", "jit/WarmUp.java, DeadCodeBench.java (JMH)", "warmup*.txt, jmh.txt, jit-flags.txt"),
    ("7", "gc/GcLatency.java, G1 and ZGC", "gc-*.txt, gc-*.log"), ("8", "vt/VirtualThreads.java", "vt.txt"),
    ("9", "box/Resources.java, Throttle.java in Docker", "containers.txt, throttle.txt"), ("10", "jmm/StaleFlag.java + 4 jcstress tests", "staleflag.txt, jcstress.log"),
    ("11", "kafka/KafkaLatency.java, one broker in Docker", "kafka-*.txt"),
]
page("method", f'''
{sub("Before you start", "How it was measured", "#0F172A")}
<p class="lede-s">Each page explains a mechanism and then measures it. Explanations cite a specification, the source code of the version discussed, or the vendor’s documentation; measurements come from programs in this repository, run in CI.</p>
<div class="two top" style="grid-template-columns:1fr 1fr;gap:3mm">
  <div class="mech" style="--accent:#0F172A">
    <h3>Sources for explanations</h3>
    <p>The specification (RFC 9293 for TCP, the Java Language Specification for the memory model, JEPs for JDK features), the <b>source code of the version discussed</b> — OpenJDK 21, Linux 6.17, the libraries — or the vendor’s documentation. Each page lists what it used at its foot; the full list is at the back.</p>
  </div>
  <div class="mech" style="--accent:#0F172A">
    <h3>Measurements</h3>
    <p>Each chapter has a small program in <code>deepdive/</code>. The <code>deepdive</code> CI job runs all of them on every push (<code>deepdive/run.sh</code>) and publishes the logs to the <code>ci-logs-deepdive</code> branch. This book is built from those logs: every measured number on a page is read from them at build time.</p>
  </div>
</div>
<div class="two top" style="grid-template-columns:1fr 1.15fr;gap:3mm;margin-top:3mm">
  <div>
    <h2 style="margin-top:0">The machine</h2>
    {table(["", ""], MACH_ROWS, "xs")}
    <p class="small muted" style="margin-top:1mm">From <code>machine.txt</code>, written by the same run.</p>
  </div>
  <div>
    <h2 style="margin-top:0">The experiments</h2>
    {table(["Ch.", "Program", "Log"], EXPS, "xs")}
  </div>
</div>
<h2>One number, traced</h2>
{table(["Step", "Evidence"], [
    ("The claim (chapter 1)", f"Two small writes with Nagle on: median <b>{float(dd1.ROWS[0][1]):.2f} ms</b> per request"),
    ("The log line", f"<code>{html.escape(nag[0].split('  p90')[0])}</code> — <code>nagle.txt</code>, written by <code>Nagle.java</code> in CI"),
    ("The packets", f"<code>nagle-trace.txt</code>: the server’s ACK of the first 50-byte half left {dd1.WAIT_MS:.2f} ms after it; the second half was held until then — tcpdump on loopback"),
    ("Why 40 ms", f"Linux <code>include/net/tcp.h</code>: <code>TCP_DELACK_MIN = HZ/25</code>; with <code>CONFIG_HZ={MACHINE['hz']}</code> that is {MACHINE['hz'] // 25} ms"),
    ("Why it waits at all", "RFC 9293 §3.7.4 (Nagle: hold small segments while data is unacknowledged) and §3.8.6.3 (delayed ACK)"),
], "xs")}
<div class="two top" style="grid-template-columns:1fr 1fr;gap:3mm;margin-top:3mm">
  {ticks(["<b>The text follows the data.</b> Where a sentence interprets a result — “slower”, “removed by the JIT”, “not caused by a GC pause” — it is computed from the log, and changes if the result changes.",
          "<b>Conclusions are checked.</b> <code>guide/claims_deep.py</code> re-reads the logs and fails the build if a conclusion this book states no longer holds."])}
  {ticks(["<b>One machine.</b> The numbers are from one CI runner and depend on its CPU, kernel and JDK. To rerun on another machine: <code>bash deepdive/run.sh</code> (Linux, JDK 21, Maven, Docker; <code>sudo</code> for tcpdump and iptables).",
          "<b>Versions matter.</b> Statements are for JDK 21 and the library versions named; where a later JDK changed the behaviour (JEP 474, 490, 491) the page says so."])}
</div>
''', chapter="How it was measured", color="#0F172A", bm="How it was measured")
