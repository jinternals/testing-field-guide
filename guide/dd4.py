"""Chapter 6 · JIT warm-up and benchmarks. Chapter 7 · GC pauses. Chapter 8 · virtual threads."""
from dd_lib import *

# ============================================================================
# 6 · JIT
# ============================================================================
K6 = chap(6, "JIT and benchmarks")


def batches(name):
    return [(int(a), float(b)) for a, b in re.findall(r"^\s*(\d+)\s+([\d.]+)$", dlog(name), re.M)]


WU, XI = batches("warmup.txt"), batches("warmup-xint.txt")
steady = sorted(v for _, v in WU[-5:])[2]
interp = sorted(v for _, v in XI[-5:])[2]
COMP = [l for l in dlog("warmup-compilation.txt").splitlines() if l.strip()]
FLAGS = {}
if has("jit-flags.txt"):
    FLAGS = dict(re.findall(r"\s(\w+)\s+=\s+(\d+)", dlog("jit-flags.txt")))
TIERS = [
    ("0", "interpreter", "runs bytecode; profiles the method"),
    ("1", "C1, full optimisation, no profiling", "trivial methods"),
    ("2", "C1 with invocation and back-edge counters", "when C2 is busy"),
    ("3", "C1 with full profiling", "the usual first compiled form"),
    ("4", "C2, profile-guided optimisation", "the fast steady state"),
]
WARM_CHART = chart([("default (tiered JIT)", "#6D28D9", [v for _, v in WU]), ("-Xint (interpreter only)", "#B91C1C", [v for _, v in XI])],
                   [str(b) for b, _ in WU], "µs per call, batch by batch from the first call", "µs per call (log)", logy=True, w=300, h=160, xlabel="batch of 100 calls")

thr = ""
if FLAGS:
    thr = (f'<p class="small" style="margin-top:1mm">On the runner’s JVM: <code>Tier3InvocationThreshold</code> = {FLAGS.get("Tier3InvocationThreshold")}, '
           f'<code>Tier4InvocationThreshold</code> = {FLAGS.get("Tier4InvocationThreshold")}, <code>Tier4BackEdgeThreshold</code> = {FLAGS.get("Tier4BackEdgeThreshold")}, '
           f'<code>CICompilerCount</code> = {FLAGS.get("CICompilerCount")} — from <code>-XX:+PrintFlagsFinal</code>. They are thresholds for counters scaled by the policy, not exact call counts.</p>')

page("jit", f'''
{sub(K6, f"Warm-up: the same method, {interp / steady:.0f}× faster later", CJ)}
<p class="lede-s">HotSpot starts every method in the interpreter, counts calls and loop iterations, and compiles the hot ones — first quickly with C1, collecting a profile, then again with C2 using that profile. Until then the code runs slower, sometimes much slower. A test or benchmark that measures the first calls measures the interpreter.</p>
<div class="two top" style="grid-template-columns:1fr 1fr;gap:3mm">
  <div>
    {table(["Level", "Code", "Used for"], TIERS, "xs")}
    {thr}
  </div>
  {WARM_CHART}
</div>
<div class="two top" style="grid-template-columns:1.1fr 1fr;gap:3mm;margin-top:2mm">
  {code(dsrc("jit/WarmUp.java", "    for (int batch = 1", "\n    }"), "WarmUp.java — 30 batches of 100 calls", cls="xs")}
  <div>
    {code("\n".join(COMP), "-XX:+PrintCompilation · real output (ms · id · % OSR · level)", kind="plain", cls="xs out wrap")}
    <p class="small" style="margin-top:1mm">Read top to bottom: level 3 code with on-stack replacement (<code>%</code> at bytecode 11, the loop), level 3, then level 4 OSR; the level 3 versions are <b>made not entrant</b> once the level 4 code replaces them.</p>
  </div>
</div>
<h2>Reading a PrintCompilation line</h2>
{table(["Column", "Meaning"], [
    ("1", "milliseconds since the JVM started"),
    ("2", "compile id — the same id for every event of one compilation"),
    ("3", "flags: <code>%</code> on-stack replacement · <code>s</code> synchronized · <code>!</code> has exception handlers · <code>b</code> blocking compile · <code>n</code> native wrapper"),
    ("4", "tier, 0–4 (table above)"),
    ("5", "the method; <code>@ 11</code> after an OSR compile is the bytecode index of the loop it enters at; then the bytecode size"),
    ("…", "<code>made not entrant</code>: new calls no longer use this code — a better tier replaced it, or an assumption it made was broken (deoptimisation)"),
], "xs")}
<div class="two top" style="grid-template-columns:1fr 1fr;gap:3mm;margin-top:2mm">
  {ticks([f"<b>Interpreter only:</b> about {interp:.0f} µs per call. <b>Compiled:</b> about {steady:.1f} µs — {interp / steady:.0f}× faster, the same code.",
          f"<b>The first batches</b> ran at {WU[0][1]:.0f}–{max(v for _, v in WU[:3]):.0f} µs while compilation was under way."], CJ)}
  {ticks(["<b>Warm up before you measure</b>, and keep measuring until the numbers are flat; or use JMH, which does both and forks a fresh JVM.",
          "<b>Load tests:</b> discard the first minutes, or plot latency over time — a cold service after a deploy is slower, and that is worth knowing too."], CJ)}
</div>
{src("OpenJDK 21 hotspot/share/compiler/compilationPolicy.hpp (the five levels), compileTask.cpp (the print format)", "-XX:+PrintCompilation, -XX:+PrintFlagsFinal on the runner", "results: deepdive/logs/warmup*.txt, jit-flags.txt")}
''', chapter=K6, color=CJ, bm="06 · JIT and benchmarks")

JMH = {}
for m in re.finditer(r"DeadCodeBench\.(\w+)\s+avgt\s+\d+\s+([\d.]+)\s+±\s+([\d.]+)\s+ns/op", dlog("jmh.txt")):
    JMH[m.group(1)] = (float(m.group(2)), float(m.group(3)))
base = JMH["baseline"][0]


def verdict(discarded, kept):
    """Compare a variant whose result is unused with the same work returned, both relative to the empty baseline."""
    if discarded not in JMH or kept not in JMH:
        return None
    d, k = JMH[discarded][0] - base, JMH[kept][0] - base
    noise = 3 * max(JMH[discarded][1], JMH[kept][1], JMH["baseline"][1])
    if k <= noise:
        return "too cheap"
    if d <= 0.25 * k:
        return "removed"
    return "not removed" if d >= 0.75 * k else "partly"


def say(v, what):
    return {"removed": f"the JIT <b>removed</b> {what}.",
            "not removed": f"<b>not</b> removed: {what} still ran.",
            "partly": f"partly removed — {what} got cheaper but did not vanish.",
            "too cheap": "the work is too cheap to tell apart from the harness."}[v]


JMH_ROWS = [(f"<code>{n}</code>", f"{v:.3f}", f"± {e:.3f}", f"{v - base:+.3f}") for n, (v, e) in JMH.items()]
log_v = verdict("discarded", "returned")
const_folded = "constant" in JMH and JMH["constant"][0] - base <= 0.25 * (JMH["returned"][0] - base)
findings = [f"<b>The empty baseline costs {base:.2f} ns</b>: the harness itself. Anything at that level did no work.",
            f"<b>Math.log, result unused</b>: {JMH['discarded'][0]:.2f} ns; returned {JMH['returned'][0]:.2f} ns; into a Blackhole {JMH['blackhole'][0]:.2f} ns — "
            + say(log_v, "the unused call") + ("" if log_v == "removed" else " JMH’s classic dead-code sample (JMHSample_08, also <code>Math.log</code>) does not reproduce here."),
            f"<b>Math.log of a static final constant</b>: {JMH['constant'][0]:.2f} ns — " + ("folded at compile time." if const_folded else "<b>not</b> folded: HotSpot does not evaluate this intrinsic ahead of time.")]
if "sumDiscarded" in JMH:
    findings.append(f"<b>A pure loop summing 1,000 ints</b>: {JMH['sumDiscarded'][0]:.2f} ns unused, {JMH['sumReturned'][0]:.2f} ns returned — " + say(verdict("sumDiscarded", "sumReturned"), "the whole loop"))
if "mulDiscarded" in JMH:
    findings.append(f"<b><code>x * x + 1</code></b>: {JMH['mulDiscarded'][0]:.2f} ns unused, {JMH['mulReturned'][0]:.2f} ns returned, {JMH['mulConstant'][0]:.2f} ns on constants — " + say(verdict("mulDiscarded", "mulReturned"), "the arithmetic"))
BENCH = dsrc("jit/DeadCodeBench.java", "@State")
cut = BENCH.index("  @Benchmark\n  public void sumDiscarded")
page("jit2", f'''
{sub(K6, "Measured with JMH: when does the JIT throw your work away?", CJ)}
<p class="lede-s">The JIT may remove code whose result is never used (dead-code elimination) and compute expressions on constants ahead of time (constant folding). A hand-written timing loop cannot tell whether that happened. JMH makes it visible: compare against an empty baseline, and hand results back (return them, or <code>Blackhole.consume</code>).</p>
<div class="two top" style="grid-template-columns:1fr 1fr;gap:3mm">
  {code(BENCH[:cut], "DeadCodeBench.java (1/2)", cls="xs")}
  {code(BENCH[cut:], "DeadCodeBench.java (2/2)", cls="xs")}
</div>
<div class="two top" style="grid-template-columns:1fr 1.15fr;gap:3mm;margin-top:2mm">
  <div>
    {table(["Benchmark", "ns/op", "error (99.9%)", "minus baseline"], JMH_ROWS, "xs")}
    <p class="small muted" style="margin-top:1mm">JMH 1.37 · 1 fork, 3 warm-up and 5 measured iterations of 1 s · {RUNNER}</p>
  </div>
  {ticks(findings, CJ)}
</div>
<div class="two top" style="grid-template-columns:1fr 1fr;gap:3mm;margin-top:2mm">
  {ticks(["<b>Never trust a benchmark you have not seen fail.</b> Add a baseline and a variant that should be eliminated; if they differ in the wrong direction, the measurement is broken.",
          "<b>What happens is JDK- and CPU-specific.</b> These numbers are from one JDK on one machine; rerun them where you deploy."], CJ)}
  {ticks(["<b>Return results or use a Blackhole</b>; read inputs from <code>@State</code> fields, not constants.",
          "<b>Let JMH fork</b> (<code>-f</code>): a fresh JVM per run avoids profiles left over from other benchmarks."], CJ)}
</div>
{src("JMH 1.37 (org.openjdk.jmh): Blackhole, @State, -f/-wi/-i options; JMHSample_08_DeadCode", "results: deepdive/logs/jmh.txt, jmh-full.txt")}
''', chapter=K6, color=CJ)

# ============================================================================
# 7 · GC
# ============================================================================
K7 = chap(7, "GC pauses and tail latency")
PAUSE = re.compile(r"^\[([\d.]+)s\].*GC\((\d+)\) (?:([YOyo]): )?Pause (.+?) ([\d.]+)ms$", re.M)


def pauses_of(name, up):
    """Every pause after measuring started: (gc id, kind, ms, evacuation failed)."""
    out = []
    for ts, gid, gen, rest, ms in PAUSE.findall(dlog(f"gc-{name}.log")):
        if float(ts) < up:
            continue
        failed = "Evacuation Failure" in rest
        kind = re.sub(r"\s*\((G1 [A-Za-z ]+Pause|Evacuation Failure|Major|Minor)\)|\s*\d+M->\d+M\(\d+M\)", "", rest).strip()
        cyc = {"y": " · minor", "Y": " · major, young", "O": " · major, old"}.get(gen, "")
        out.append((int(gid), kind + cyc, float(ms), failed))
    return out


GC = {}
for name in ("G1", "ZGC"):
    t = dlog(f"gc-{name}.txt")
    up = float(re.search(r"measuring from uptime ([\d.]+) s", t).group(1))
    m = re.search(r"(\d+) operations\s+p50 ([\d.]+)\s+p99 ([\d.]+)\s+p99\.9 ([\d.]+)\s+max ([\d.]+) ms", t)
    ev = pauses_of(name, up)
    GC[name] = dict(ops=int(m.group(1)), p50=float(m.group(2)), p99=float(m.group(3)), p999=float(m.group(4)), max=float(m.group(5)),
                    pauses=[ms for _, _, ms, _ in ev], events=ev, up=up)
INTERVAL_MS = 0.05  # GcLatency.INTERVAL_NS
for g in GC.values():
    g["window"] = g["ops"] * INTERVAL_MS
    g["paused"] = sum(g["pauses"])
    g["due"] = g["paused"] / INTERVAL_MS


def kinds(g):
    k = {}
    for _, kind, ms, failed in g["events"]:
        c = k.setdefault(kind, [0, 0.0, 0])
        c[0] += 1
        c[1] = max(c[1], ms)
        c[2] += failed
    return k


G1_WHAT = {
    "Young (Normal)": "copies live young objects; promotes survivors to old",
    "Young (Concurrent Start)": "a young collection that also starts concurrent marking",
    "Remark": "finishes marking, processes references, frees empty regions",
    "Cleanup": "decides whether mixed collections follow",
    "Young (Prepare Mixed)": "the last young-only collection before mixed ones",
    "Young (Mixed)": "young regions plus some old regions, copied",
    "Full": "fallback: compacts the whole heap in place, all threads stopped",
}
ZGC_WHAT = {"Mark Start": "starts concurrent marking", "Mark End": "ends marking", "Relocate Start": "starts concurrent relocation"}
g1k, zk = kinds(GC["G1"]), kinds(GC["ZGC"])
G1_KIND_ROWS = [(k, str(c), f"{mx:.3f}", (f"{f}" if f else "–"), G1_WHAT.get(k, "")) for k, (c, mx, f) in g1k.items()]
Z_KIND_ROWS = [(k, str(c), f"{mx:.3f}", ZGC_WHAT.get(k.split(" · ")[0], "")) for k, (c, mx, f) in zk.items()]
evac_failed = sum(f for _, _, f in g1k.values())
full = [e for e in GC["G1"]["events"] if e[1] == "Full"]
FULL_PHASES = []
if full:
    gid = max(full, key=lambda e: e[2])[0]
    FULL_PHASES = re.findall(rf"GC\({gid}\) Phase \d: (.+?) ([\d.]+)ms$", dlog("gc-G1.log"), re.M)
    FULL_HEAP = re.search(rf"GC\({gid}\) Pause Full .*?(\d+M->\d+M)\(", dlog("gc-G1.log")).group(1)
GC_ROWS = [(n, f"{g['ops']:,}", f"{g['p50']:.3f}", f"{g['p99']:.3f}", f"{g['p999']:.3f}", f"{g['max']:.3f}",
            str(len(g["pauses"])), f"{max(g['pauses']):.3f}" if g["pauses"] else "–", f"{g['paused']:.1f}") for n, g in GC.items()]
GC_CHART = chart([("G1", "#B45309", [GC["G1"][k] for k in ("p50", "p99", "p999", "max")]), ("ZGC, generational", "#6D28D9", [GC["ZGC"][k] for k in ("p50", "p99", "p999", "max")])],
                 ["p50", "p99", "p99.9", "max"], "Operation latency, from the due time", "ms (log)", logy=True, w=300, h=150)

evac_note = (f'<p class="small" style="margin-top:1mm"><b>Evacuation failure</b> ({evac_failed} of these pauses): G1 could not find free regions to copy live objects into. '
             'The tuning guide: G1 then hopes marking and mixed collections catch up; “if this assumption doesn’t hold, then G1 will eventually schedule a Full GC”'
             + (f' — which is what happened here: one full, in-place compaction of the heap ({FULL_HEAP}).' if full else '.') + '</p>') if evac_failed else ""
page("gc", f'''
{sub(K7, "Stop-the-world, or almost never", CJ)}
<p class="lede-s">A garbage collector has to find live objects and make room. Some of that work needs every application thread stopped — a <b>pause</b>. G1, the default on a server-class machine, collects in regions and aims for short pauses, but copies live objects while the application waits. ZGC does that work concurrently, while the application runs, and stops it only briefly.</p>
<div class="two top" style="grid-template-columns:1fr 1fr;gap:3mm">
  <div class="mech" style="--accent:{CJ}">
    <h3>The collectors, as of JDK 21–24</h3>
    <p><b>G1</b>: default when the JVM sees at least 2 CPUs and about 1792 MB (chapter 9). Young and mixed collections copy live objects during pauses; marking of the old generation runs concurrently.</p>
    <p style="margin-top:1mm"><b>Generational ZGC</b>: JEP 439, JDK 21, enabled with <code>-XX:+UseZGC -XX:+ZGenerational</code>; the default ZGC mode from JDK 23 (JEP 474); the only mode from JDK 24 (JEP 490). Marking and relocation run concurrently; the remaining pauses do not grow with the heap.</p>
  </div>
  {GC_CHART}
</div>
<h2>A G1 cycle, as it happened in the measured window</h2>
{table(["Pause", "Count", "Longest ms", "Evacuation failed", "What it does (JDK 21 G1 tuning guide)"], G1_KIND_ROWS, "xs")}
{evac_note}
<h2>The workload</h2>
<div class="two top" style="grid-template-columns:1.25fr 1fr;gap:3mm">
  {code(dsrc("gc/GcLatency.java", "    for (int i = 0; i < total; i++) {", "\n    }", dedent=4), "GcLatency.java — one operation due every 50 µs", cls="xs")}
  <p class="small">A live set of 400,000 × 1 KB arrays (≈ 400 MB in a 1 GB heap) that keeps changing — every operation replaces one, so old objects keep dying — plus 8 KB of garbage per operation. One operation is due every 50 µs for 15 s; latency counts from the due time, the open-loop measurement from chapter 5. Pauses come from each JVM’s own log (<code>-Xlog:gc,gc+phases</code>), from the moment measuring started.</p>
</div>
{src("JEP 439 (JDK 21), JEP 474 (JDK 23), JEP 490 (JDK 24)", "Java SE 21 HotSpot GC Tuning Guide, “Garbage-First (G1) Garbage Collector”", "OpenJDK 21 gcConfig.cpp, os.cpp (default selection)", f"run: {RUNNER}, -Xms1g -Xmx1g")}
''', chapter=K7, color=CJ, bm="07 · GC pauses")

g1, z = GC["G1"], GC["ZGC"]
no_full = [ms for _, k, ms, _ in g1["events"] if k != "Full"]
tail_card = f'''<div class="mech" style="--accent:{CJ}">
    <h3>Why p99 sits on the pauses</h3>
    <p>In an open loop, every operation that falls due during a pause waits for it. G1 was paused for {g1["paused"]:.1f} ms of the {g1["window"] / 1000:.0f} s window: about {g1["due"]:,.0f} operations (one per 50 µs) were due while the application was stopped — {g1["due"] / g1["ops"] * 100:.2f}% of all operations. Anything above that share is inside the tail: p99 is the slowest 1%, p99.9 the slowest 0.1%.</p>
    <p style="margin-top:1mm">ZGC was paused for {z["paused"]:.2f} ms in total — about {z["due"]:,.0f} operations, {z["due"] / z["ops"] * 100:.4f}%: too few to reach p99.9.</p>
  </div>'''
anat = ""
if FULL_PHASES:
    anat = f'''<div>
    {table(["Full GC phase", "ms"], [(n, f"{float(v):.3f}") for n, v in FULL_PHASES] + [("<b>pause</b>", f"<b>{max(e[2] for e in full):.3f}</b>")], "xs")}
    <p class="small" style="margin-top:1mm">The full collection marked and compacted the whole heap while every application thread waited. Without it, G1’s longest pause was {max(no_full):.1f} ms.</p>
  </div>'''
else:
    anat = table(["ZGC pause", "Count", "Longest ms", "What it does"], Z_KIND_ROWS, "xs")
page("gc2", f'''
{sub(K7, "Measured: G1 and generational ZGC, same workload", CJ)}
{table(["Collector", "Operations", "p50 ms", "p99 ms", "p99.9 ms", "max ms", "pauses", "longest pause ms", "pause total ms"], GC_ROWS, "xs")}
<p class="small muted" style="margin-top:1mm">Real output and GC logs · {RUNNER}</p>
<div class="two top" style="grid-template-columns:1fr 1fr;gap:3mm;margin-top:2mm">
  {ticks([f"<b>The median was the same</b> ({g1['p50']:.3f} ms against {z['p50']:.3f} ms): most operations never meet a pause.",
          f"<b>The tail was not:</b> G1’s p99.9 was {g1['p999']:.1f} ms and its worst operation waited {g1['max']:.1f} ms; with ZGC p99.9 was {z['p999']:.3f} ms and the worst {z['max']:.1f} ms.",
          f"<b>The GC logs agree:</b> G1’s longest pause was {max(g1['pauses']):.1f} ms; ZGC paused {len(z['pauses'])} times, the longest {max(z['pauses']):.3f} ms."
          + (f" ZGC’s worst operation ({z['max']:.1f} ms) was therefore <b>not</b> a GC pause: something else — the OS scheduler, the collector’s own threads on {MACHINE['cpus']} CPUs — delayed it." if z["max"] > 10 * max(z["pauses"]) else "")], CJ)}
  {ticks(["<b>Concurrent is not free:</b> ZGC uses CPU while the application runs. On a machine with few cores, measure throughput too, not only latency.",
          "<b>Log GC in every load test</b> (<code>-Xlog:gc*</code>) and line the pauses up with the slow requests — a slow p99.9 with long pauses at the same moments is GC.",
          "<b>Size the heap on purpose</b> (<code>-Xmx</code> or <code>MaxRAMPercentage</code>): the default is 25% of the memory the JVM sees, which in a container is the container’s limit."], CJ)}
</div>
<div class="two top" style="grid-template-columns:1.2fr 1fr;gap:3mm;margin-top:2mm">
  {tail_card}
  {anat}
</div>
<h2>Every pause in the measured window</h2>
<div class="two top" style="grid-template-columns:1fr 1.2fr;gap:3mm">
  {code(chr(10).join(f"{ms:8.3f} ms  {k}" for _, k, ms, _ in g1["events"][:26]), f"G1: {len(g1['pauses'])} pauses", kind="plain", cls="xs out")}
  <div>{table(["ZGC: " + str(len(z["pauses"])) + " pauses", "Count", "Longest ms", "What it does"], Z_KIND_ROWS, "xs")}
  <p class="small" style="margin-top:1mm">The log tags each ZGC pause <code>y:</code> (a minor cycle: young generation only), or <code>Y:</code> / <code>O:</code> (the young and old generations of a major cycle, which it marks <code>(Major)</code>).</p></div>
</div>
{src("Java SE 21 HotSpot GC Tuning Guide (G1 cycle, evacuation failure)", "results: deepdive/logs/gc-G1.txt, gc-G1.log, gc-ZGC.txt, gc-ZGC.log")}
''', chapter=K7, color=CJ)

# ============================================================================
# 8 · virtual threads
# ============================================================================
K8 = chap(8, "Virtual threads")
VT = dlog("vt.txt")
vt = dict((m.group(1).strip(), float(m.group(2))) for m in re.finditer(r"^(\d[\d,]* tasks, .+?)\s{2,}([\d.]+) s$", VT, re.M))
carriers = int(re.search(r"availableProcessors\): (\d+)", VT).group(1))
pin_trace = "\n".join(l for l in VT.splitlines() if "VirtualThread[" in l or "<==" in l)[:400]
plat, virt = vt["10,000 tasks, 200 platform threads"], vt["10,000 tasks, virtual thread each"]
pinned, unpinned = vt["100 tasks, synchronized + sleep"], vt["100 tasks, ReentrantLock + sleep"]
VT_ROWS = [(k, f"{v:.2f} s") for k, v in vt.items()]

page("vt", f'''
{sub(K8, "Cheap threads, and the one thing that pins them", CJ)}
<p class="lede-s">A virtual thread (JEP 444, final in JDK 21) is a Java thread that is not tied to an OS thread. It runs <i>mounted</i> on a carrier — a platform thread of a small pool — and when it blocks on I/O, a sleep or a lock, it <i>unmounts</i> and the carrier runs another one. Blocking becomes cheap; you can have a thread per task again.</p>
<div class="two top" style="grid-template-columns:1fr 1fr;gap:3mm">
  <div class="mech" style="--accent:{CJ}">
    <h3>Carriers</h3>
    <p>The scheduler is a <code>ForkJoinPool</code> whose parallelism is <code>availableProcessors()</code> unless <code>jdk.virtualThreadScheduler.parallelism</code> says otherwise (JDK 21 <code>VirtualThread.java</code>). The runner had {carriers}.</p>
  </div>
  <div class="mech" style="--accent:{CJ}">
    <h3>Pinning (JDK 21–23)</h3>
    <p>Blocking inside <code>synchronized</code> keeps the virtual thread <b>pinned</b>: it cannot unmount, so it holds its carrier while it waits. JEP 491 (JDK 24) lets virtual threads unmount inside <code>synchronized</code>; the <code>jdk.tracePinnedThreads</code> property used here was removed with it.</p>
  </div>
</div>
<div class="two top" style="grid-template-columns:1.1fr 1fr;gap:3mm;margin-top:2mm">
  {code(dsrc("vt/VirtualThreads.java", "  static void blockInSynchronized", "\n  }") + "\n\n" + dsrc("vt/VirtualThreads.java", "  static void blockInLock", "\n  }"), "VirtualThreads.java — the same wait, two locks", cls="xs")}
  <div>
    {table(["Run", "Wall time"], VT_ROWS, "xs")}
    <p class="small muted" style="margin-top:1mm">Real output · JDK 21 · {RUNNER}</p>
    {code(pin_trace, "-Djdk.tracePinnedThreads=short · real output", kind="plain", cls="xs out wrap")}
  </div>
</div>
<div class="two top" style="grid-template-columns:1fr 1fr;gap:3mm;margin-top:2mm">
  {ticks([f"<b>10,000 blocking tasks:</b> {plat:.2f} s on 200 platform threads (10,000 / 200 × 0.1 s = 5 s), {virt:.2f} s with a virtual thread each.",
          f"<b>Pinned:</b> 100 tasks holding a monitor while sleeping took {pinned:.2f} s = 100 / {carriers} carriers × 0.1 s. With <code>ReentrantLock</code>: {unpinned:.2f} s."], CJ)}
  {ticks(["<b>On JDK 21–23, replace <code>synchronized</code> around blocking calls</b> with <code>java.util.concurrent</code> locks, or upgrade: JDK 24 removes this kind of pinning.",
          "<b>Virtual threads do not make CPU work faster</b> — chapter 4’s CPU pool applies unchanged. They make waiting cheap."], CJ)}
</div>
<h2>What a blocking call does to the carrier, JDK 21</h2>
{table(["The virtual thread blocks in…", "Carrier", "Evidence"], [
    ("<code>Thread.sleep</code>, <code>LockSupport.park</code>, <code>java.util.concurrent</code> locks and queues, socket I/O", "<b>released</b> — the virtual thread unmounts", f"measured above: ReentrantLock + sleep, {unpinned:.2f} s"),
    ("<code>Object.wait()</code>, file I/O such as <code>FileInputStream.read</code>", "held, but <b>compensated</b>: the pool adds a carrier for the duration", "JDK 21 <code>Object.wait</code> and <code>FileInputStream.read</code> call <code>Blocker.begin()</code> → <code>ForkJoinPool</code> compensated block"),
    ("any of the above inside <code>synchronized</code>", "<b>pinned</b>, not compensated: the carrier waits too", f"measured above: {pinned:.2f} s = 100 / {carriers} × 0.1 s; <code>VirtualThread.parkOnCarrierThread</code>"),
    ("a native method or foreign function on the stack", "<b>pinned</b>", "JEP 444, “Pinning”"),
], "xs")}
<div class="two top" style="grid-template-columns:1fr 1fr;gap:3mm;margin-top:2mm">
  <p class="small"><b>Compensation has a ceiling:</b> <code>jdk.virtualThreadScheduler.maxPoolSize</code>, by default the larger of the parallelism and 256 (JDK 21 <code>VirtualThread.createDefaultScheduler</code>). Thousands of virtual threads in file I/O at once still queue.</p>
  <p class="small"><b>Finding pins in production:</b> the JFR event <code>jdk.VirtualThreadPinned</code> is on in the default JFR settings, with a 20 ms threshold and a stack trace (JDK 21 <code>default.jfc</code>). Do not pool virtual threads — JEP 444: they are cheap enough to create one per task.</p>
</div>
{src("JEP 444 (JDK 21), JEP 491 (JDK 24)", "OpenJDK 21 java/lang/VirtualThread.java, Object.java, io/FileInputStream.java, jdk/internal/misc/Blocker.java", "jdk.jfr default.jfc", "results: deepdive/logs/vt.txt")}
''', chapter=K8, color=CJ, bm="08 · Virtual threads")
