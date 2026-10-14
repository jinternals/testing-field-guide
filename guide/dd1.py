"""Chapter 1 · Nagle's algorithm, delayed ACK and TCP_NODELAY."""
from dd_lib import *

K = chap(1, "Nagle and delayed ACK")

# ---------------------------------------------------------------- the trace
TRACE = [l for l in dlog("nagle-trace.txt").splitlines() if " IP " in l]


def pkt(line):
    m = re.match(r"\s*(\d+):(\d+):([\d.]+) IP [\d.]+\.(\d+) > [\d.]+\.(\d+): Flags \[([^\]]+)\](?:, seq ([\d:]+))?.*?length (\d+)", line)
    h, mi, sec, sport, dport, flags, seq, length = m.groups()
    t = (int(h) * 3600 + int(mi) * 60 + float(sec)) * 1000
    return dict(t=t, client=dport == "18080", flags=flags, seq=seq, len=int(length))


PK = [pkt(l) for l in TRACE]
# the first request whose second half waited: client data, then the server's ACK more than 10 ms later
i0 = next(i for i in range(len(PK) - 1)
          if PK[i]["client"] and PK[i]["len"] == 50 and not PK[i + 1]["client"] and PK[i + 1]["t"] - PK[i]["t"] > 10)
ROUND = PK[i0:i0 + 5]
T0 = ROUND[0]["t"]
WAIT_MS = ROUND[1]["t"] - T0
f0 = next(i for i, p in enumerate(PK) if p["client"] and p["len"] == 50)   # round 1, first data
FIRST_ACK_MS = PK[f0 + 1]["t"] - PK[f0]["t"]


def seq_diagram():
    b = [ARROW.format(id="na", c="#1D4ED8"), ARROW.format(id="nb", c="#92400E")]
    cx, sx, top = 120, 420, 34
    for x, name in ((cx, "client · Nagle on"), (sx, "server")):
        b.append(f'<text x="{x}" y="14" text-anchor="middle" font-size="8.4" font-weight="700" fill="#0F172A">{name}</text>')
        b.append(f'<line x1="{x}" y1="20" x2="{x}" y2="196" stroke="#94A3B8" stroke-width="1.2"/>')
    ys = [top, 128, 146, 160, 178]
    labels = []
    for (p, y) in zip(ROUND, ys):
        dt = p["t"] - T0
        what = f'{p["len"]} bytes' if p["len"] else "ACK"
        x1, x2, col, mk = (cx, sx, "#1D4ED8", "na") if p["client"] else (sx, cx, "#92400E", "nb")
        b.append(f'<line x1="{x1}" y1="{y}" x2="{x2 - 4 if x2 > x1 else x2 + 4}" y2="{y + 7}" stroke="{col}" stroke-width="1.3" marker-end="url(#{mk})"/>')
        b.append(f'<text x="{(x1 + x2) / 2}" y="{y + 1}" text-anchor="middle" font-size="7.2" fill="{col}" font-weight="600">{what}</text>')
        b.append(f'<text x="{x2 + (8 if x2 > x1 else -8)}" y="{y + 10}" text-anchor="{"start" if x2 > x1 else "end"}" font-size="6.8" class="mono" fill="#334155">+{dt:.2f} ms</text>')
    b.append(f'<rect x="8" y="{top + 16}" width="104" height="62" rx="4" fill="#EFF6FF" stroke="#93C5FD"/>')
    for k, t in enumerate(["2nd write(): 50 bytes", "held by Nagle —", "the first 50 are", "not ACKed yet"]):
        b.append(f'<text x="14" y="{top + 28 + k * 11}" font-size="6.9" fill="#1E3A8A">{t}</text>')
    b.append(f'<rect x="428" y="{top + 16}" width="104" height="62" rx="4" fill="#FFFBEB" stroke="#FCD34D"/>')
    for k, t in enumerate(["has 50 of 100 bytes,", "nothing to send:", "ACK waits for the", "delayed-ACK timer"]):
        b.append(f'<text x="434" y="{top + 28 + k * 11}" font-size="6.9" fill="#78350F">{t}</text>')
    b.append(f'<text x="270" y="92" text-anchor="middle" font-size="9" font-weight="700" fill="#B91C1C">{WAIT_MS:.1f} ms with nothing on the wire</text>')
    b.append(f'<text x="270" y="194" text-anchor="middle" font-size="6.8" fill="#5B6474">response, 100 bytes: the request is done</text>')
    return svg("".join(b), 540, 202,
               f"Packet sequence from a real tcpdump capture: the client sends 50 bytes; its second 50-byte write is held by Nagle's algorithm; "
               f"the server has only half the request and delays its ACK; {WAIT_MS:.1f} ms later the ACK arrives, the client sends the rest and the server answers.")


# ---------------------------------------------------------------- results
ROWS = []
for line in dlog("nagle.txt").splitlines():
    m = re.match(r"(.+?)\s+p50\s+([\d.]+)\s+p90\s+([\d.]+)\s+p99\s+([\d.]+)\s+max\s+([\d.]+) ms\s+over 30 ms: (\d+) of (\d+)", line)
    if m:
        ROWS.append(m.groups())
NAGLE = {r[0].replace("  ", " "): r for r in ROWS}
slow = [r for r in ROWS if int(r[5]) > 0]
fast = [r for r in ROWS if int(r[5]) == 0]
SLOW_P50 = max(float(r[1]) for r in slow)
FAST_P99 = max(float(r[3]) for r in fast)
HZ = MACHINE["hz"]
SC = MACHINE["sysctl"]

LINUX = [
    ('<code style="white-space:nowrap">TCP_DELACK_MIN</code>', "HZ/25 jiffies = <b>40 ms</b>", "shortest delayed-ACK timer", "include/net/tcp.h"),
    ('<code style="white-space:nowrap">TCP_DELACK_MAX</code>', "HZ/5 jiffies = <b>200 ms</b>", "longest delayed-ACK timer", "include/net/tcp.h"),
    ('<code style="white-space:nowrap">TCP_MAX_QUICKACKS</code>', "<b>16</b>", "ACKs sent at once in quick-ACK mode", "include/net/tcp.h"),
    ('<code style="white-space:nowrap">tcp_pingpong_thresh</code>', f"<b>{SC.get('tcp_pingpong_thresh', '?')}</b> on the runner", "replies before a connection counts as request/response", "ip-sysctl.rst"),
    ('<code style="white-space:nowrap">CONFIG_HZ</code>', f"<b>{HZ}</b> on the runner", f"timer tick: {1000 / HZ:g} ms", "/boot/config"),
]

page("nagle", f'''
{sub(K, "Two good ideas that wait for each other", CN)}
<p class="lede-s">TCP has two old optimisations against tiny packets. The <b>sender</b> holds back a small segment while earlier data is unacknowledged (Nagle). The <b>receiver</b> holds back its ACK, hoping to piggyback it on a reply (delayed ACK). In a request/response exchange where one message goes out in two <code>write()</code> calls, each waits for the other — until a timer fires.</p>
<div class="two top" style="grid-template-columns:1fr 1fr;gap:3mm">
  <div class="mech" style="--accent:{CN}">
    <h3>Nagle’s algorithm — the sender</h3>
    <p class="rfc">“If there is unacknowledged data (i.e., SND.NXT &gt; SND.UNA), then the sending TCP endpoint buffers all user data (regardless of the PSH bit) until the outstanding data has been acknowledged or until the TCP endpoint can send a full-sized segment.” — RFC 9293 §3.7.4</p>
    <p>TCP <b>SHOULD</b> implement it (SHLD-7); there <b>MUST</b> be a way to disable it per connection (MUST-17). In Java that is <code>TCP_NODELAY</code>, off by default on a <code>java.net.Socket</code>.</p>
  </div>
  <div class="mech" style="--accent:{CN}">
    <h3>Delayed ACK — the receiver</h3>
    <p class="rfc">“A TCP endpoint SHOULD implement a delayed ACK (SHLD-18) … the delay MUST be less than 0.5 seconds (MUST-40).” An ACK SHOULD go out for at least every second full-sized segment. — RFC 9293 §3.8.6.3</p>
    <p>Linux starts each connection in <b>quick-ACK</b> mode and leaves it once the connection looks like request/response (“ping-pong”): a reply sent within the ACK timeout of receiving data counts. From then on, a lone segment waits for the timer.</p>
  </div>
</div>
<h2>The stall, captured</h2>
{seq_diagram()}
<div class="two top" style="grid-template-columns:1.25fr 1fr;gap:3mm;margin-top:1.5mm">
  {table(["Linux", "Value", "Meaning", "Where"], LINUX, "xs")}
  <div>
    <p class="small">The capture shows the second request on the connection. <b>{WAIT_MS:.1f} ms</b> = the 40 ms minimum delayed-ACK timer plus timer granularity ({1000 / HZ:g} ms ticks on this kernel).</p>
    <p class="small" style="margin-top:1.2mm">The <b>first</b> request did not wait: its ACK came back in {FIRST_ACK_MS:.3f} ms, while the new connection was still in quick-ACK mode. After one request and its reply, Linux treats the connection as ping-pong and starts delaying ACKs.</p>
  </div>
</div>
{src("RFC 9293 (2022) §3.7.4, §3.8.6.3", "RFC 896 (Nagle, 1984)", "Linux include/net/tcp.h, net/ipv4/tcp_input.c, tcp_output.c (tcp_event_data_sent: pingpong)", "Documentation/networking/ip-sysctl.rst", "OpenJDK 21 StandardSocketOptions.TCP_NODELAY", f"capture: tcpdump on loopback, {RUNNER}")}
''', chapter=K, color=CN, bm="01 · Nagle and delayed ACK")

WHO = [
    ("JDK <code>HttpClient</code>", "on", "<code>PlainHttpConnection</code>: <code>setOption(TCP_NODELAY, true)</code>"),
    ("JDK <code>HttpServer</code>", "<b>off</b>", "only with <code>-Dsun.net.httpserver.nodelay=true</code> (<code>ServerConfig</code>)"),
    ("<code>java.net.Socket</code>", "<b>off</b>", "<code>StandardSocketOptions.TCP_NODELAY</code>: default <code>FALSE</code>"),
    ("Tomcat", "on", "<code>SocketProperties.tcpNoDelay = TRUE</code>"),
    ("Jetty 12", "on", "<code>ServerConnector._acceptedTcpNoDelay = true</code>"),
    ("Netty 4.1", "on", "<code>DefaultSocketChannelConfig</code>: on unless Android"),
    ("PostgreSQL JDBC", "on", "<code>PGProperty.TCP_NO_DELAY</code>: default <code>\"true\"</code>"),
    ("Lettuce (Redis)", "on", "<code>SocketOptions.DEFAULT_SO_NO_DELAY = true</code>"),
    ("Kafka client", "on", "<code>Selector</code>: <code>socket.setTcpNoDelay(true)</code>"),
]
res_rows = [(f"{r[0].strip()}", f"{float(r[1]):.2f}", f"{float(r[3]):.2f}", f"{float(r[4]):.2f}", f"{r[5]} of {r[6]}") for r in ROWS]

page("nagle2", f'''
{sub(K, f"Measured: 200 requests, {len(ROWS)} ways to send them", CN)}
<p class="lede-s">One connection on loopback, 200 request/response round trips of 100 bytes each way. The only differences: whether a message is written in one <code>write()</code> or two (like headers, then body), on which side, and which socket option is set.</p>
<div class="two top" style="grid-template-columns:1.12fr 1fr;gap:3mm">
  {code(dsrc("tcp/Nagle.java", "  static long[] exchange", "\n  }") + "\n\n" + dsrc("tcp/Nagle.java", "  /** 100 bytes in one write", "\n  }"), "Nagle.java — the client side", cls="xs")}
  <div>
    {table(["Setup", "p50 ms", "p99 ms", "max ms", "over 30 ms"], res_rows, "xs")}
    <p class="small muted" style="margin-top:1mm">Real output · {RUNNER}</p>
  </div>
</div>
<div class="two top" style="grid-template-columns:1fr 1fr;gap:3mm;margin-top:2mm">
  <div>
    <h2 style="margin-top:0">Who turns Nagle off for you</h2>
    {table(["Library", "TCP_NODELAY", "Evidence in its source"], WHO, "xs")}
  </div>
  {ticks([f"<b>Two writes per message + Nagle = one timer per message.</b> Every round trip took about {SLOW_P50:.0f} ms; every fix brought p99 under {FAST_P99:.1f} ms.",
          "<b>Write each message once.</b> Build it in a buffer (or wrap the stream in a <code>BufferedOutputStream</code>) and flush once: Nagle never has a second small segment to hold.",
          "<b>Or set <code>TCP_NODELAY</code></b> on request/response connections — on the side that writes twice. Most servers and the JDK client already do; the JDK’s own <code>HttpServer</code> does not.",
          "<b>The receiver can help:</b> <code>jdk.net.ExtendedSocketOptions.TCP_QUICKACK</code> (Linux, JDK 10+) asks for an immediate ACK — but it is not sticky. Set once, nothing changed; set before every read, the stall was gone.",
          "<b>Test for it:</b> a latency test on loopback shows it at once — on Linux, a p50 just over 40 ms with idle CPUs. The main guide’s load test found exactly this in the JDK <code>HttpServer</code>."], CN)}
</div>
{src("OpenJDK 21: jdk/internal/net/http/PlainHttpConnection.java, sun/net/httpserver/ServerConfig.java, ServerImpl.java, java/net/StandardSocketOptions.java, jdk/net/ExtendedSocketOptions.java (TCP_QUICKACK, since 10)", "Tomcat main: SocketProperties.java", "Jetty 12.0: ServerConnector.java", "Netty 4.1: DefaultSocketChannelConfig.java", "pgjdbc: PGProperty.java", "Lettuce: SocketOptions.java", "Kafka: clients/…/network/Selector.java", "results: deepdive/logs/nagle.txt")}
''', chapter=K, color=CN)
