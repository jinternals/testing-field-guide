"""Sources and index of the deep-dive book."""
from dd_lib import *

J21 = "https://github.com/openjdk/jdk21u/blob/master/src/"
LNX = "https://github.com/torvalds/linux/blob/v6.17/"


def a(url, text):
    return f'<a href="{url}">{text}</a>'


SOURCES = [
    ("Standards and specifications", [
        a("https://www.rfc-editor.org/rfc/rfc9293", "RFC 9293") + " — Transmission Control Protocol (2022): Nagle (§3.7.4), delayed ACK (§3.8.6.3), TIME-WAIT and MSL (§3.4.2–3.4.3), states (§3.3.2)",
        a("https://www.rfc-editor.org/rfc/rfc896", "RFC 896") + " — J. Nagle, Congestion Control in IP/TCP Internetworks (1984)",
        a("https://www.rfc-editor.org/rfc/rfc5737", "RFC 5737") + " — IPv4 address blocks reserved for documentation (192.0.2.0/24)",
        a("https://docs.oracle.com/javase/specs/jls/se21/html/jls-17.html", "JLS SE 21, chapter 17") + " — threads and locks; the memory model (§17.3–17.5)",
        a("https://openjdk.org/jeps/439", "JEP 439") + " Generational ZGC · " + a("https://openjdk.org/jeps/444", "JEP 444") + " Virtual threads · "
        + a("https://openjdk.org/jeps/474", "JEP 474") + " ZGC generational by default · " + a("https://openjdk.org/jeps/490", "JEP 490") + " non-generational ZGC removed · "
        + a("https://openjdk.org/jeps/491", "JEP 491") + " synchronized without pinning",
    ]),
    ("Linux 6.17 source and documentation", [
        a(LNX + "include/net/tcp.h", "include/net/tcp.h") + " — TCP_DELACK_MIN/MAX, TCP_MAX_QUICKACKS, TCP_TIMEWAIT_LEN",
        a(LNX + "net/ipv4/tcp_input.c", "net/ipv4/tcp_input.c") + " (quick ACKs, pingpong mode) · " + a(LNX + "net/ipv4/tcp_output.c", "net/ipv4/tcp_output.c") + " (tcp_event_data_sent) · " + a(LNX + "net/ipv4/tcp.c", "net/ipv4/tcp.c") + " (zero-linger close)",
        a("https://docs.kernel.org/networking/ip-sysctl.html", "Documentation/networking/ip-sysctl.rst") + " — tcp_pingpong_thresh, tcp_tw_reuse, tcp_fin_timeout, tcp_syn_retries, ip_local_port_range",
        a("https://docs.kernel.org/admin-guide/cgroup-v2.html", "Documentation/admin-guide/cgroup-v2.rst") + " — cpu.max, cpu.stat, memory.max",
    ]),
    ("OpenJDK 21 source", [
        "java.net.http: " + ", ".join(a(J21 + "java.net.http/share/classes/" + p, n) for p, n in [
            ("jdk/internal/net/http/PlainHttpConnection.java", "PlainHttpConnection"), ("jdk/internal/net/http/MultiExchange.java", "MultiExchange"),
            ("jdk/internal/net/http/ResponseTimerEvent.java", "ResponseTimerEvent"), ("module-info.java", "module-info (keep-alive 30 s)")]),
        "java.base: " + ", ".join(a(J21 + "java.base/share/classes/" + p, n) for p, n in [
            ("java/net/StandardSocketOptions.java", "StandardSocketOptions"), ("java/net/Socket.java", "Socket"), ("java/net/URLConnection.java", "URLConnection"),
            ("java/lang/VirtualThread.java", "VirtualThread"), ("java/lang/Object.java", "Object"), ("java/io/FileInputStream.java", "FileInputStream"),
            ("jdk/internal/misc/Blocker.java", "Blocker"), ("java/util/concurrent/ForkJoinPool.java", "ForkJoinPool"), ("java/util/concurrent/package-info.java", "java.util.concurrent package-info"), ("jdk/internal/vm/Continuation.java", "Continuation"), ("sun/nio/ch/NioSocketImpl.java", "NioSocketImpl"), ("jdk/internal/vm/StackChunk.java", "StackChunk")]),
        "jdk.httpserver " + a(J21 + "jdk.httpserver/share/classes/sun/net/httpserver/ServerConfig.java", "ServerConfig") + " · jdk.net "
        + a(J21 + "jdk.net/share/classes/jdk/net/ExtendedSocketOptions.java", "ExtendedSocketOptions") + " · jdk.jfr "
        + a(J21 + "jdk.jfr/share/conf/jfr/default.jfc", "default.jfc"),
        "HotSpot: " + ", ".join(a(J21 + "hotspot/" + p, n) for p, n in [
            ("share/compiler/compilationPolicy.hpp", "compilationPolicy.hpp"), ("share/compiler/compileTask.cpp", "compileTask.cpp"),
            ("share/runtime/os.cpp", "os.cpp"), ("share/gc/shared/gcConfig.cpp", "gcConfig.cpp"), ("share/gc/shared/gc_globals.hpp", "gc_globals.hpp"),
            ("share/runtime/arguments.cpp", "arguments.cpp"), ("share/gc/shared/workerPolicy.cpp", "workerPolicy.cpp"),
            ("os/linux/cgroupUtil_linux.cpp", "cgroupUtil_linux.cpp"), ("os/linux/globals_linux.hpp", "globals_linux.hpp"), ("share/code/nmethod.cpp", "nmethod.cpp"), ("share/gc/z/zDriver.cpp", "zDriver.cpp"), ("share/memory/allocation.hpp", "allocation.hpp"), ("share/services/nmtDCmd.hpp", "nmtDCmd.hpp"), ("share/opto/c2_globals.hpp", "c2_globals.hpp"), ("share/opto/doCall.cpp", "doCall.cpp"),
            ("share/gc/g1/heapRegion.cpp", "heapRegion.cpp"), ("share/gc/g1/g1RemSet.hpp", "g1RemSet.hpp"), ("share/gc/g1/g1BarrierSet.hpp", "g1BarrierSet.hpp"),
            ("share/gc/z/zAddress.hpp", "zAddress.hpp"), ("share/gc/z/zBarrier.hpp", "zBarrier.hpp"), ("share/gc/shared/c2/barrierSetC2.cpp", "barrierSetC2.cpp"),
            ("cpu/x86/x86_64.ad", "x86_64.ad"), ("os_cpu/linux_x86/globals_linux_x86.hpp", "globals_linux_x86.hpp")]),
    ]),
    ("Documentation", [
        a("https://docs.oracle.com/en/java/javase/21/gctuning/garbage-first-g1-garbage-collector1.html", "Java SE 21 HotSpot GC Tuning Guide") + " — the G1 cycle, evacuation failure, full GC; “Available Collectors”",
        a("https://docs.oracle.com/en/java/javase/21/docs/api/java.net.http/java/net/http/HttpClient.Builder.html", "HttpClient.Builder") + " and "
        + a("https://docs.oracle.com/en/java/javase/21/docs/api/java.net.http/java/net/http/HttpRequest.Builder.html", "HttpRequest.Builder") + " Javadoc — connect and request timeouts",
        a("https://github.com/brettwooldridge/HikariCP/wiki/About-Pool-Sizing", "HikariCP wiki, “About Pool Sizing”") + " · J. D. C. Little, “A Proof for the Queuing Formula: L = λW”, Operations Research 9(3), 1961",
    ]),
    ("Apache Kafka 4.3.1 client source", [
        ", ".join(a("https://github.com/apache/kafka/blob/4.3.1/clients/src/main/java/org/apache/kafka/clients/" + p, n) for p, n in [
            ("producer/ProducerConfig.java", "ProducerConfig"), ("consumer/ConsumerConfig.java", "ConsumerConfig"),
            ("consumer/KafkaConsumer.java", "KafkaConsumer"), ("CommonClientConfigs.java", "CommonClientConfigs")]) + " — defaults and documentation of every setting the chapter uses",
    ]),
    ("Libraries (source, default branch or named version)", [
        "Tomcat SocketProperties · Jetty 12.0 ServerConnector · Netty 4.1 DefaultSocketChannelConfig, MultithreadEventLoopGroup",
        "pgjdbc PGProperty · HikariCP HikariConfig · Lettuce SocketOptions, RedisURI · Kafka Selector, ProducerConfig",
    ]),
    ("Tools", [
        a("https://github.com/openjdk/jmh", "JMH 1.37") + " · " + a("https://github.com/openjdk/jcstress", "jcstress 0.16") + " · "
        + a("https://github.com/HdrHistogram/HdrHistogram", "HdrHistogram") + " (recordValueWithExpectedInterval) · " + a("https://github.com/giltene/wrk2", "wrk2")
        + " · " + a("https://grafana.com/docs/k6/latest/using-k6/scenarios/concepts/open-vs-closed/", "k6, open and closed models") + " · "
        + a("https://docs.gatling.io/reference/script/core/injection/", "Gatling, injection profiles"),
    ]),
    ("The evidence in this repository", [
        "Experiments: <code>deepdive/src/main/java/deep/</code> and <code>concurrency/src/main/java/shop/</code> (jcstress) · runner script <code>deepdive/run.sh</code>",
        "Logs: branch <code>ci-logs-deepdive</code> (<code>logs/</code>) and <code>ci-logs-ops</code> (<code>logs/jcstress.log</code>), rewritten on every push to main",
    ]),
]
src_html = "".join(f'<h2>{h}</h2><ul class="ticks tight" style="--tick:#0F172A">' + "".join(f"<li>{i}</li>" for i in items) + "</ul>" for h, items in SOURCES)
page("dsources", f'''
{sub("Back matter", "Sources", "#0F172A")}
<p class="lede-s">Everything this book relies on for how things work. Measured results come from the logs listed last.</p>
{src_html}
''', chapter="Sources", color="#0F172A", bm="Sources")

IDX = {
    "Nagle’s algorithm": ["nagle", "nagle2"], "Delayed ACK": ["nagle", "nagle2"], "TCP_NODELAY": ["nagle", "nagle2"], "TCP_QUICKACK": ["nagle", "nagle2"],
    "Pingpong mode (Linux)": ["nagle"], "tcpdump": ["nagle", "conn"], "Three-way handshake": ["conn"], "Keep-alive (HTTP)": ["conn", "conn2"],
    "TIME_WAIT": ["conn", "conn2"], "CLOSE_WAIT": ["conn", "conn2"], "FIN_WAIT2": ["conn", "conn2"], "Ephemeral ports": ["conn"], "tcp_tw_reuse": ["conn"],
    "SO_LINGER / RST": ["conn2"], "Connect timeout": ["timeouts", "timeouts2"], "Request timeout (HttpClient)": ["timeouts", "timeouts2"],
    "SO_TIMEOUT / read timeout": ["timeouts", "timeouts2"], "SYN retries": ["timeouts2"], "Timeout defaults": ["timeouts"],
    "Little’s Law": ["pools", "pools2"], "Pool sizing": ["pools", "pools2"], "HikariCP": ["pools", "timeouts"], "CPU-bound pools": ["pools2"],
    "Coordinated omission": ["co", "co2"], "Open vs closed loop": ["co", "co2"], "Percentiles": ["co", "co2"], "HdrHistogram": ["co"],
    "wrk2 / k6 / Gatling": ["co"], "JIT tiers (C1, C2)": ["jit"], "Warm-up": ["jit"], "On-stack replacement": ["jit"], "PrintCompilation": ["jit"],
    "Deoptimisation": ["jit"], "JMH": ["jit2"], "Dead-code elimination": ["jit2"], "Constant folding": ["jit2"], "Blackhole": ["jit2"],
    "G1": ["gc", "gc2"], "ZGC (generational)": ["gc", "gc2"], "Evacuation failure": ["gc", "gc2"], "Full GC": ["gc", "gc2"], "GC logging": ["gc", "gc2"],
    "Tail latency": ["gc2", "co2"], "Virtual threads": ["vt"], "Carrier threads": ["vt"], "Pinning": ["vt"], "jdk.VirtualThreadPinned (JFR)": ["vt"],
    "synchronized": ["vt", "jmm"], "ReentrantLock": ["vt"], "cgroups": ["box", "box2"], "--cpus / cpu.max": ["box", "box2"], "availableProcessors()": ["box", "box2"],
    "MaxRAMPercentage": ["box", "box2"], "ActiveProcessorCount": ["box"], "Server-class machine": ["box", "gc"], "Serial GC": ["box"],
    "CPU throttling": ["box", "box2"], "ForkJoinPool.commonPool": ["box2"], "Native memory": ["box2"], "Java Memory Model": ["jmm", "jmm2"],
    "Happens-before": ["jmm", "jmm2"], "Data race": ["jmm"], "volatile": ["jmm", "jmm2"], "Store buffering": ["jmm"], "jcstress": ["jmm", "jmm2"],
    "Visibility": ["jmm2"], "Lost update": ["jmm2"], "Final fields": ["jmm2"],
    "Kafka producer batching": ["kafka"], "linger.ms": ["kafka"], "batch.size": ["kafka"], "acks": ["kafka"], "enable.idempotence": ["kafka"],
    "fetch.min.bytes / fetch.max.wait.ms": ["kafka2"], "Consumer groups and partitions": ["kafka2"], "max.poll.interval.ms": ["kafka2"],
    "CommitFailedException": ["kafka2"], "Rebalance (Kafka)": ["kafka2"],
    "Minshall’s modification": ["nagle3"], "TCP_CORK": ["nagle3"], "tcp_autocorking": ["nagle3"], "Inlining": ["jit3"], "MaxInlineSize / FreqInlineSize": ["jit3"],
    "Megamorphic call site": ["jit3"], "Bimorphic inlining": ["jit3"], "Uncommon trap": ["jit3"], "Escape analysis": ["jit3"], "PrintInlining": ["jit3"],
    "G1 regions": ["gc3"], "Humongous objects": ["gc3"], "Remembered set": ["gc3"], "Card table": ["gc3"], "Load barrier (ZGC)": ["gc3"], "Coloured pointers": ["gc3"],
    "Write barrier": ["gc3"], "StackChunk": ["vt2"], "ThreadStackSize": ["vt2"], "Native Memory Tracking": ["vt2", "box2"], "Memory barriers (fences)": ["jmm3"],
    "lock addl": ["jmm3"], "VarHandle setRelease": ["jmm3"], "AtomicInteger cost": ["jmm3"],
}
HAS = {p[0] for p in PAGES} | {"dsources", "dindex"}


def idx_html():
    keyf = lambda t: re.sub(r"^[-@.]+", "", t).lower()
    out, cur = [], None
    for term in sorted(IDX, key=keyf):
        ks = [k for k in IDX[term] if k in HAS]
        if not ks:
            continue
        L = keyf(term)[0].upper()
        if L != cur:
            out.append(f'<div class="L">{L}</div>')
            cur = L
        out.append(f'<div class="e"><span>{term}</span><span class="pgs">{", ".join(f"<a href=\"#p-{k}\">@@{k}@@</a>" for k in ks)}</span></div>')
    return "".join(out)


page("dindex", f'''
{sub("Find anything", "Index A–Z", "#0F172A")}
<div class="idx" style="--accent:#1D4ED8">{idx_html()}</div>
<h2>Three ways in</h2>
<div class="three">
  <div class="card"><b class="h">A request is slow</b>Nagle {ref("nagle")}, connection reuse {ref("conn2")}, pools {ref("pools")}, GC pauses {ref("gc2")}, CPU throttling {ref("box2")}.</div>
  <div class="card"><b class="h">A request hangs</b>Timeouts and their defaults {ref("timeouts")}, the three broken peers {ref("timeouts2")}, pinned virtual threads {ref("vt")}, a loop that never sees a flag {ref("jmm2")}.</div>
  <div class="card"><b class="h">The numbers look wrong</b>Coordinated omission {ref("co")}, warm-up {ref("jit")}, JMH and dead code {ref("jit2")}, production limits in tests {ref("box")}.</div>
</div>
''', chapter="Index", color="#0F172A", bm="Index")
