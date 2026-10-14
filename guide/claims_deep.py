"""Guards for the deep-dive book: each conclusion its pages state without a condition is re-checked against the CI logs.
If a fresh run tells a different story, this fails and the PDF is not published."""
import os, sys

import lib
import dd1, dd2, dd3, dd4, dd5

CI = bool(os.environ.get("GITHUB_ACTIONS"))
problems = []


def claim(ok, text):
    print(("ok   " if ok else "FAIL ") + text)
    if not ok:
        problems.append(text)


def needed(found, what):
    """A log line a page relies on; locally an older log may lack it."""
    if not found:
        print(("FAIL " if CI else "skip ") + "missing: " + what)
        if CI:
            problems.append("missing: " + what)
    return bool(found)


# 1 · Nagle and delayed ACK
N = {r[0].strip(): r for r in dd1.ROWS}
p50 = lambda k: float(N[k][1])
slow_n = lambda k: int(N[k][5])
claim(p50("client 2 writes, Nagle on") > 30 and slow_n("client 2 writes, Nagle on") > 0.9 * int(N["client 2 writes, Nagle on"][6]),
      f"Nagle: 2 client writes stall (p50 {p50('client 2 writes, Nagle on')} ms)")
claim(p50("server 2 writes, Nagle on") > 30, "Nagle: 2 server writes stall")
for k in ("client 2 writes, TCP_NODELAY", "server 2 writes, TCP_NODELAY", "client 1 write,  Nagle on"):
    claim(slow_n(k) == 0 and p50(k) < 1, f"fast: {k} (p50 {p50(k)} ms)")
if needed("client 2 writes, QUICKACK once" in N, "QUICKACK rows in nagle.txt"):
    claim(p50("client 2 writes, QUICKACK once") > 30, "QUICKACK set once: still stalls")
    claim(p50("client 2 writes, QUICKACK per read") < 1, "QUICKACK before every read: no stall")
claim(35 <= dd1.WAIT_MS <= 45, f"trace: delayed ACK after {dd1.WAIT_MS:.2f} ms ≈ TCP_DELACK_MIN 40 ms")
claim(dd1.FIRST_ACK_MS < 1, f"trace: first request ACKed at once ({dd1.FIRST_ACK_MS:.3f} ms, quick-ACK mode)")

# 2 · connections
C = dd2.CONN
claim(all(us > dd2.KEEP for k, (us, _) in C.items() if k.startswith("new connection")), "a new connection per request costs more than keep-alive")
if needed(dd2.NEW_STYLE and "new connection, server never" in C, "connections.txt with close modes"):
    tw = lambda k: C["new connection, " + k][1]["TIME_WAIT"]
    claim(tw("client first") == (2000, 0), "TIME_WAIT: client closes first → 2,000 on the client, 0 on the server")
    claim(tw("server first") == (0, 2000), "TIME_WAIT: server closes first → 0 / 2,000")
    claim(tw("client reset") == (0, 0), "SO_LINGER(0): no TIME_WAIT")
    st = C["new connection, server never"][1]
    claim(st["CLOSE_WAIT"] == (0, 2000) and st["FIN_WAIT2"] == (2000, 0), "server never closes: CLOSE_WAIT on server, FIN_WAIT2 on client")

# 3 · timeouts
T = {(p, s): (t, r) for p, s, t, r in dd2.TO}
claim(T[("silent", "connectTimeout 1 s")][1].startswith("still waiting"), "silent server: connectTimeout alone does not help")
claim("HttpTimeoutException" in T[("silent", "request timeout 2 s")][1] and abs(T[("silent", "request timeout 2 s")][0] - 2) < 0.5, "silent server: request timeout fires at 2 s")
claim(T[("trickle", "request timeout 2 s")][1].startswith("still waiting"), "trickling body: request timeout does not cover the body")
claim("no error" in T[("trickle", "Socket soTimeout 1 s")][1] and T[("trickle", "Socket soTimeout 1 s")][0] > 1.5, "trickling body: soTimeout is per read, no error")
claim("HttpConnectTimeoutException" in T[("dropped", "connectTimeout 1 s")][1] and abs(T[("dropped", "connectTimeout 1 s")][0] - 1) < 0.5, "dropped packets: connectTimeout fires at 1 s")
claim("HttpConnectTimeoutException" in T[("dropped", "request timeout 2 s")][1], "dropped packets: request timeout reports a connect timeout")

# 4 · pools
claim(max(dd3.lw) < 0.02, f"Little’s Law within 2% in every row (worst {max(dd3.lw) * 100:.1f}%)")
P = {int(r[0]): r for r in dd3.P}
for c in (1, 2):
    pred = c / dd3.service_ms * 1000
    claim(abs(int(P[c][1]) - pred) / pred < 0.1, f"pool {c}: measured {P[c][1]}/s vs predicted {pred:.0f}/s")
claim(max(int(P[c][1]) for c in P if c >= 4) < 1.05 * int(P[4][1]), "pools above 4 add no throughput")
claim(float(P[64][4]) > float(P[4][4]), "a bigger pool moves the wait into the database")

# 5 · coordinated omission
n, o = dd3.naive[1], dd3.openl[1]
claim(float(n["p99"]) * 50 < float(o["p99"]), f"closed-loop p99 {n['p99']} ms hides the stall; open loop {o['p99']} ms")
claim(1 / int(dd3.naive[0]) < 0.001 and float(n.get("p99.99", n["max"])) > 500, "the stall only shows at p99.99 / max in the closed loop")
claim(int(dd3.naive[0]) < dd3.CO_N, "the closed loop sent fewer requests than were due")

# 6 · JIT
claim(dd4.interp / dd4.steady > 20, f"compiled code much faster than the interpreter ({dd4.interp / dd4.steady:.0f}×)")
claim(any("made not entrant" in l for l in dd4.COMP), "PrintCompilation shows code made not entrant")

# 7 · GC
g1, z = dd4.GC["G1"], dd4.GC["ZGC"]
claim(z["max"] < g1["max"] and z["p999"] < g1["p999"], "ZGC tail below G1's")
claim(max(z["pauses"]) < 1, f"ZGC pauses under 1 ms (longest {max(z['pauses']):.3f})")
claim(g1["p50"] < 0.1 and z["p50"] < 0.1, "median unaffected by either collector")

# 8 · virtual threads
claim(dd4.virt < dd4.plat / 5, f"virtual threads {dd4.virt} s vs 200 platform threads {dd4.plat} s")
expect = 100 / dd4.carriers * 0.1
claim(abs(dd4.pinned - expect) / expect < 0.15, f"pinned: {dd4.pinned} s ≈ 100 / {dd4.carriers} × 0.1 = {expect:.2f} s")
claim(dd4.unpinned < 0.3, f"ReentrantLock: {dd4.unpinned} s, no pinning")
claim("reason:MONITOR" in dd4.VT, "pinning trace names a monitor")

# 9 · containers
claim(dd5.half["cpus"] == 1, "--cpus=0.5 reported as 1 CPU")
claim(dd5.two["gc"] == "G1" and dd5.one["gc"] == "Serial" and dd5.apc["gc"] == "Serial", "G1 at 2 CPUs/2 GB; Serial at 1 GB, even with 4 CPUs")
claim(dd5.apc["cpus"] == 4 and dd5.mrp["heap"] > 2.5 * dd5.one["heap"], "ActiveProcessorCount and MaxRAMPercentage take effect")
claim(all(abs(b["heap"] / b["mem"] - 0.25) < 0.02 for b in dd5.BOX if b["mem"] and not b["flags"]), "default heap ≈ 25% of the limit")
claim(all(b["pool"] == max(1, b["cpus"] - 1) for b in dd5.BOX), "commonPool = CPUs − 1, at least 1")
if needed(dd5.THR, "throttle.txt"):
    claim(dd5.hot["thr"] > 0 and dd5.hot["opts"] != "no limit", f"throttling seen under {dd5.hot['opts']}")
    if dd5.calm:
        claim(dd5.hot["max"] > 3 * dd5.calm["max"], "throttled timer far later than unlimited")

# 10 · memory model
sb = int(dd5.sb[1].replace(",", ""))
claim(sb > 0, f"store buffering: 0, 0 observed {sb:,} times with plain fields")
claim(dd5.sbv[1] == "0", "store buffering: never with volatile")
claim(dd5.sf_stuck >= 1 and dd5.sf_vstop == len(dd5.sf_vol), f"StaleFlag: plain stuck {dd5.sf_stuck}/{len(dd5.sf_plain)}, volatile always stopped")
claim(dd5.jrow("SpinVolatileTest", "STALE")[1] == "0", "SpinVolatileTest never stale")
claim(dd5.atomic[1] == "0" and dd5.racy[1] != "0", "racy counter loses updates, atomic never does")

print(f"\n{len(problems)} problem(s)")
sys.exit(1 if problems else 0)
