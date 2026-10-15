"""Chapter 9 · containers and CPUs. Chapter 10 · the Java Memory Model."""
from dd_lib import *

# ============================================================================
# 9 · containers
# ============================================================================
K9 = chap(9, "Containers and CPUs")
ROW = re.compile(r"^(.*?)\s+cgroup cpu\.max (\S+)\s+memory\.max (\S+)\s+\| CPUs (\d+)\s+max heap\s+(\d+) MB\s+commonPool (\d+)\s+GC (.+)$", re.M)
BOX = []
for label, cpu, mem, cpus, heap, pool, gcs in ROW.findall(dlog("containers.txt")):
    label = label.replace("docker run", "").strip()
    flags = " ".join(w for w in label.split() if w.startswith("-XX"))
    limits = " ".join(w for w in label.split() if not w.startswith("-XX") and w not in ("…", "java")) or "no limits"
    q, per = cpu.split("/")
    BOX.append(dict(limits=limits, flags=flags, cpu=cpu, quota=None if q == "max" else int(q) / int(per),
                    mem=None if mem == "max" else int(mem) // (1 << 20), cpus=int(cpus), heap=int(heap),
                    pool=int(pool), gc="Serial" if "Copy" in gcs else ("G1" if "G1" in gcs else gcs), gcs=gcs))
HOST = next(b for b in BOX if b["limits"] == "no limits")


def pct(b):
    return f"{b['heap'] / b['mem'] * 100:.1f}% of {b['mem']:,} MB" if b["mem"] else f"{b['heap']:,} MB of the host’s memory"


BOX_ROWS = [(f"<code>{b['limits']}</code>" + (f"<br><code>{b['flags']}</code>" if b["flags"] else ""),
             b["cpu"], f"{b['mem']:,} MB" if b["mem"] else "max", f"<b>{b['cpus']}</b>", f"{b['heap']:,} MB", pct(b).split(" of ")[0] if b["mem"] else "–",
             str(b["pool"]), f"<b>{b['gc']}</b>") for b in BOX]


def find(limits, flags=""):
    return next(b for b in BOX if b["limits"] == limits and b["flags"] == flags)


two, one, half = find("--cpus=2 --memory=2g"), find("--cpus=1 --memory=1g"), find("--cpus=0.5 --memory=512m")
apc = find("--cpus=1 --memory=1g", "-XX:ActiveProcessorCount=4")
mrp = find("--cpus=1 --memory=1g", "-XX:MaxRAMPercentage=75")

page("box", f'''
{sub(K9, "How the JVM reads cgroup limits", CP)}
<p class="lede-s">A container’s limits are cgroup settings: a CPU <b>quota</b> per period (<code>cpu.max</code>) and a memory limit (<code>memory.max</code>). With <code>UseContainerSupport</code>, true by default in JDK 21 (<code>globals_linux.hpp</code>), the JVM reads both at start-up and sizes itself from them — the number of CPUs it reports, the heap, the garbage collector, and every thread pool sized from <code>availableProcessors()</code>.</p>
<div class="two top" style="grid-template-columns:1fr 1fr 1fr;gap:3mm">
  <div class="mech" style="--accent:{CP}">
    <h3>CPUs from the quota</h3>
    <p><code>--cpus=N</code> writes <code>cpu.max</code> as <i>quota period</i>. HotSpot divides quota by period and <b>rounds up</b>, capped at the host’s CPUs (JDK 21 <code>cgroupUtil_linux.cpp</code>: <code>ceilf(quota / period)</code>). <code>-XX:ActiveProcessorCount</code> overrides the result.</p>
  </div>
  <div class="mech" style="--accent:{CP}">
    <h3>Heap from the memory limit</h3>
    <p>Without <code>-Xmx</code>, the maximum heap is <code>MaxRAMPercentage</code> of the memory the JVM sees — <b>25</b> by default (<code>gc_globals.hpp</code>). <code>MinRAMPercentage</code> (50) is used instead only when memory is so small that half of it is below the default <code>MaxHeapSize</code> (<code>arguments.cpp</code>).</p>
  </div>
  <div class="mech" style="--accent:{CP}">
    <h3>The collector from both</h3>
    <p>G1 is chosen only on a “server-class machine”: at least <b>2</b> active processors and at least <b>2 GB − 256 MB</b> of memory (<code>os.cpp</code> <code>is_server_class_machine</code>, with an extra check for hyper-threaded packages). Otherwise <b>Serial</b> — one thread, stop-the-world (<code>gcConfig.cpp</code>).</p>
  </div>
</div>
<h2>Measured: the same JVM, different limits</h2>
{table(["docker run …", "cpu.max", "memory.max", "CPUs", "max heap", "heap / limit", "common pool", "GC"], BOX_ROWS, "xs")}
<p class="small muted" style="margin-top:1mm">eclipse-temurin:21-jdk on {RUNNER} · the program prints <code>/sys/fs/cgroup</code> and what the JVM decided · GC names: Copy + MarkSweepCompact is Serial</p>
<div class="two top" style="grid-template-columns:1.05fr 1fr;gap:3mm;margin-top:2mm">
  {code(dsrc("box/Resources.java", "  public static void main", "\n  }"), "Resources.java", cls="xs")}
  {ticks([f"<b>--cpus=0.5</b> is reported as <b>{half['cpus']}</b> CPU: {half['quota']:g} rounded up. The JVM cannot express half a CPU; the kernel enforces it by throttling.",
          f"<b>2 CPUs and 2 GB</b> crossed the server-class line: <b>{two['gc']}</b>, heap {two['heap']} MB. <b>1 CPU and 1 GB</b> did not: <b>{one['gc']}</b>.",
          f"<b>ActiveProcessorCount=4</b> made the JVM report {apc['cpus']} CPUs (common pool {apc['pool']}) — and it still chose <b>{apc['gc']}</b>: 1 GB is below the memory line.",
          f"<b>MaxRAMPercentage=75</b> raised the heap from {one['heap']} MB to {mrp['heap']} MB in the same 1 GB container."], CP)}
</div>
<div style="margin-top:2mm">
  <div class="mech" style="--accent:{CP}">
    <h3>A quota is time, not cores</h3>
    <p><code>--cpus=0.5</code> lets the container run for half of each scheduling period, then stops it until the next one. The JVM still reports {half['cpus']} CPU and runs one GC thread. A multi-threaded burst can use the whole quota early in the period and then wait — throttling, visible in <code>cpu.stat</code> as <code>nr_throttled</code> and <code>throttled_usec</code>.</p>
  </div>
</div>
{src("OpenJDK 21: os/linux/cgroupUtil_linux.cpp, os/linux/globals_linux.hpp, runtime/os.cpp, gc/shared/gcConfig.cpp, gc/shared/gc_globals.hpp, runtime/arguments.cpp", "results: deepdive/logs/containers.txt")}
''', chapter=K9, color=CP, bm="09 · Containers and CPUs")

SIZED = [
    ("<code>ForkJoinPool.commonPool()</code> — parallel streams, <code>CompletableFuture.*Async</code>", "CPUs − 1, at least 1", "JDK 21 <code>ForkJoinPool.java</code>", f"{HOST['pool']} / {two['pool']} / {one['pool']}"),
    ("virtual-thread carriers", "CPUs", "JDK 21 <code>VirtualThread.java</code>", "chapter 8"),
    ("G1/Parallel GC worker threads (<code>ParallelGCThreads</code>)", "CPUs up to 8, then 8 + 5/8 of the rest", "JDK 21 <code>workerPolicy.cpp</code>", "–"),
    ("Netty event-loop threads", "2 × CPUs", "Netty 4.1 <code>MultithreadEventLoopGroup</code>", "–"),
    ("the garbage collector itself", "Serial below 2 CPUs or 1792 MB", "<code>os.cpp</code>, <code>gcConfig.cpp</code>", f"{one['gc']} at 1 CPU"),
]
THR = []
if has("throttle.txt"):
    for opts, bn, p50, p99, mx, per, thr, tms in re.findall(
            r"^docker run\s*(.*?)\s+burners (\d+)\s+sleep 5 ms, late by: p50 ([\d.]+)\s+p99 ([\d.]+)\s+max ([\d.]+) ms\s+\|\s+periods (\d+)\s+throttled (\d+)\s+throttled (\d+) ms$",
            dlog("throttle.txt"), re.M):
        THR.append(dict(opts=opts or "no limit", burners=int(bn), p50=float(p50), p99=float(p99), max=float(mx), periods=int(per), thr=int(thr), tms=int(tms)))
if THR:
    THR_ROWS = [(f"<code>{t['opts']}</code>", str(t["burners"]), f"{t['p50']:.1f}", f"{t['p99']:.1f}", f"<b>{t['max']:.1f}</b>",
                 str(t["periods"]) if t["periods"] else "–", str(t["thr"]) if t["periods"] else "–") for t in THR]
    hot = max(THR, key=lambda t: t["max"])
    calm = next((t for t in THR if t["opts"] == "no limit" and t["burners"] == hot["burners"]), None)
    THR_HTML = f'''<h2>Measured: throttling</h2>
{table(["docker run …", "busy threads", "late p50 ms", "late p99 ms", "late max ms", "periods", "throttled periods"], THR_ROWS, "xs")}
<div class="two top" style="grid-template-columns:1fr 1.3fr;gap:3mm;margin-top:1mm">
  <p class="small muted">Throttle.java: busy threads use the quota while a timer thread sleeps 5 ms, 600 times, and records how late it wakes; periods and throttling from the container’s <code>cpu.stat</code> · {RUNNER}</p>
  {ticks([f"<b>{hot['opts']} with {hot['burners']} busy threads:</b> {hot['thr']} of {hot['periods']} periods throttled, and a 5 ms sleep woke up to <b>{hot['max']:.0f} ms</b> late"
          + (f" — against {calm['max']:.1f} ms with no limit." if calm else "."),
          "<b>Why the timer thread was late:</b> the busy threads used the period’s quota, and <code>cpu.max</code> allows the cgroup “up to $MAX in each $PERIOD” (cgroup-v2.rst), so the timer thread could not run until the next period began."], CP)}
</div>'''
else:
    THR_HTML = PENDING

page("box2", f'''
{sub(K9, "Defaults sized from the CPU count; CPU throttling", CP)}
<p class="lede-s">These defaults are computed from <code>availableProcessors()</code>, which reported {one['cpus']} for both <code>--cpus=1</code> and <code>--cpus=0.5</code> in the runs on the previous page.</p>
{table(["Sized from the CPU count", "Default", "Source", "Measured (host / 2 / 1 CPU)"], SIZED, "xs")}
<div style="margin-top:3mm">
  <div class="mech" style="--accent:{CP}">
    <h3>The heap is not the whole process</h3>
    <p><code>memory.max</code> is a “memory usage hard limit” for the whole cgroup; if usage reaches it and cannot be reduced, “the OOM killer is invoked” (cgroup-v2.rst). The JVM uses memory outside the heap too: Native Memory Tracking reports it under Class, Thread Stack, Code, GC, Compiler, Internal, Other and more (JDK 21 <code>allocation.hpp</code>). Raising <code>MaxRAMPercentage</code> to 75 (measured above: {mrp['heap']} MB of {mrp['mem']:,} MB) leaves the rest for that memory; measure it with <code>-XX:NativeMemoryTracking=summary</code> and <code>jcmd &lt;pid&gt; VM.native_memory</code>.</p>
  </div>
</div>
<div class="two top" style="grid-template-columns:1fr 1fr;gap:3mm;margin-top:2mm">
  {ticks(["<b>Run performance tests with the production limits</b> — the same <code>--cpus</code> and <code>--memory</code>. A laptop or an unlimited runner chooses a different collector, a different heap and different pool sizes.",
          "<b>Print what the JVM decided:</b> <code>-Xlog:gc</code> prints the collector at start-up (“Using G1” in chapter 7’s log); <code>-XX:+PrintFlagsFinal</code> marks values the JVM chose itself <code>{ergonomic}</code>."], CP)}
  {ticks(["<b>Give a JVM service at least 2 CPUs and 2 GB</b>, or choose the collector yourself (<code>-XX:+UseG1GC</code>) — otherwise a small pod gets Serial.",
          "<b>Set the heap on purpose</b> — <code>-Xmx</code>, or <code>MaxRAMPercentage</code> for a heap that follows the limit."], CP)}
</div>
{THR_HTML}
{src("OpenJDK 21: java/util/concurrent/ForkJoinPool.java, java/lang/VirtualThread.java, gc/shared/workerPolicy.cpp, memory/allocation.hpp and services/nmtDCmd.hpp (Native Memory Tracking)", "Netty 4.1 MultithreadEventLoopGroup.java", "Linux 6.17 Documentation/admin-guide/cgroup-v2.rst (cpu.max, cpu.stat, memory.max)", "results: deepdive/logs/containers.txt, throttle.txt")}
''', chapter=K9, color=CP)

# ============================================================================
# 10 · Java Memory Model
# ============================================================================
K10 = chap(10, "The Java Memory Model")
JC = (OPS / "jcstress.log").read_text(errors="replace")
JC = JC[JC.index("RUN RESULTS:"):]
JCR = {}
for m in re.finditer(r"\[OK\] shop\.(\w+)\s+Results across all configurations:\s*\n\s*RESULT[^\n]*\n((?:[ \t]+\S[^\n]*\n)+)", JC):
    rows = []
    for line in m.group(2).splitlines():
        parts = re.split(r"\s{2,}", line.strip())
        if len(parts) == 5:
            rows.append(parts)
    JCR[m.group(1)] = rows


def jrow(test, rid):
    return next(r for r in JCR[test] if r[0] == rid)


def jtable(test):
    return table(["Result", "Samples", "Share", "Expected", "Meaning"],
                 [(f"<code>{r[0]}</code>", r[1], r[2], r[3], r[4]) for r in JCR[test]], "xs")


sb, sbv = jrow("StoreBufferingTest", "0, 0"), jrow("StoreBufferingVolatileTest", "0, 0")
sb_total = sum(int(r[1].replace(",", "")) for r in JCR["StoreBufferingTest"])
sbv_total = sum(int(r[1].replace(",", "")) for r in JCR["StoreBufferingVolatileTest"])
HB = ["An unlock on a monitor <i>happens-before</i> every subsequent lock on that monitor.",
      "A write to a <code>volatile</code> field <i>happens-before</i> every subsequent read of that field.",
      "A call to <code>start()</code> on a thread <i>happens-before</i> any actions in the started thread.",
      "All actions in a thread <i>happen-before</i> any other thread successfully returns from a <code>join()</code> on that thread."]

page("jmm", f'''
{sub(K10, "Data races, happens-before and store buffering", CJ)}
<p class="lede-s">Without synchronisation, Java promises much less than the source code suggests. The compiler and the CPU may reorder and cache memory accesses as long as a single thread cannot tell. The Java Memory Model (JLS chapter 17) says exactly when another thread is guaranteed to see a write — and that guarantee is the <i>happens-before</i> order.</p>
<div class="two top" style="grid-template-columns:1fr 1fr;gap:3mm">
  <div class="mech" style="--accent:{CJ}">
    <h3>Data race (JLS §17.4.5)</h3>
    <p>Two accesses to the same variable <b>conflict</b> if at least one is a write. A program has a <b>data race</b> when two conflicting accesses are not ordered by happens-before.</p>
    <p style="margin-top:1mm"><b>The guarantee</b> (§17.4.3): “If a program has no data races, then all executions of the program will appear to be sequentially consistent.” With a race, the JMM allows results no interleaving of the source lines can produce.</p>
  </div>
  <div class="mech" style="--accent:{CJ}">
    <h3>Happens-before, JLS §17.4.5 (quoted)</h3>
    {ticks(HB, CJ)}
    <p style="margin-top:1mm">Plus program order within a thread, and transitivity. The <code>java.util.concurrent</code> package documentation (“Memory Consistency Properties”) extends them to concurrent collections, executors, futures, locks and synchronizers.</p>
  </div>
</div>
<h2>Measured with jcstress: store buffering</h2>
<div class="two top" style="grid-template-columns:0.8fr 1.2fr;gap:3mm">
  {code(csrc("StoreBufferingTest.java", "@State"), "StoreBufferingTest.java (outcomes declared with @Outcome)", cls="xs")}
  <div>
    <p class="small" style="margin-bottom:1mm"><b>Plain fields</b> — every interleaving of the four lines gives at least one 1. Yet:</p>
    {jtable("StoreBufferingTest")}
    <p class="small" style="margin:2mm 0 1mm"><b>The same with <code>volatile int x, y</code></b> — <code>0, 0</code> declared forbidden:</p>
    {jtable("StoreBufferingVolatileTest")}
  </div>
</div>
<div class="two top" style="grid-template-columns:1fr 1fr;gap:3mm;margin-top:2mm">
  {ticks([f"<b>{sb[1]} of {sb_total:,} plain runs ({sb[2]}) ended 0, 0</b>: both threads read before either write was visible. No interleaving of the source allows that; the JMM does, because the program has a data race.",
          f"<b>With volatile: {sbv[1]} of {sbv_total:,}</b>. Volatile reads and writes are synchronisation actions, totally ordered (§17.4.4), so one write must come first and the other thread’s read must see it."], CJ)}
  {ticks(["<b>The result does not say whether the compiler or the CPU reordered the accesses.</b> The log shows jcstress ran the actors interpreted, with C1 and with C2, and with C2’s stress options (<code>-XX:+StressLCM</code>, <code>-XX:+StressGCM</code> …); the JMM allows 0, 0 for this racy program in every case.",
          f"<b>The machine:</b> {MACHINE['cpus']} CPUs" + (f" ({MACHINE['cpu']})" if MACHINE["cpu"] != "not recorded" else "") + "; jcstress pins each actor thread to its own CPU."], CJ)}
</div>
{src("JLS SE 21 §17.4.2–17.4.5", "jcstress 0.16 (org.openjdk.jcstress)", "OpenJDK 21 java/util/concurrent/package-info.java", "results: ci-logs-ops logs/jcstress.log")}
''', chapter=K10, color=CJ, bm="10 · Java Memory Model")

SF = dlog("staleflag.txt")
sf_plain = re.findall(r"^plain field:\s+(.+)$", SF, re.M)
sf_vol = re.findall(r"^volatile field:\s+(.+)$", SF, re.M)
sf_stuck = sum("still spinning" in s for s in sf_plain)
sf_vstop = sum(s == "stopped" for s in sf_vol)
stale, term = jrow("SpinTest", "STALE"), jrow("SpinTest", "TERMINATED")
racy, atomic = jrow("RacyCounterTest", "1"), jrow("AtomicCounterTest", "1")
page("jmm2", f'''
{sub(K10, "Visibility and lost updates", CJ)}
<p class="lede-s">Happens-before is also about <i>whether</i> a write is seen at all. A thread spinning on a plain field has no happens-before edge with the thread that sets it, and JLS §17.3 allows the loop to keep a value it read once: “The compiler is free to read the field <code>this.done</code> just once, and reuse the cached value in each execution of the loop.”</p>
<div class="two top" style="grid-template-columns:1.05fr 1fr;gap:3mm">
  {code(dsrc("jmm/StaleFlag.java", "  static String stops", "\n  }"), "StaleFlag.java — the loop runs 1 s, then the flag is set", cls="xs")}
  <div>
    {code(SF.strip(), "real output · 5 runs in CI", kind="plain", cls="xs out")}
    {ticks([f"<b>Plain field: {sf_stuck} of {len(sf_plain)} runs</b> still spinning 3 s after the flag was set, as §17.3 allows.",
            f"<b>Volatile: {sf_vstop} of {len(sf_vol)}</b> stopped. A write to a volatile field happens-before every subsequent read of that field (§17.4.5)."], CJ)}
  </div>
</div>
<h2>The same question, asked by jcstress</h2>
<div class="two top" style="grid-template-columns:0.85fr 1.15fr;gap:3mm">
  {code(csrc("SpinTest.java", "@JCStressTest"), "SpinTest.java — Mode.Termination", cls="xs")}
  <div>
    {jtable("SpinTest")}
    <p class="small" style="margin:1mm 0 2mm">With <code>volatile boolean ready</code>: <code>STALE</code> {jrow("SpinVolatileTest", "STALE")[1]} of {int(jrow("SpinVolatileTest", "STALE")[1].replace(",", "")) + int(jrow("SpinVolatileTest", "TERMINATED")[1].replace(",", "")):,}, declared forbidden.</p>
    {ticks([f"<b>Only {stale[1]} of {int(stale[1].replace(',', '')) + int(term[1].replace(',', '')):,} runs ({stale[2]}) got stuck.</b> StaleFlag, which let the loop run for 1 s before setting the flag, got stuck in every run.",
            f"<b>Lost updates</b>, from the guide’s own counter tests: <code>count++</code> on a plain field lost an update in {racy[2]} of {sum(int(r[1].replace(',', '')) for r in JCR['RacyCounterTest']):,} runs; <code>AtomicInteger</code> in {atomic[1]} of {sum(int(r[1].replace(',', '')) for r in JCR['AtomicCounterTest']):,}."], CJ)}
  </div>
</div>
<div class="two top" style="grid-template-columns:1fr 1fr;gap:3mm;margin-top:2mm">
  {ticks(["<b>Share mutable state through something that creates the edge:</b> <code>volatile</code>, an <code>Atomic*</code>, a lock, a concurrent collection, a future’s result, <code>Thread.start</code> / <code>join</code>.",
          "<b>Publish immutable objects through final fields</b> (JLS §17.5): a correctly constructed object’s final fields are seen initialised by every thread."], CJ)}
  {ticks([f"<b>The bad outcomes were rare in jcstress</b> ({stale[2]} stuck spins, {racy[2]} lost updates): a test that runs the code once will usually pass. jcstress runs it millions of times across compilation modes."], CJ)}
</div>
{src("JLS SE 21 §17.3, §17.4, §17.5", "jcstress 0.16: Mode.Termination, @Signal", "results: deepdive/logs/staleflag.txt; ci-logs-ops logs/jcstress.log")}
''', chapter=K10, color=CJ)
