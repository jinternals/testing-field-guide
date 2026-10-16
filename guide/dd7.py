"""Detail pages: when Nagle helps (ch 1), inside C2 (ch 6), inside the collectors (ch 7),
where thread stacks live (ch 8), what volatile compiles to (ch 10)."""
from dd_lib import *
import dd1, dd4, dd5

J21 = "OpenJDK 21"


def jmh_rows(text, cls):
    """{benchmark: (score, error, unit)} from a JMH result table."""
    out = {}
    for m in re.finditer(rf"{cls}\.(\w+)\s+avgt\s+\d+\s+([\d.]+)\s+±\s+([\d.]+)\s+(\S+/op)", text):
        out[m.group(1)] = (float(m.group(2)), float(m.group(3)), m.group(4))
    return out


# =====================================================================
# 1 · when Nagle helps, and what each setting does
# =====================================================================
SW = {}
if has("smallwrites.txt"):
    cork = None
    for line in dlog("smallwrites.txt").splitlines():
        m = re.match(r"tcp_autocorking (\d)", line)
        if m:
            cork = int(m.group(1))
            continue
        m = re.match(r"(.+?)\s{2,}(\d+) ms\s+data segments sent by the client\s+([\d,]+)$", line)
        if m and cork is not None:
            SW[(cork, m.group(1).strip())] = (int(m.group(2)), int(m.group(3).replace(",", "")))

RULES = '''/* Return false, if packet can be sent now without violation Nagle's rules:
 * 1. It is full sized. (provided by caller in %partial bool)
 * 2. Or it contains FIN. (already checked by caller)
 * 3. Or TCP_CORK is not set, and TCP_NODELAY is set.
 * 4. Or TCP_CORK is not set, and all sent packets are ACKed.
 *    With Minshall's modification: all sent small packets are ACKed.
 */'''

SETTINGS = [
    ("<code>TCP_NODELAY</code>", "socket", "<code>Socket.setTcpNoDelay</code>, <code>StandardSocketOptions.TCP_NODELAY</code> (default false)", "rule 3: a small segment may go out while others are unacknowledged"),
    ("<code>TCP_QUICKACK</code>", "socket, Linux", "<code>jdk.net.ExtendedSocketOptions.TCP_QUICKACK</code>", "the receiver ACKs at once; “this option is not permanent” (its Javadoc) — chapter 1 set it before every read"),
    ("<code>TCP_CORK</code>", "socket, Linux", "not in JDK 21’s <code>ExtendedSocketOptions</code>", "holds partial segments until uncorked (rule 3 and 4 require it unset)"),
    ("<code>tcp_autocorking</code>", "sysctl, default 1", "—", "coalesces consecutive small writes “if at least one prior packet for the flow is waiting in Qdisc queues or device transmit queue”"),
]

sw_html = PENDING
if SW:
    names = ["Nagle on (default)", "TCP_NODELAY", "BufferedOutputStream, one flush"]
    rows = []
    for c in (1, 0):
        for n in names:
            if (c, n) in SW:
                ms, segs = SW[(c, n)]
                rows.append((n, str(c), f"{ms}", f"{segs:,}"))
    on, nd, buf = SW[(1, names[0])], SW[(1, names[1])], SW[(1, names[2])]
    nd0, on0 = SW.get((0, names[1])), SW.get((0, names[0]))
    notes = [f"<b>Nagle on</b>: {on[1]:,} data segments for 10,000 writes — bytes waited while earlier ones were unacknowledged, then went together."]
    if nd0:
        notes.append(f"<b>TCP_NODELAY, autocorking off</b>: {nd0[1]:,} data segments" + (" — one per write." if nd0[1] >= 9_900 else "."))
    notes.append(f"<b>TCP_NODELAY, autocorking on</b> (the default): {nd[1]:,}" + (" — <code>tcp_autocorking</code> merged writes while earlier packets were still queued." if nd0 and nd[1] < 0.9 * nd0[1] else "."))
    notes.append(f"<b>One buffered write</b>: {buf[1]:,} segments in {buf[0]} ms.")
    sw_html = f'''<div class="two top" style="grid-template-columns:1.15fr 1fr;gap:3mm"><div>{table(["Writer", "tcp_autocorking", "ms", "data segments sent"], rows, "xs")}
    <p class="small muted" style="margin:1mm 0">SmallWrites.java · the client socket’s <code>data_segs_out</code> counter (<code>ss -ti</code>) · {RUNNER}</p></div>
    {ticks(notes, CN)}</div>'''

page("nagle3", f'''
{sub(dd1.K, "When Nagle helps, and what each setting changes", CN)}
<p class="lede-s">Nagle’s algorithm trades a delay for fewer, fuller segments. Chapter 1 measured its cost in a request/response exchange; this page measures a one-way stream of small writes and lists the settings that change the behaviour.</p>
{code(RULES, "Linux 6.17 net/ipv4/tcp_output.c — the comment above tcp_nagle_check()", kind="plain", cls="xs out")}
<p class="small" style="margin-top:1mm">“Full sized” means one maximum segment size (MSS). Rule 4 with Minshall’s modification: a small segment may go out once every earlier <i>small</i> segment is acknowledged, even while full-sized ones are in flight (<code>tcp_minshall_check</code>).</p>
<h2>Measured: 10,000 one-byte writes, no reply</h2>
{sw_html}
<h2>The settings</h2>
{table(["Setting", "Where it is set; from Java", "Effect"], [(a, f"{b}; {c}" if c != "—" else b, d) for a, b, c, d in SETTINGS], "xs")}
<div class="two top" style="grid-template-columns:1fr 1fr;gap:3mm;margin-top:2mm">
  {ticks(["<b>Set <code>TCP_NODELAY</code></b> when a request or response is written in more than one <code>write()</code> and the peer waits for the whole message — chapter 1’s case: 41 ms per exchange with Nagle on, under 0.2 ms with it off.",
          "<b>Leave Nagle on</b> for a one-way stream of small writes where no reply is awaited: here it cut the segment count."], CN)}
  {ticks(["<b>Prefer writing each message once</b> (build it in a buffer): then neither Nagle nor <code>TCP_NODELAY</code> matters, and the segment count is lowest."], CN)}
</div>
{src("Linux 6.17 net/ipv4/tcp_output.c (tcp_nagle_check, tcp_minshall_check), include/net/tcp.h (TCP_NAGLE_OFF/CORK/PUSH)", "Documentation/networking/ip-sysctl.rst (tcp_autocorking)", f"{J21} jdk/net/ExtendedSocketOptions.java, java/net/StandardSocketOptions.java", "results: deepdive/logs/smallwrites.txt")}
''', chapter=dd1.K, color=CN)

# =====================================================================
# 6 · inside C2
# =====================================================================
FL = {}
if has("jit-flags.txt"):
    FL = dict(re.findall(r"\s(\w+)\s+=\s+(\S+)", dlog("jit-flags.txt")))
LIMITS = [(f"<code>{k}</code>", FL.get(k, "?"), d) for k, d in [
    ("MaxInlineSize", "“The maximum bytecode size of a method to be inlined by high tier compiler”"),
    ("FreqInlineSize", "“The maximum bytecode size of a frequent method to be inlined”"),
    ("InlineSmallCode", "“Only inline already compiled methods if their code size is less than this”"),
    ("MaxInlineLevel", "“maximum number of nested calls that are inlined by high tier compiler”"),
    ("TypeProfileWidth", "“Number of receiver types to record in call/cast profile”"),
    ("TypeProfileMajorReceiverPercent", "“% of major receiver type to all profiled receivers”"),
    ("DoEscapeAnalysis", "“Perform escape analysis”"),
    ("EliminateAllocations", "“Use escape analysis to eliminate allocations”")]]

IN, ALLOC = {}, {}
if has("jmh-inline.txt"):
    t = dlog("jmh-inline.txt")
    IN = jmh_rows(t, "InliningBench")
    for m in re.finditer(r"InliningBench\.(\w+)[:·]gc\.alloc\.rate\.norm\s+avgt\s+\d+\s+(≈\s*\S+|[\d.]+)", t):
        v = m.group(2)
        ALLOC[m.group(1)] = 0.0 if v.startswith("≈") else float(v)
INL = ""
if has("jit-inlining.txt"):
    lines, seen = [], 0
    for l in dlog("jit-inlining.txt").splitlines():
        if re.search(r"CallSites::fourTypes \(", l):
            seen += 1
        lines.append(l.rstrip())
        if seen and "virtual call" in l:
            break
    keep = [l for l in lines if "@ 25" in l or re.search(r"CallSites::(oneType|fourTypes) ", l)]
    INL = "\n".join(re.sub(r"\s{2,}", "  ", l.strip()) for l in keep)
INL_OK = "inline (hot)" in INL and "virtual call" in INL and "fourTypes" in INL
INL_NOTE = ("In <code>oneType</code> the call at bytecode 25 became the inlined <code>A::area</code>; in <code>fourTypes</code> the same call stayed a <code>virtual call</code> to <code>Shape::area</code>." if INL_OK else "")

jit_html = PENDING
if IN:
    label = {"callInlined": "tiny static method, inlined", "callNotInlined": "same method, <code>DONT_INLINE</code>",
             "types1": "call site saw 1 type (1,024 calls)", "types2": "call site saw 2 types", "types4": "call site saw 4 types",
             "allocation": "<code>new Point</code> that never escapes", "allocationNoEscapeAnalysis": "same, <code>-XX:-DoEscapeAnalysis</code>"}
    rows = [(label[k], f"{IN[k][0]:.3f}", f"± {IN[k][1]:.3f}", f"{ALLOC[k]:.0f}" if k in ALLOC else "–") for k in label if k in IN]
    t1, t2, t4 = IN["types1"][0], IN["types2"][0], IN["types4"][0]
    jit_html = f'''<div class="two top" style="grid-template-columns:1.1fr 1fr;gap:3mm"><div>{table(["Benchmark", "ns/op", "error", "bytes allocated / op"], rows, "xs")}
    <p class="small muted" style="margin-top:1mm">InliningBench.java · JMH 1.37 with <code>-prof gc</code> (<code>gc.alloc.rate.norm</code>) · each benchmark in its own JVM · {RUNNER}</p></div>
    {ticks([f"<b>Not inlining a two-int addition</b> cost {IN['callNotInlined'][0] - IN['callInlined'][0]:.2f} ns per call.",
            f"<b>The call site with 4 receiver types</b> took {t4 / t1:.1f}× as long as with 1 ({t4:.0f} against {t1:.0f} ns for 1,024 calls); 2 types: {t2:.0f} ns.",
            f"<b>Escape analysis</b>: the non-escaping <code>Point</code> allocated {ALLOC.get('allocation', 0):.0f} bytes per call; with it switched off, {ALLOC.get('allocationNoEscapeAnalysis', 0):.0f}."], CJ)}</div>'''

page("jit3", f'''
{sub(dd4.K6, "Inside C2: inlining, receiver types, escape analysis", CJ)}
<p class="lede-s">Most of C2’s speed comes from three things it does with the interpreter’s profile: copying small called methods into the caller (inlining), betting on the receiver types a call site has seen, and removing allocations of objects that never leave a method (escape analysis). Each is controlled by flags; the values below are the runner’s.</p>
<div class="two top" style="grid-template-columns:1fr 1fr;gap:3mm">
  <div class="mech" style="--accent:{CJ}">
    <h3>A call site’s receiver types — <code>doCall.cpp</code></h3>
    <p>The profile records up to <code>TypeProfileWidth</code> receiver classes per call site. C2 then generates:</p>
    {ticks(["<b>1 type</b>: a type check and the inlined method; another type takes an <i>uncommon trap</i> and the method is deoptimized.",
            "<b>2 types</b> (<code>UseBimorphicInlining</code>): two checks, both methods inlined.",
            "<b>More</b>: the most frequent type inlined only if it reaches <code>TypeProfileMajorReceiverPercent</code> of calls; otherwise a virtual call."], CJ)}
  </div>
  <div>{code(INL or "(waiting for the next CI run)", "-XX:+PrintCompilation -XX:+PrintInlining · CallSites.java (real output, start)", kind="plain", cls="xs out")}
  <p class="small" style="margin-top:1mm">Run with C2 only (<code>-XX:-TieredCompilation</code>), so each inlining line follows its own method’s compile line. {INL_NOTE}</p></div>
</div>
{table(["Flag", "Runner", "Description in c2_globals.hpp / globals.hpp"], LIMITS, "xs")}
<h2>Measured</h2>
{jit_html}
{src(f"{J21} hotspot/share/opto/c2_globals.hpp, runtime/globals.hpp, opto/doCall.cpp (Compile::call_generator)", "JMH 1.37 CompilerControl, GCProfiler", "results: deepdive/logs/jmh-inline.txt, jit-inlining.txt, jit-flags.txt")}
''', chapter=dd4.K6, color=CJ)

# =====================================================================
# 7 · inside the collectors
# =====================================================================
REG = re.findall(r"-Xmx(\w+)\s+Heap Region Size: (\S+)", dlog("gc-init.txt")) if has("gc-init.txt") else []
BAR = {}
if has("jmh-barrier.txt"):
    cur = None
    for line in dlog("jmh-barrier.txt").splitlines():
        if line.startswith("## "):
            cur = "Parallel" if "Parallel" in line else ("G1" if "G1" in line else "ZGC")
            continue
        m = re.match(r"BarrierBench\.(\w+)\s+avgt\s+\d+\s+([\d.]+)\s+±\s+([\d.]+)", line)
        if m and cur:
            BAR.setdefault(cur, {})[m.group(1)] = float(m.group(2))
BIG = {}
for name in ("G1", "ZGC"):
    if has(f"gc-{name}-4g.txt"):
        t = dlog(f"gc-{name}-4g.txt")
        up = float(re.search(r"measuring from uptime ([\d.]+) s", t).group(1))
        m = re.search(r"p99\.9 ([\d.]+)\s+max ([\d.]+) ms", t)
        ev = dd4.pauses_of(f"{name}-4g", up)
        BIG[name] = dict(p999=float(m.group(1)), max=float(m.group(2)), pauses=[e[2] for e in ev], full=sum(1 for e in ev if e[1] == "Full"))

reg_html = table(["Heap (-Xmx)", "G1 region size"], [(f"-Xmx{h}", r) for h, r in REG], "xs") if REG else PENDING
bar_html = PENDING
if BAR:
    rows = [(op, *(f"{BAR[g][op]:.2f}" if op in BAR.get(g, {}) else "–" for g in ("Parallel", "G1", "ZGC")))
            for op in ("loadRefs", "storeRefs", "storeInts")]
    bar_html = f'''{table(["4,096 accesses (µs)", "Parallel", "G1", "generational ZGC"], rows, "xs")}
    <p class="small muted" style="margin-top:1mm">BarrierBench.java · JMH, <code>-Xms1g -Xmx1g</code> and the collector’s flag · {RUNNER}</p>
    {ticks([f"<b>Reference loads</b>: {BAR['ZGC']['loadRefs']:.2f} µs with ZGC’s load barrier against {BAR['G1']['loadRefs']:.2f} (G1) and {BAR['Parallel']['loadRefs']:.2f} (Parallel), which have none.",
            f"<b>Reference stores</b>: {BAR['Parallel']['storeRefs']:.2f} (Parallel), {BAR['G1']['storeRefs']:.2f} (G1), {BAR['ZGC']['storeRefs']:.2f} µs (ZGC). Int stores, which no collector intercepts: {min(BAR[g]['storeInts'] for g in BAR):.2f}–{max(BAR[g]['storeInts'] for g in BAR):.2f} µs.",
            "<b>The collectors differ in more than barriers</b> — heap layout and object placement too — so these numbers describe this loop on this machine, not a barrier cost in isolation."], CJ)}'''
big_html = PENDING
if BIG and "G1" in BIG and "ZGC" in BIG:
    rows = []
    for name, small in (("G1", dd4.GC["G1"]), ("ZGC", dd4.GC["ZGC"])):
        b = BIG[name]
        rows.append((name, "1 GB", f"{small['p999']:.3f}", f"{max(small['pauses']):.3f}", str(sum(1 for e in small['events'] if e[1] == 'Full'))))
        rows.append((name, "4 GB", f"{b['p999']:.3f}", f"{max(b['pauses']):.3f}", str(b["full"])))
    big_html = f'''{table(["Collector", "Heap", "p99.9 ms", "longest pause ms", "full GCs"], rows, "xs")}
    <p class="small muted" style="margin-top:1mm">Chapter 7’s workload (≈ 400 MB live) with a 1 GB and a 4 GB heap.</p>'''

page("gc3", f'''
{sub(dd4.K7, "Inside the collectors: regions, cards and barriers", CJ)}
<div class="two top" style="grid-template-columns:1fr 1fr;gap:3mm">
  <div class="mech" style="--accent:{CJ}">
    <h3>G1: regions and remembered sets</h3>
    <p>The heap is divided into equal regions. Without <code>G1HeapRegionSize</code>, the size is the heap divided by 2,048, kept between 1 MB and 32 MB and rounded up to a power of two (<code>HeapRegion::setup_heap_region_size</code>). An object of at least half a region is <i>humongous</i> and gets regions of its own (<code>humongous_threshold_for</code>).</p>
    <p style="margin-top:1mm">To collect some regions without scanning the rest, “each heap region has a rem set that records the external heap references into it” (<code>g1RemSet.hpp</code>). After a reference store, G1’s write barrier marks the 512-byte card (<code>GCCardSizeInBytes</code>) that holds the updated field; the cards are later processed into the remembered sets. Before the store, a second barrier logs the old value for snapshot-at-the-beginning marking (<code>g1BarrierSet.hpp</code>).</p>
  </div>
  <div class="mech" style="--accent:{CJ}">
    <h3>ZGC: coloured pointers and load barriers</h3>
    <p>Generational ZGC keeps metadata in the low bits of each stored reference (<code>zAddress.hpp</code>): remapped, marked-young, marked-old, finalizable and remembered bits. Its load barrier, from <code>zBarrier.hpp</code>:</p>
    <p class="rfc">“The load barriers of ZGC check if a loaded value is safe to expose or not, and then shifts the pointer to remove metadata bits, such that it points to mapped memory.”</p>
    <p>In compiled code the check and the shift are one shift instruction; a pointer with a bad colour takes a slow path that fixes it — for example, finds the object’s new address after relocation. This is how objects can move while the application runs.</p>
  </div>
</div>
<div class="two top" style="grid-template-columns:0.6fr 1.4fr;gap:3mm;margin-top:2mm">
  <div><h2 style="margin-top:0">Measured: region size</h2>{reg_html}<p class="small muted" style="margin-top:1mm"><code>-Xlog:gc+init</code></p></div>
  <div><h2 style="margin-top:0">Measured: the cost of barriers</h2>{bar_html}</div>
</div>
<h2>Measured: pauses with a bigger heap</h2>
{big_html}
{src(f"{J21} gc/g1/heapRegion.cpp, heapRegionBounds.hpp, g1CollectedHeap.hpp, g1RemSet.hpp, g1BarrierSet.hpp; gc/shared/gc_globals.hpp (GCCardSizeInBytes); gc/z/zAddress.hpp, zBarrier.hpp", "results: deepdive/logs/gc-init.txt, jmh-barrier.txt, gc-G1-4g.*, gc-ZGC-4g.*")}
''', chapter=dd4.K7, color=CJ)

# =====================================================================
# 8 · where a blocked thread keeps its stack
# =====================================================================
STACKCHUNK = """package jdk.internal.vm;

public final class StackChunk {
    public static void init() {}

    private StackChunk parent;
    private int size;    // in words
    private int sp;      // in words
    private int bottom;  // in words

    // The stack itself is appended here by the VM, as well as some injected fields

    public StackChunk parent() { return parent; }
    public boolean isEmpty()   { return sp == bottom; }
}"""

VM = {}
if has("vt-memory.txt"):
    for block in re.split(r"(?m)^(?=(?:platform|virtual) threads:)", dlog("vt-memory.txt")):
        m = re.match(r"(platform|virtual) threads", block)
        if not m:
            continue
        d = {}
        d["heap"] = int(re.search(r"heap used after GC\s+([\d,]+) KB", block).group(1).replace(",", ""))
        d["rss"] = int(re.search(r"VmRSS: (\d+) kB", block).group(1))
        t = re.search(r"Thread \(reserved=(\d+)KB, committed=(\d+)KB\)", block)
        d["nmt_res"], d["nmt_com"] = (int(t.group(1)), int(t.group(2))) if t else (None, None)
        th = re.search(r"\(threads #(\d+)\)", block)
        d["threads"] = int(th.group(1)) if th else None
        sc = re.search(r"(\d+)\s+(\d+)\s+jdk\.internal\.vm\.StackChunk", block)
        d["chunks"], d["chunk_bytes"] = (int(sc.group(1)), int(sc.group(2))) if sc else (0, 0)
        VM[m.group(1)] = d

vm_html = PENDING
if "platform" in VM and "virtual" in VM:
    p_, v_ = VM["platform"], VM["virtual"]
    mb = lambda kb: f"{kb / 1024:,.0f} MB"
    rows = [("OS threads (NMT)", f"{p_['threads']:,}", f"{v_['threads']:,}"),
            ("thread stacks reserved (NMT)", mb(p_["nmt_res"]), mb(v_["nmt_res"])),
            ("thread stacks committed (NMT)", mb(p_["nmt_com"]), mb(v_["nmt_com"])),
            ("<code>StackChunk</code> objects on the heap", f"{p_['chunks']:,}", f"{v_['chunks']:,}"),
            ("their size", mb(p_["chunk_bytes"] / 1024), mb(v_["chunk_bytes"] / 1024)),
            ("heap used after GC", mb(p_["heap"]), mb(v_["heap"])),
            ("process resident memory (VmRSS)", mb(p_["rss"]), mb(v_["rss"]))]
    per = v_["chunk_bytes"] / max(v_["chunks"], 1)
    vm_html = f'''{table(["10,000 threads blocked 20 frames deep", "platform", "virtual"], rows, "xs")}
    <p class="small muted" style="margin-top:1mm">ThreadMemory.java with <code>-XX:NativeMemoryTracking=summary</code>; it runs <code>jcmd VM.native_memory summary</code> and <code>jcmd GC.class_histogram</code> on itself · {RUNNER}</p>
    {ticks([f"<b>Platform threads</b>: {p_['threads']:,} OS threads, {mb(p_['nmt_res'])} of stack address space reserved — {p_['nmt_res'] / max(p_['threads'], 1):,.0f} KB each, the <code>ThreadStackSize</code> of {FL.get('ThreadStackSize', '?')} KB — of which {mb(p_['nmt_com'])} committed.",
            f"<b>Virtual threads</b>: {v_['chunks']:,} <code>StackChunk</code> objects, {per:,.0f} bytes each on average, on the Java heap; the process had {v_['threads']} OS threads.",
            f"<b>Resident memory</b>: {mb(p_['rss'])} against {mb(v_['rss'])}."], CJ)}'''

page("vt2", f'''
{sub(dd4.K8, "Where a blocked thread keeps its stack", CJ)}
<p class="lede-s">A platform thread is an OS thread with its own stack, reserved when the thread starts. A virtual thread that blocks is unmounted: its frames are copied off the carrier’s stack into an object on the Java heap, and copied back when it continues. Both are visible from outside the program.</p>
<div class="two top" style="grid-template-columns:1fr 1fr;gap:3mm">
  <div class="mech" style="--accent:{CJ}">
    <h3>Platform thread: <code>ThreadStackSize</code></h3>
    <p>On Linux x86-64 the default Java thread stack is <b>1024 KB</b> (<code>globals_linux_x86.hpp</code>: <code>define_pd_global(intx, ThreadStackSize, 1024)</code>); the runner reports <code>ThreadStackSize = {FL.get("ThreadStackSize", "?")}</code>. Native Memory Tracking counts it as <i>reserved</i>; only pages the thread touches are <i>committed</i>.</p>
  </div>
  <div>{code(STACKCHUNK, f"{J21} java.base jdk/internal/vm/StackChunk.java (complete, without the licence header)", cls="xs wrap")}</div>
</div>
<h2>Measured: 10,000 blocked threads</h2>
<div class="two top" style="grid-template-columns:1.25fr 1fr;gap:3mm">
  <div>{vm_html}</div>
  {code(dsrc("vt/ThreadMemory.java", "  static void deep(int depth)", "\n  }"), "ThreadMemory.java — each thread blocks 20 frames deep", cls="xs")}
</div>
{src(f"{J21} hotspot/os_cpu/linux_x86/globals_linux_x86.hpp (ThreadStackSize), java.base jdk/internal/vm/StackChunk.java, Continuation.java", "Native Memory Tracking (services/nmtDCmd.hpp)", "results: deepdive/logs/vt-memory.txt")}
''', chapter=dd4.K8, color=CJ)

# =====================================================================
# 10 · what volatile compiles to on x86-64
# =====================================================================
FB = jmh_rows(dlog("jmh-fence.txt"), "FenceBench") if has("jmh-fence.txt") else {}
AD = '''instruct membar_acquire() %{
  match(MemBarAcquire);
  match(LoadFence);
  format %{ "MEMBAR-acquire ! (empty encoding)" %}

instruct membar_release() %{
  match(MemBarRelease);
  match(StoreFence);
  format %{ "MEMBAR-release ! (empty encoding)" %}

instruct membar_volatile(rFlagsReg cr) %{
  match(MemBarVolatile);
  format %{
    $$emit$$"lock addl [rsp + #0], 0\\t! membar_volatile"
  %}
  ins_encode %{
    __ membar(Assembler::StoreLoad);
  %}'''

fb_html = PENDING
if FB:
    label = [("plainStore", "plain field: <code>plain++</code>"), ("releaseStore", "<code>setRelease</code> (release store) + <code>plain++</code>"),
             ("volatileStore", "volatile store + <code>plain++</code>"), ("plainLoad", "plain load"), ("volatileLoad", "volatile load"),
             ("atomicIncrement", "<code>AtomicInteger.incrementAndGet</code>"), ("synchronizedIncrement", "<code>synchronized</code> + <code>++</code>, uncontended")]
    rows = [(l, f"{FB[k][0]:.3f}", f"± {FB[k][1]:.3f}") for k, l in label if k in FB]
    fb_html = f'''{table(["One thread, no contention", "ns/op", "error"], rows, "xs")}
    <p class="small muted" style="margin-top:1mm">FenceBench.java · JMH 1.37 · {RUNNER}</p>
    {ticks([f"<b>The volatile store</b> added {FB['volatileStore'][0] - FB['plainStore'][0]:.2f} ns to the plain increment: the <code>lock addl</code> after it.",
            f"<b>The release store</b> added {FB['releaseStore'][0] - FB['plainStore'][0]:.2f} ns" + (", consistent with a barrier that emits no instruction on x86-64." if FB['releaseStore'][0] - FB['plainStore'][0] < 0.5 else ", although its barrier emits no instruction on x86-64; this benchmark does not show where that time goes."),
            f"<b>The volatile load</b> took {FB['volatileLoad'][0]:.3f} ns against {FB['plainLoad'][0]:.3f} ns for a plain load: on x86-64 the acquire barrier is empty.",
            f"<b>The atomic increment</b> (a <code>lock</code>-prefixed instruction) took {FB['atomicIncrement'][0]:.2f} ns; an uncontended <code>synchronized</code> block {FB['synchronizedIncrement'][0]:.2f} ns."], CJ)}'''

page("jmm3", f'''
{sub(dd5.K10, "What volatile compiles to on x86-64", CJ)}
<p class="lede-s">The memory model says what must be visible; the JIT decides how. For each volatile access C2 inserts memory-barrier nodes, and each CPU back end turns them into instructions — or into nothing, where the CPU already gives the ordering.</p>
<div class="two top" style="grid-template-columns:1fr 1fr;gap:3mm">
  <div class="mech" style="--accent:{CJ}">
    <h3>Where C2 puts the barriers — <code>barrierSetC2.cpp</code></h3>
    {ticks(["<b>Volatile store</b>: <code>MemBarRelease</code> before it and <code>MemBarVolatile</code> after it, on CPUs that are multi-copy atomic (x86 defines <code>CPU_MULTI_COPY_ATOMIC</code>).",
            "<b>Volatile load</b>: <code>MemBarAcquire</code> after it.",
            "<b>Release store</b> (<code>VarHandle.setRelease</code>): <code>MemBarRelease</code> only."], CJ)}
    <p style="margin-top:1mm">An atomic add such as <code>getAndAdd</code> becomes <code>lock xadd</code> (<code>x86_64.ad</code>). <code>synchronized</code> runs with <code>LockingMode = {FL.get("LockingMode", "?")}</code> on the runner; <code>globals.hpp</code> documents 1 as “monitors &amp; legacy stack-locking (LM_LEGACY, default)”.</p>
  </div>
  {code(AD, f"{J21} hotspot/cpu/x86/x86_64.ad (excerpts)", kind="plain", cls="xs out")}
</div>
<div class="two top" style="grid-template-columns:1.1fr 1fr;gap:3mm;margin-top:2mm">
  <div><h2 style="margin-top:0">Measured</h2>{fb_html}</div>
  {code(dsrc("jmm/FenceBench.java", "  @Benchmark\n  public void plainStore()", "      locked++;\n    }\n  }"), "FenceBench.java", cls="xs")}
</div>
{src(f"{J21} hotspot/share/gc/shared/c2/barrierSetC2.cpp, cpu/x86/x86_64.ad, cpu/x86/globalDefinitions_x86.hpp, share/utilities/globalDefinitions.hpp, runtime/globals.hpp (LockingMode)", "results: deepdive/logs/jmh-fence.txt, jit-flags.txt")}
''', chapter=dd5.K10, color=CJ)
