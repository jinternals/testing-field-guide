"""Chapter 4 · pools and Little's Law. Chapter 5 · measuring latency: coordinated omission."""
from dd_lib import *

# ============================================================================
# 4 · pools
# ============================================================================
K4 = chap(4, "Pools and Little’s Law")
P = []
for m in re.finditer(r"^\s*(\d+)\s+(\d+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+) ms\s+([\d.]+)\s+([\d.]+)$", dlog("pool.txt"), re.M):
    P.append(tuple(m.groups()))
CPU = []
cpu_txt = dlog("cpupool.txt")
for m in re.finditer(r"^\s*(\d+)\s+(\d+)\s+(\d+)\s+([\d.]+)\s+([\d.]+)$", cpu_txt, re.M):
    CPU.append(tuple(m.groups()))
CPUS = int(re.search(r"availableProcessors: (\d+)", cpu_txt).group(1))
best = max(int(r[1]) for r in P)
service_ms = 4 / best * 1000                       # 4 slots / throughput
lw = [abs(float(r[6]) - float(r[5])) / float(r[5]) for r in P]


def pool_diagram():
    b = [ARROW.format(id="pa", c="#475569")]
    b.append('<text x="6" y="12" font-size="7.6" font-weight="700" fill="#0F172A">64 callers</text>')
    for i in range(8):
        b.append(f'<circle cx="{14 + (i % 4) * 12}" cy="{26 + (i // 4) * 12}" r="4" fill="#CBD5E1"/>')
    b.append('<text x="6" y="60" font-size="6.6" fill="#5B6474">… waiting for a connection</text>')
    b.append('<line x1="70" y1="32" x2="116" y2="32" stroke="#475569" marker-end="url(#pa)"/>')
    b.append('<rect x="120" y="8" width="130" height="48" rx="5" fill="#FFFBEB" stroke="#B45309"/>')
    b.append('<text x="185" y="22" text-anchor="middle" font-size="7.6" font-weight="700" fill="#92400E">app pool: P connections</text>')
    b.append('<text x="185" y="35" text-anchor="middle" font-size="6.8" fill="#78350F">P ≤ 4: callers queue here</text>')
    b.append('<text x="185" y="46" text-anchor="middle" font-size="6.8" fill="#78350F">P &gt; 4: the queue moves on</text>')
    b.append('<line x1="250" y1="32" x2="296" y2="32" stroke="#475569" marker-end="url(#pa)"/>')
    b.append('<rect x="300" y="8" width="150" height="48" rx="5" fill="#EFF6FF" stroke="#1D4ED8"/>')
    b.append('<text x="375" y="22" text-anchor="middle" font-size="7.6" font-weight="700" fill="#1D4ED8">database: 4 at a time</text>')
    for i in range(4):
        b.append(f'<rect x="{320 + i * 28}" y="30" width="22" height="16" rx="3" fill="#fff" stroke="#93C5FD"/>')
        b.append(f'<text x="{331 + i * 28}" y="41" text-anchor="middle" font-size="6.2" fill="#1E3A8A">10 ms</text>')
    return svg("".join(b), 456, 64, "64 callers wait for one of P pooled connections; each query then waits for one of the database's 4 execution slots and takes 10 ms. With P up to 4 the queue is in the pool; with P above 4 the extra callers queue inside the database instead.")


page("pools", f'''
{sub(K4, "Throughput, latency and the size of a pool", CQ)}
<p class="lede-s">Every pool is a queue in front of a resource. Little’s Law ties the three numbers you can measure together, for any stable system, whatever the pattern of arrivals: <b>L = λ·W</b> — the average number of requests inside equals the rate they leave times the average time each spends inside.</p>
<div class="two top" style="grid-template-columns:1fr 1fr;gap:3mm">
  <div class="mech" style="--accent:{CQ}">
    <h3>Three consequences</h3>
    <p><b>1. A pool caps throughput:</b> with C connections each busy for S seconds, at most C/S requests per second leave. Our database (4 slots, ~{service_ms:.1f} ms per query as measured) tops out near {best} per second.</p>
    <p style="margin-top:1mm"><b>2. Past the cap, more callers only add waiting:</b> 64 callers in a system that serves {best}/s means W = 64 / {best} ≈ {64 / best * 1000:.0f} ms each, however the queue is arranged.</p>
    <p style="margin-top:1mm"><b>3. A bigger pool moves the queue</b> — from the pool into the database, where waiting is more expensive: memory, locks, context switches.</p>
  </div>
  <div class="mech" style="--accent:{CQ}">
    <h3>How big, then?</h3>
    <p class="rfc">“connections = ((core_count * 2) + effective_spindle_count)” — a starting point from the PostgreSQL project, quoted by HikariCP’s “About Pool Sizing”</p>
    <p>The reasoning: a CPU core runs one thread at a time; beyond that, more threads add context switching, not throughput — unless they wait on disk or network. Treat the formula as a first guess, then measure throughput and latency as you change it, as below.</p>
  </div>
</div>
<h2>The experiment</h2>
{pool_diagram()}
{code(dsrc("pool/PoolSize.java", "      callers[i] = Thread.ofVirtual()", "      });", dedent=6), "PoolSize.java — one caller’s loop", cls="xs")}
<h2>Using it: three questions, answered from the measured numbers</h2>
{table(["Question", "Little’s Law", "With this chapter’s database"], [
    ("How many connections are busy at a target rate?", "L = λ · S  (S = time a query holds a connection)", f"{best // 2} queries/s × {service_ms:.1f} ms = <b>{best // 2 * service_ms / 1000:.1f}</b> connections busy on average — a pool of 4 has headroom"),
    ("What would a smaller pool deliver?", "λ<sub>max</sub> = C / S", f"C = 1: <b>{1 / service_ms * 1000:.0f}/s</b>, C = 2: <b>{2 / service_ms * 1000:.0f}/s</b> predicted; measured {next(r for r in P if r[0] == '1')[1]}/s and {next(r for r in P if r[0] == '2')[1]}/s"),
    ("How long will callers wait once it is saturated?", "W = L / λ<sub>max</sub>", f"64 callers / {best}/s = <b>{64 / best * 1000:.0f} ms</b>; measured mean with pool 4: {next(r for r in P if r[0] == '4')[2]} ms"),
], "xs")}
<p class="small" style="margin-top:1mm">S is derived from the saturated rows only (4 slots ÷ {best} queries/s); the smaller pools are then a prediction, checked against their own rows. The law needs averages over a stable period; it says nothing about the tail — p99 needs the distribution (chapter 5).</p>
{src("J. D. C. Little, “A Proof for the Queuing Formula: L = λW”, Operations Research 9(3), 1961", "HikariCP wiki, “About Pool Sizing”", "deepdive/src/…/pool/PoolSize.java")}
''', chapter=K4, color=CQ, bm="04 · Pools and Little’s Law")

POOL_CHARTS = chart([("queries / s", "#B45309", [float(r[1]) for r in P])], [r[0] for r in P], "Throughput by pool size", "queries per second", w=250, h=130, xlabel="pool size") \
    + chart([("time in system (W)", "#1D4ED8", [float(r[2]) for r in P]), ("of which waiting inside the DB", "#B91C1C", [max(float(r[4]), 0.01) for r in P])],
            [r[0] for r in P], "Where the time goes", "ms", w=250, h=130, xlabel="pool size")
CPU_CHARTS = chart([("tasks / s", "#B45309", [float(r[2]) for r in CPU])], [r[0] for r in CPU], "Throughput by threads", "tasks per second", w=250, h=130, xlabel="threads") \
    + chart([("task p50", "#1D4ED8", [float(r[3]) for r in CPU]), ("task p99", "#B91C1C", [float(r[4]) for r in CPU])], [r[0] for r in CPU], "Each task’s own time", "ms", w=250, h=130, xlabel="threads")
POOL_ROWS = [(r[0], r[1], r[2], r[3], f"{float(r[4]):.1f} ms", r[5], r[6]) for r in P]
CPU_ROWS = [(r[0], r[1], r[2], r[3], r[4]) for r in CPU]
c1 = next(r for r in CPU if int(r[0]) == 1)
cn = next(r for r in CPU if int(r[0]) == CPUS)
cbig = max(CPU, key=lambda r: int(r[0]))
page("pools2", f'''
{sub(K4, "Measured: six pool sizes, then real CPUs", CQ)}
<p class="lede-s">Each row ran for 3 s with 64 callers. λ, W and L were measured independently over the steady window 0.5–2.5 s: λ from completions, W from each request’s time in the system, L by counting callers inside every millisecond.</p>
<div class="two top" style="grid-template-columns:1.25fr 1fr;gap:3mm">
  <div>
    {table(["Pool", "Queries/s (λ)", "Mean ms (W)", "p99 ms", "Wait in DB", "L", "λ·W"], POOL_ROWS, "xs")}
    <p class="small muted" style="margin-top:1mm">Real output · {RUNNER}</p>
  </div>
  {ticks([f"<b>Little’s Law held in every row:</b> λ·W was within {max(lw) * 100:.1f}% of the measured L.",
          f"<b>Throughput stopped at the database:</b> from pool size 4 up, {min(int(r[1]) for r in P if int(r[0]) >= 4)}–{max(int(r[1]) for r in P if int(r[0]) >= 4)} queries/s.",
          f"<b>Bigger pools moved the queue into the database:</b> the wait inside it grew from 0 to {float(P[-1][4]):.0f} ms per query while the total time stayed the same.",
          "<b>Too small a pool</b> is visible the same way: at 1 and 2 connections the database sat idle while callers queued."], CQ)}
</div>
<div class="two" style="grid-template-columns:1fr 1fr;gap:3mm;margin-top:1.5mm">{POOL_CHARTS}</div>
<h2>The same question with a real resource: {CPUS} CPU cores</h2>
<div class="two top" style="grid-template-columns:1.25fr 1fr;gap:3mm">
  <div>
    {table(["Threads", "Total ms", "Tasks/s", "Task p50 ms", "Task p99 ms"], CPU_ROWS, "xs")}
    <p class="small muted" style="margin-top:1mm">400 tasks of about 5 ms of arithmetic each · real output · {RUNNER}</p>
  </div>
  {ticks([f"<b>Throughput is capped by cores:</b> {c1[2]} tasks/s on 1 thread, {cn[2]} on {CPUS}, {cbig[2]} on {cbig[0]} — no gain past the core count.",
          f"<b>Each task got slower</b> as threads were added: p50 {c1[3]} ms alone, {cbig[3]} ms with {cbig[0]} threads, because the cores were shared. A timeout set from a single-thread test would fail under load.",
          "<b>For I/O-bound work</b> the right size is set by the resource behind it (the database’s slots), for CPU-bound work by the cores. Measure both throughput and per-task latency when you change it."], CQ)}
</div>
<div class="two" style="grid-template-columns:1fr 1fr;gap:3mm;margin-top:1.5mm">{CPU_CHARTS}</div>
{src("results: deepdive/logs/pool.txt, cpupool.txt", "deepdive/src/…/pool/PoolSize.java, CpuPool.java")}
''', chapter=K4, color=CQ)

# ============================================================================
# 5 · coordinated omission
# ============================================================================
K5 = chap(5, "Measuring latency")
CO = {}
for line in dlog("co.txt").splitlines():
    m = re.match(r"(.+?)\s+(\d+) samples(.*)$", line)
    if m:
        pct = dict(re.findall(r"(p[\d.]+|max)\s+([\d.]+)", m.group(3)))
        CO[m.group(1).strip()] = (m.group(2), pct)
naive, corr, openl = CO["closed loop (naive)"], CO["closed loop, corrected"], CO["open loop, from due time"]
_cs = (JAVA / "deepdive/src/main/java/deep/latency/CoordinatedOmission.java").read_text()
_c = lambda n: int(re.search(rf"{n} = ([\d_]+)L", _cs).group(1).replace("_", ""))
CO_INT_MS, CO_RUN_S = _c("INTERVAL") / 1e6, _c("RUN_NS") / 1e9
CO_STALL_MS = (_c("STALL_TO") - _c("STALL_FROM")) / 1e6
CO_N, CO_DUE = int(CO_RUN_S * 1000 / CO_INT_MS), int(CO_STALL_MS / CO_INT_MS)


def co_diagram():
    b = []
    b.append('<text x="6" y="12" font-size="7.6" font-weight="700" fill="#0F172A">closed loop: next request only after the last one returns</text>')
    for i in range(30):
        x = 10 + i * 14 if i < 14 else 10 + 13 * 14 + 150 + (i - 13) * 14
        if x > 600:
            break
        b.append(f'<rect x="{x}" y="18" width="9" height="10" rx="2" fill="#93C5FD"/>')
    b.append('<rect x="206" y="18" width="150" height="10" rx="2" fill="#B91C1C"/>')
    b.append('<text x="281" y="40" text-anchor="middle" font-size="6.8" fill="#B91C1C">1 slow request recorded; ~500 never sent</text>')
    b.append('<text x="6" y="60" font-size="7.6" font-weight="700" fill="#0F172A">open loop: requests are due every 2 ms, stall or not</text>')
    for i in range(43):
        x = 10 + i * 14
        stalled = 206 <= x <= 356
        b.append(f'<rect x="{x}" y="66" width="9" height="10" rx="2" fill="{"#FCA5A5" if stalled else "#93C5FD"}"/>')
    b.append('<text x="281" y="88" text-anchor="middle" font-size="6.8" fill="#B91C1C">every request due during the stall waits — and is recorded</text>')
    b.append('<text x="281" y="104" text-anchor="middle" font-size="6.8" fill="#5B6474">(schematic: one box per request; the real run has 5,000)</text>')
    return svg("".join(b), 620, 108, "Schematic: a closed-loop client sends one request during a stall and records one slow sample, while the requests it would have sent are never sent. An open-loop client keeps its schedule; every request due during the stall is delayed and recorded.")


page("co", f'''
{sub(K5, "Coordinated omission: the load test that hides the stall", CQ)}
<p class="lede-s">Most load tests send a request, wait for the answer, then send the next. When the server stalls, the test stalls with it — and stops sending the requests that real users would have kept sending. Those requests are never measured. Gil Tene named this <b>coordinated omission</b>: the tester coordinates with the system it measures, and omits exactly the bad moments.</p>
{co_diagram()}
<div class="two top" style="grid-template-columns:1fr 1fr;gap:3mm;margin-top:2mm">
  <div class="mech" style="--accent:{CQ}">
    <h3>Two ways to get the truth</h3>
    <p><b>Measure from the due time.</b> Keep a schedule — an <i>open</i> workload — and count each request’s latency from when it should have been sent. wrk2 “measures response latency from the time the transmission <i>should</i> have occurred”.</p>
    <p style="margin-top:1mm"><b>Or correct afterwards.</b> HdrHistogram’s <code>recordValueWithExpectedInterval</code> adds, for a value longer than the expected interval, “an additional series of decreasingly-smaller … value records” — the requests that would have queued behind it.</p>
  </div>
  <div class="mech" style="--accent:{CQ}">
    <h3>Open and closed models in load tools</h3>
    <p class="rfc">“In a closed model, the execution time of each iteration dictates the number of iterations executed … In the open model, on the other hand, VUs arrive independently of iteration completion.” — k6 documentation</p>
    <p>k6: <code>constant-arrival-rate</code>, <code>ramping-arrival-rate</code> (open). Gatling: <code>constantUsersPerSec</code>, <code>rampUsersPerSec</code> (open) versus <code>constantConcurrentUsers</code> (closed). Real users arrive whether or not the last one finished: test with an open model.</p>
  </div>
</div>
<div class="mech" style="--accent:{CQ};margin-top:2mm">
    <h3>The arithmetic of this chapter’s experiment</h3>
    <p>The program (constants read from <code>CoordinatedOmission.java</code>) sends one request every {CO_INT_MS:g} ms for {CO_RUN_S:g} s — {CO_N:,} due — and the server stalls once, for {CO_STALL_MS:g} ms. <b>Open loop:</b> {CO_DUE:,} requests fall due during the stall, {CO_DUE / CO_N * 100:.0f}% of all; they wait from about {CO_STALL_MS:g} ms down to 0, so everything from about p{100 - CO_DUE / CO_N * 100:.0f} up is stall. <b>Closed loop:</b> the client waits with the server, so only one request sees the stall — 1 of {int(naive[0]):,} samples, {1 / int(naive[0]) * 100:.2f}%: it can only appear at p99.99 or the maximum. Chapter 5’s second page shows exactly that.</p>
  </div>
<h2>Percentiles, read correctly</h2>
<div class="two top" style="grid-template-columns:1fr 1fr;gap:3mm">
  <div>
    {code(dsrc("Stats.java", "  /** Nearest-rank", "\n  }"), "Stats.java — the percentile every experiment here uses", cls="xs")}
    <p class="small" style="margin-top:1mm"><b>p99 of 5,000 samples is the 4,950th smallest</b> — the 50 slowest are above it. Nearest-rank never interpolates: the value reported was really measured.</p>
  </div>
  {table(["Requests per page view", "Chance one of them is slower than p99"], [(str(n), f"{(1 - 0.99 ** n) * 100:.0f}%") for n in (1, 10, 50, 100, 200)], "xs")}
</div>
<p class="small" style="margin-top:1.2mm">The table is arithmetic, not a measurement: 1 − 0.99<sup>n</sup>. A page that makes 100 backend calls shows a p99 delay to most of its users — so for the calls behind a page, p99.9 and the maximum are the numbers that describe the user’s experience.</p>
{src("HdrHistogram AbstractHistogram.recordValueWithExpectedInterval (Javadoc)", "wrk2 README (github.com/giltene/wrk2)", "k6 docs, “Open and closed models”", "Gatling docs, “Injection”")}
''', chapter=K5, color=CQ, bm="05 · Measuring latency")

PCTS = [k for k in ["p50", "p90", "p99", "p99.9", "p99.99", "max"] if k in naive[1]]
CO_ROWS = [(name, d[0], *[(f"<b>{d[1][k]}</b>" if k == "p99" and name != "closed loop, HdrHistogram-style correction" else d[1][k]) for k in PCTS])
           for name, d in [("closed loop — what most tests report", naive), ("closed loop, HdrHistogram-style correction", corr), ("open loop, latency from the due time", openl)]]
SPECTRUM = chart([("closed loop (naive)", "#1D4ED8", [float(naive[1][k]) for k in PCTS]),
                  ("closed loop, corrected", "#B45309", [float(corr[1][k]) for k in PCTS]),
                  ("open loop, from due time", "#B91C1C", [float(openl[1][k]) for k in PCTS])],
                 PCTS, "Latency by percentile, same stall, three measurements", "ms (log scale)", logy=True, w=520, h=170)
page("co2", f'''
{sub(K5, "Measured: one stall, three reports", CQ)}
<p class="lede-s">A service that answers in 1 ms, except once: from second 2 to second 3 of a 10-second run it stalls. The intended rate is one request every 2 ms (500 per second). The same stall, measured three ways:</p>
{table(["Measurement", "Samples", *[f"{k} ms" for k in PCTS]], CO_ROWS, "xs")}
<p class="small muted" style="margin-top:1mm">Real output · {RUNNER}</p>
{SPECTRUM}
<div class="two top" style="grid-template-columns:1fr 1fr;gap:3mm;margin-top:2mm">
  {code(dsrc("latency/CoordinatedOmission.java", "  /** Requests are due", "\n  }"), "open loop: latency from the due time", cls="xs")}
  {code(dsrc("latency/CoordinatedOmission.java", "  /**\n   * HdrHistogram", "\n  }"), "the correction, as HdrHistogram does it", cls="xs")}
</div>
<div class="two top" style="grid-template-columns:1fr 1fr;gap:3mm;margin-top:2mm">
  {ticks([f"<b>The naive p99 was {naive[1]['p99']} ms</b> — a healthy-looking service. Measured from the due times, p99 was <b>{openl[1]['p99']} ms</b>: one request in ten was due during the stall, and more waited while the backlog drained.",
          f"<b>The naive run recorded {naive[0]} samples, not {CO_N:,}</b>: the missing {CO_N - int(naive[0])} are the requests the client did not send while it waited. The max was right; the percentiles below it were not.",
          f"<b>The correction recovered most of it</b> (p99 {corr[1]['p99']} ms) from the closed-loop data alone, because the expected interval was known."], CQ)}
  {ticks(["<b>Report max and high percentiles, with the sample count.</b> A drop in the count during a test is a stall the percentiles cannot show.",
          "<b>Generate load on a schedule</b> (open model) and measure from the due time; if your tool cannot, correct with the known interval.",
          "<b>Never average latencies</b>, and never average percentiles across machines or intervals: merge the histograms, then read the percentile."], CQ)}
</div>
{src("results: deepdive/logs/co.txt", "deepdive/src/…/latency/CoordinatedOmission.java", "G. Tene, “How NOT to Measure Latency” (conference talk)")}
''', chapter=K5, color=CQ)
