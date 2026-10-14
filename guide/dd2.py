"""Chapter 2 · connections: handshake, keep-alive, TIME_WAIT. Chapter 3 · timeouts."""
from dd_lib import *
import dd1

# ============================================================================
# 2 · connections
# ============================================================================
K2 = chap(2, "Connections")
SC = MACHINE["sysctl"]
lo, hi = (int(x) for x in SC["ip_local_port_range"].split())
PORTS = hi - lo + 1
TW_S = 60                                             # Linux TCP_TIMEWAIT_LEN = 60*HZ
RATE = PORTS / TW_S

C = dlog("connections.txt")
CONN = {}
for m in re.finditer(r"^(.+?)\s{2,}([\d.]+) µs per request(.*)$", C, re.M):
    st = dict((k, (int(a), int(b))) for k, a, b in re.findall(r"(TIME_WAIT|CLOSE_WAIT|FIN_WAIT2) (\d+)/(\d+)", m.group(3)))
    CONN[m.group(1).strip()] = (float(m.group(2)), st)
KEEP = CONN["one kept-alive connection"][0]
NEW_STYLE = any(k.startswith("new connection, client first") for k in CONN)

# handshake and close, from the real capture
PK = dd1.PK
HS = PK[:3]
CL = [p for p in PK if "F" in p["flags"]]
fin_i = PK.index(CL[0])
CLOSE = PK[fin_i:fin_i + 3]


def life_diagram():
    b = [ARROW.format(id="la", c="#1D4ED8"), ARROW.format(id="lb", c="#92400E")]
    cx, sx = 110, 400
    for x, name in ((cx, "client"), (sx, "server")):
        b.append(f'<text x="{x}" y="12" text-anchor="middle" font-size="8.4" font-weight="700" fill="#0F172A">{name}</text>')
        b.append(f'<line x1="{x}" y1="18" x2="{x}" y2="188" stroke="#94A3B8" stroke-width="1.2"/>')

    def arrow(p, y, t0, label):
        x1, x2, col, mk = (cx, sx, "#1D4ED8", "la") if p["client"] else (sx, cx, "#92400E", "lb")
        b.append(f'<line x1="{x1}" y1="{y}" x2="{x2 - 4 if x2 > x1 else x2 + 4}" y2="{y + 6}" stroke="{col}" stroke-width="1.3" marker-end="url(#{mk})"/>')
        b.append(f'<text x="{(x1 + x2) / 2}" y="{y + 1}" text-anchor="middle" font-size="7.2" font-weight="600" fill="{col}">{label}</text>')
        b.append(f'<text x="{x2 + (8 if x2 > x1 else -8)}" y="{y + 9}" text-anchor="{"start" if x2 > x1 else "end"}" font-size="6.6" class="mono" fill="#334155">+{(p["t"] - t0) * 1000:.0f} µs</text>')

    names = ["SYN", "SYN, ACK", "ACK"]
    for k, p in enumerate(HS):
        arrow(p, 28 + k * 16, HS[0]["t"], names[k])
    b.append(f'<rect x="{cx + 20}" y="80" width="{sx - cx - 40}" height="34" rx="4" fill="#F1F5F9" stroke="#CBD5E1"/>')
    b.append(f'<text x="{(cx + sx) / 2}" y="94" text-anchor="middle" font-size="7.2" fill="#334155">request / response, again and again</text>')
    b.append(f'<text x="{(cx + sx) / 2}" y="106" text-anchor="middle" font-size="7.2" fill="#334155">on the same connection (keep-alive)</text>')
    names = ["FIN", "FIN, ACK", "ACK"]
    for k, p in enumerate(CLOSE):
        arrow(p, 126 + k * 16, CLOSE[0]["t"], names[k])
    closer = "client" if CLOSE[0]["client"] else "server"
    x = cx if CLOSE[0]["client"] else sx
    b.append(f'<rect x="{x - 64 if closer == "client" else x + 10}" y="172" width="118" height="20" rx="4" fill="#FEF3C7" stroke="#F59E0B"/>')
    b.append(f'<text x="{x - 5 if closer == "client" else x + 69}" y="185" text-anchor="middle" font-size="7.2" font-weight="700" fill="#78350F">{closer}: TIME_WAIT, {TW_S} s</text>')
    return svg("".join(b), 520, 196, f"Real capture of one connection: three-way handshake (SYN, SYN-ACK, ACK), many request/response exchanges, then the {closer} sends the first FIN and keeps the connection in TIME_WAIT for {TW_S} seconds.")


STATES = [
    ("<code>SYN-SENT</code>", "connect() sent a SYN, no answer yet", "the server is unreachable or dropping packets — see the next chapter"),
    ("<code>ESTABLISHED</code>", "open, data can flow both ways", "normal; compare with your pool sizes"),
    ("<code>FIN-WAIT-2</code>", "we closed; the peer has not closed its side yet", "the peer is not closing its sockets"),
    ("<code>CLOSE-WAIT</code>", "the peer closed; our application has not called close()", "<b>a socket leak in our code</b>"),
    ("<code>TIME-WAIT</code>", "we closed first; waiting before the port can be reused", "many short-lived connections: reuse them"),
]

page("conn", f'''
{sub(K2, "Open once, reuse, close carefully", CN)}
<p class="lede-s">Before the first byte of a request, TCP spends a round trip on the handshake. After the last byte, the side that closes <b>first</b> keeps the connection in TIME_WAIT, holding its port. Both costs are paid per connection — so the number of connections, not requests, is what hurts.</p>
{life_diagram()}
<div class="three top" style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:3mm;margin-top:2mm">
  <div class="mech" style="--accent:{CN}">
      <h3>TIME_WAIT</h3>
      <p class="rfc">“When a connection is closed actively, it MUST linger in the TIME-WAIT state for a time 2xMSL (Maximum Segment Lifetime) (MUST-13).” “For this specification the MSL is taken to be 2 minutes.” — RFC 9293 §3.6.1, §3.4.2</p>
      <p>Sequence numbers stay “busy” until MSL seconds have passed (§3.4.3): the wait keeps old segments from being taken for a new connection’s. Linux does not wait 4 minutes but a fixed <b>{TW_S} s</b> (<code>TCP_TIMEWAIT_LEN</code>). <code>tcp_fin_timeout</code> is something else — how long an orphaned connection may sit in FIN_WAIT_2.</p>
    </div>
  <div class="mech" style="--accent:{CN}">
    <h3>Ephemeral ports run out</h3>
    <p>A connection is identified by four values: source address and port, destination address and port. To one destination, a client can only vary its own port. The runner’s range is <code>{lo}–{hi}</code>: <b>{PORTS:,}</b> ports. Each closed connection keeps its port for {TW_S} s, so one client address can open at most about <b>{RATE:,.0f} new connections per second</b> to one server address and port, for as long as that lasts — unless TIME_WAIT reuse applies.</p>
  </div>
  <div class="mech" style="--accent:{CN}">
    <h3>Reuse is not on everywhere</h3>
    <p><code>tcp_tw_reuse</code> lets a new outgoing connection take a port still in TIME_WAIT when that is safe. Its default is <b>2: loopback traffic only</b> — the runner has <code>{SC.get("tcp_tw_reuse", "?")}</code>. So a load test against <code>localhost</code> can open connections endlessly, while the same test against a real host runs out of ports. Test against the network you will run on.</p>
  </div>
</div>
<h2>States you will see in <code>ss</code>, and what they tell you</h2>
{table(["State", "Means", "Many of them usually mean"], STATES, "xs")}
{src("RFC 9293 §3.3.2, §3.4.2, §3.4.3, §3.6.1", "Linux include/net/tcp.h (TCP_TIMEWAIT_LEN)", "Documentation/networking/ip-sysctl.rst (ip_local_port_range, tcp_tw_reuse, tcp_fin_timeout)", f"capture and sysctl values: {RUNNER}")}
''', chapter=K2, color=CN, bm="02 · Connections")

HOW = {"client first": "client closes first", "server first": "server closes first",
       "client reset": "client closes with <code>SO_LINGER(0)</code>", "server never": "server never closes (a leak)"}
CONN_ROWS = [("one kept-alive connection", f"{KEEP:.1f}", "1.0×", "–", "–", "–")]
for key, label in HOW.items():
    us, st = CONN.get("new connection, " + key, (None, None))
    if us is None:
        continue
    f = lambda k, i: (f"<b>{st[k][i]}</b>" if st[k][i] else "0")
    CONN_ROWS.append((f"new connection, {label}", f"{us:.1f}", f"{us / KEEP:.1f}×",
                      f"{f('TIME_WAIT', 0)} / {f('TIME_WAIT', 1)}", f"{f('CLOSE_WAIT', 0)} / {f('CLOSE_WAIT', 1)}",
                      f"{f('FIN_WAIT2', 0)} / {f('FIN_WAIT2', 1)}" if "FIN_WAIT2" in st else "–"))
CF = CONN.get("new connection, client first", (0, {}))[0]

page("conn2", f'''
{sub(K2, "Measured: 2,000 requests, five ways", CN)}
<p class="lede-s">2,000 request/response exchanges on loopback: over one kept-alive connection, then over a new connection each time, closed four different ways. Afterwards the program counts sockets by state in the kernel’s own tables, <code>/proc/net/tcp</code> and <code>tcp6</code>.</p>
{table(["How", "µs / request", "vs kept-alive", "TIME_WAIT client / server", "CLOSE_WAIT client / server", "FIN_WAIT2 client / server"], CONN_ROWS, "xs")}
<p class="small muted" style="margin-top:1mm">Real output · {RUNNER}</p>
<div class="two top" style="grid-template-columns:1fr 1fr;gap:3mm;margin-top:2mm">
  {code(dsrc("tcp/Connections.java", "  static void perRequest", "\n  }"), "Connections.java — a new connection per request", cls="xs")}
  {ticks([f"<b>Reuse wins even on loopback:</b> a new connection per request cost {CF / KEEP:.1f}× as much — no network latency involved. Over a real network add a round trip per connection, and TLS on top.",
          "<b>TIME_WAIT lands on whoever closes first</b> — exactly 2,000 sockets on that side, none on the other. HTTP/1.1 <code>Connection: close</code> from a server leaves them on the server.",
          "<b><code>SO_LINGER(0)</code> left no TIME_WAIT</b>: <code>close()</code> sends a reset instead of a FIN. It also throws away unsent data and tells the peer something went wrong — a tool for errors, not a fix for port exhaustion.",
          "<b>A server that never closes</b> left 2,000 sockets in CLOSE_WAIT, and the clients’ ends waited in FIN_WAIT2 — the one state <code>tcp_fin_timeout</code> limits. Growing CLOSE_WAIT in <code>ss</code> means a socket leak in the application.",
          "<b>One <code>HttpClient</code> per application.</b> The JDK client keeps idle connections for 30 s (<code>jdk.httpclient.keepalive.timeout</code>) and reuses them. A new client per request means a new connection per request."], CN)}
</div>
<div class="two top" style="grid-template-columns:1fr 1fr;gap:3mm;margin-top:1mm">{ticks(["<b>Load tests:</b> open connections the way production does. A generator that reconnects for every request measures handshakes and can exhaust its own ports; one that never reconnects hides the cost of new users.",
          "<b>Watch for it:</b> <code>ss -tan state time-wait | wc -l</code> during a test; connection errors such as “Cannot assign requested address” mean the client ran out of ports.",
          "<b>Pools need a limit and an idle timeout</b> shorter than the server’s, or the pool hands out connections the server has already closed."], CN)}
  {code(dsrc("tcp/Connections.java", "  static long count", "\n  }"), "counting sockets by state", cls="xs")}</div>
{src("OpenJDK 21 java.net.http module-info.java (jdk.httpclient.keepalive.timeout, default 30)", "Linux ip-sysctl.rst", "results: deepdive/logs/connections.txt")}
''', chapter=K2, color=CN)

# ============================================================================
# 3 · timeouts
# ============================================================================
K3 = chap(3, "Timeouts")
T = dlog("timeouts.txt")
TO = []
for m in re.finditer(r"^(\w+)\s+\|\s+(.+?)\s{2,}([\d.]+) s\s+(.+)$", T, re.M):
    TO.append((m.group(1), m.group(2).strip(), float(m.group(3)), m.group(4).strip()))
PEER = {"silent": "never answers", "trickle": "headers at once, body 1 byte / 0.5 s", "dropped": "packets dropped (no handshake)"}
TO_ROWS = [(f"<b>{p}</b>: {PEER[p]}", s, f"{t:.1f} s", f"<code>{r}</code>" if "Exception" in r else r) for p, s, t, r in TO]


def to(peer, setting):
    return next(t for t in TO if t[0] == peer and t[1].startswith(setting))


PHASES = [
    ("TCP connect (handshake)", "<code>HttpClient.Builder.connectTimeout</code>; <code>Socket.connect(addr, ms)</code>", "the kernel’s SYN retries"),
    ("request sent, waiting for the status line and headers", "<code>HttpRequest.Builder.timeout</code> (counts from the start, connect included)", "forever"),
    ("reading the body", "nothing in <code>HttpClient</code>; <code>Socket.setSoTimeout</code> bounds each <code>read()</code>, not the total", "forever"),
    ("the whole call", "only what you add around it — e.g. <code>future.get(timeout)</code>", "forever"),
]
DEFAULTS = [
    ("JDK <code>HttpClient</code>", "none", "none (“block forever”)", "<code>HttpClient.Builder</code>, <code>HttpRequest.Builder</code> Javadoc"),
    ("<code>HttpURLConnection</code>", "0 = infinite", "0 = infinite", "<code>URLConnection</code>: “A timeout of zero is interpreted as an infinite timeout”"),
    ("<code>java.net.Socket</code>", "kernel’s SYN retries", "0 = infinite, per <code>read()</code>", "<code>Socket.setSoTimeout</code> Javadoc"),
    ("PostgreSQL JDBC", "<code>connectTimeout</code> 10 s", "<code>socketTimeout</code> 0 = none", "<code>PGProperty</code>"),
    ("HikariCP", "<code>connectionTimeout</code> 30 s — waiting for a pool connection", "—", "<code>HikariConfig</code>"),
    ("Lettuce (Redis)", "10 s", "command timeout 60 s", "<code>SocketOptions</code>, <code>RedisURI.DEFAULT_TIMEOUT</code>"),
    ("Kafka producer", "—", "<code>request.timeout.ms</code> 30 s", "<code>ProducerConfig</code>"),
]


def phase_diagram():
    b = []
    ph = [("connect", 70, "#1D4ED8"), ("send request", 70, "#155E75"), ("wait for status + headers", 150, "#6D28D9"), ("read body", 150, "#92400E")]
    x = 10
    for name, w, c in ph:
        b.append(f'<rect x="{x}" y="10" width="{w - 3}" height="22" rx="3" fill="{c}" opacity=".12" stroke="{c}"/>')
        b.append(f'<text x="{x + (w - 3) / 2}" y="24.5" text-anchor="middle" font-size="7.4" font-weight="700" fill="{c}">{name}</text>')
        x += w
    bars = [("connectTimeout", 10, 80, "#1D4ED8"), ("request timeout(…) — runs from the start", 10, 290, "#6D28D9"),
            ("setSoTimeout: each read() alone", 300, 450, "#92400E"),
            ("your own deadline around the call: the only bound on the body", 10, 450, "#B91C1C")]
    for k, (label, x1, x2, c) in enumerate(bars):
        y = 44 + k * 15
        b.append(f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="{c}" stroke-width="3" stroke-linecap="round"/>')
        b.append(f'<text x="{x1 + 2}" y="{y - 4}" font-size="7" fill="{c}" font-weight="600">{label}</text>')
    return svg("".join(b), 460, 100, "The phases of an HTTP call and what each timeout covers: connectTimeout covers connecting; the request timeout runs from the start until the status line and headers arrive; a socket read timeout covers each read separately; only a deadline around the whole call bounds reading the body.")


page("timeouts", f'''
{sub(K3, "A timeout bounds one wait, not the call", CN)}
<p class="lede-s">“The call has a 2-second timeout” is rarely true. Each setting bounds one phase of the call, and the phases nobody set wait forever. Read the JDK’s documentation and source carefully, then measure against servers that misbehave in each phase.</p>
{phase_diagram()}
<div class="two top" style="grid-template-columns:1.35fr 1fr;gap:3mm;margin-top:1.5mm">
  {table(["Phase", "Bounded by", "If unset"], PHASES, "xs")}
  <div class="mech" style="--accent:{CN}">
    <h3>What the request timeout covers</h3>
    <p class="rfc">“If the response is not received within the specified timeout then an HttpTimeoutException is thrown … The effect of not setting a timeout is the same as setting an infinite Duration, i.e. block forever.” — <code>HttpRequest.Builder.timeout</code></p>
    <p>“The response” means the status line and headers: in JDK 21 the timer is cancelled when <code>exch.responseAsync()</code> completes (<code>MultiExchange</code>, step “5. handle errors and cancel any timer set”). A body that arrives slowly is not covered.</p>
  </div>
</div>
<h2>Defaults: what you get when you set nothing</h2>
{table(["Client", "Connect", "Waiting for data", "Source"], DEFAULTS, "xs")}
{src("OpenJDK 21: java/net/http/HttpRequest.java, HttpClient.java (Javadoc)", "jdk/internal/net/http/MultiExchange.java, ResponseTimerEvent.java", "java/net/Socket.java, URLConnection.java (Javadoc)", "pgjdbc PGProperty.java", "HikariCP HikariConfig.java", "Lettuce SocketOptions.java, RedisURI.java", "Kafka ProducerConfig.java")}
''', chapter=K3, color=CN, bm="03 · Timeouts")

syn_html = PENDING
if has("syn.txt") and has("syn-ss.txt"):
    syn = dlog("syn.txt").strip()
    secs = re.search(r"after ([\d.]+) s", syn).group(1)
    # the kernel's retransmission counter, seconds at which it went up
    steps, last = [], None
    for line in dlog("syn-ss.txt").splitlines():
        m = re.match(r"(\d+) s\s+timer:\(on,[^,]+,(\d+)\)", line)
        if m and m.group(2) != last:
            steps.append((int(m.group(1)), int(m.group(2))))
            last = m.group(2)
    sched = " · ".join(f"{n} at {t} s" for t, n in steps)
    gaps = [b[0] - a[0] for a, b in zip(steps, steps[1:])]
    doubling = len(gaps) >= 3 and all(abs(g2 - 2 * g1) <= 2 for g1, g2 in zip(gaps, gaps[1:]))
    how = "Each wait doubles; with" if doubling else "With"
    syn_html = f'''{code(syn, "real output · connect() with no timeout", kind="out", cls="xs out wrap")}
    <p class="small" style="margin-top:1mm">The kernel’s SYN retransmission count, read from <code>ss</code> every second: {sched}. {how} <code>tcp_syn_retries = {SC.get("tcp_syn_retries", "?")}</code> the kernel gave up after <b>{float(secs):.0f} s</b>.</p>'''

page("timeouts2", f'''
{sub(K3, "Measured: three bad servers, eight settings", CN)}
<p class="lede-s">Three local peers misbehave in different phases. The harness gives up after 5 s — the overall deadline the HTTP client does not provide. Packets to <code>192.0.2.1</code> (an address reserved for documentation, RFC 5737) are dropped with <code>iptables</code>, so the handshake simply never completes.</p>
<div class="two top" style="grid-template-columns:1.12fr 1fr;gap:3mm">
  {code(dsrc("tcp/Timeouts.java", "  static void call(String name, String hostPort", "\n  }"), "Timeouts.java — one call, two optional timeouts", cls="xs")}
  <div>
    {table(["Peer", "Setting", "Waited", "Result"], TO_ROWS, "xs")}
    <p class="small muted" style="margin-top:1mm">Real output · {RUNNER}</p>
  </div>
</div>
<div class="two top" style="grid-template-columns:1fr 1fr;gap:3mm;margin-top:2mm">
  <div>
    <h2 style="margin-top:0">No timeout at all: the kernel decides</h2>
    {syn_html}
  <div class="mech" style="--accent:{CN}">
      <h3>Connect timeouts</h3>
      <p class="rfc">“If the connection cannot be established within the given duration, then HttpClient::send throws an HttpConnectTimeoutException … If a new connection does not need to be established … this timeout duration has no effect.” — <code>HttpClient.Builder.connectTimeout</code></p>
      <p>The request timer fires during connect too: <code>ResponseTimerEvent</code> throws <code>HttpConnectTimeoutException</code> when the connection is not yet connected, else <code>HttpTimeoutException</code>.</p>
    </div>
  </div>
  {ticks([f"<b>The trickling body beat the 2 s request timeout</b>: still waiting at {to('trickle', 'request')[2]:.0f} s. A raw socket with a 1 s read timeout read it all in {to('trickle', 'Socket')[2]:.0f} s without an error — every byte came within 1 s.",
          f"<b>A connect timeout alone does not help</b> against a server that accepts and stays silent: still waiting at {to('silent', 'connectTimeout')[2]:.0f} s.",
          f"<b>Set both, and a deadline:</b> <code>connectTimeout</code> for the handshake, <code>timeout</code> for the headers, and a bound on the whole call around it (<code>future.get(…)</code>) — the only thing that stopped the trickle.",
          "<b>Test each phase</b> with a fake that misbehaves in it: silent after accept, slow headers, slow body, dropped packets. WireMock’s fixed and chunked delays and Toxiproxy do this without writing servers."], CN)}
</div>
{src("RFC 5737 (documentation addresses)", "Linux ip-sysctl.rst (tcp_syn_retries)", "results: deepdive/logs/timeouts.txt, syn.txt, syn-ss.txt")}
''', chapter=K3, color=CN)
