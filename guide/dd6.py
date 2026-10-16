"""Chapter 11 · Kafka: producer batching and consumer fetching."""
from dd_lib import *

K11 = chap(11, "Kafka")
KV = "4.3.1"

PROD, FETCH, PARTS, POLL, BROKER = [], [], [], "", ""
if has("kafka-producer.txt"):
    for m in re.finditer(r"^rate\s+(\d+)/s\s+linger\.ms\s+(\d+)\s+p50\s+([\d.]+)\s+p90\s+([\d.]+)\s+p99\s+([\d.]+)\s+max\s+([\d.]+) ms\s+\|\s+requests\s+([\d.]+)\s+records/request\s+([\d.]+)$",
                         dlog("kafka-producer.txt"), re.M):
        r = m.groups()
        PROD.append(dict(rate=int(r[0]), linger=int(r[1]), p50=float(r[2]), p90=float(r[3]), p99=float(r[4]), max=float(r[5]),
                         req=int(float(r[6])), rpr=float(r[7])))
if has("kafka-fetch.txt"):
    for m in re.finditer(r"^(fetch\.min\.bytes .+?)\s{2,}p50\s+([\d.]+)\s+p90\s+([\d.]+)\s+p99\s+([\d.]+)\s+max\s+([\d.]+) ms$", dlog("kafka-fetch.txt"), re.M):
        FETCH.append((m.group(1),) + tuple(float(x) for x in m.groups()[1:]))
if has("kafka-partitions.txt"):
    PARTS = [(c, int(n)) for c, n in re.findall(r"^consumer (c\d)\s+partitions (\d+)$", dlog("kafka-partitions.txt"), re.M)]
if has("kafka-pollinterval.txt"):
    POLL = dlog("kafka-pollinterval.txt").strip()
if has("kafka-broker.txt"):
    BROKER = re.search(r"Kafka version: (\S+)", dlog("kafka-broker.txt")).group(1)


def p(rate, linger):
    return next(x for x in PROD if x["rate"] == rate and x["linger"] == linger)


DEFAULTS = [
    ("<code>linger.ms</code>", "5", "how long a batch may wait for more records"),
    ("<code>batch.size</code>", "16384 bytes", "a batch this full is sent at once"),
    ("<code>acks</code>", "all", "the leader waits for the in-sync replicas"),
    ("<code>enable.idempotence</code>", "true", "“exactly one copy of each message is written”"),
    ("<code>fetch.min.bytes</code>", "1", "the broker answers a fetch as soon as 1 byte is available"),
    ("<code>fetch.max.wait.ms</code>", "500", "or after this long, if less data is available"),
    ("<code>max.poll.records</code>", "500", "most records returned by one <code>poll()</code>"),
    ("<code>max.poll.interval.ms</code>", "300000", "longest gap between <code>poll()</code> calls"),
]

prod_html = PENDING
if PROD:
    rows = [(f"{x['rate']:,}/s", str(x["linger"]), f"{x['p50']:.2f}", f"{x['p99']:.2f}", f"{x['max']:.2f}", f"{x['req']:,}", f"{x['rpr']:.1f}") for x in PROD]
    hi0, hi5, hi50 = p(2000, 0), p(2000, 5), p(2000, 50)
    lo0, lo50 = p(20, 0), p(20, 50)
    notes = [f"<b>At 2,000 records/s</b>, <code>linger.ms=0</code> sent {hi0['req']:,} requests ({hi0['rpr']:.1f} records each) and had a p99 of {hi0['p99']:.1f} ms. "
             f"<code>linger.ms=5</code> sent {hi5['req']:,} requests ({hi5['rpr']:.1f} records each) with a p99 of {hi5['p99']:.1f} ms"
             + (" — fewer requests and a lower tail, as the source’s note on the 4.0 default change says." if hi5["p99"] < hi0["p99"] and hi5["req"] < hi0["req"] else "."),
             f"<b>At 2,000 records/s with <code>linger.ms=50</code></b>: {hi50['rpr']:.0f} records per request and a p50 of {hi50['p50']:.1f} ms — records waited for the batch.",
             f"<b>At 20 records/s</b> (one every 50 ms) with <code>linger.ms=50</code>: p90 {lo50['p90']:.1f} ms against {lo0['p90']:.1f} ms with <code>linger.ms=0</code>, "
             f"and {lo50['rpr']:.1f} records per request — a record with no others to batch waits up to the linger time, as the source says."]
    prod_html = f'''{table(["Rate", "linger.ms", "p50 ms", "p99 ms", "max ms", "requests", "records / request"], rows, "xs")}
  <p class="small muted" style="margin:1mm 0 2mm">KafkaLatency.java · 5 s per row, 100-byte records, one partition · latency from each record’s due time to its acknowledgement · requests and records per request from the producer’s own metrics (<code>request-total</code>, <code>records-per-request-avg</code>) · broker {BROKER} in Docker · {RUNNER}</p>
  <div class="two top" style="grid-template-columns:1fr 1fr;gap:3mm">{ticks(notes, CQ)}
  {code(dsrc("kafka/KafkaLatency.java", "          for (int i = 0; i < n; i++) {", "\n          }", dedent=10), "KafkaLatency.java — records sent on a schedule", cls="xs")}</div>'''

page("kafka", f'''
{sub(K11, "Producer batching: linger.ms and batch.size", CQ)}
<p class="lede-s">A Kafka producer does not send each record on its own. It appends records to a batch per partition and sends a batch when it is full or when it has waited <code>linger.ms</code>. The Kafka {KV} client’s documentation for <code>linger.ms</code> compares this to chapter 1:</p>
<div class="two top" style="grid-template-columns:0.8fr 1.2fr;gap:3mm">
  <div class="mech" style="--accent:{CQ}">
    <h3><code>linger.ms</code>, from <code>ProducerConfig.java</code></h3>
    <p class="rfc">“This can be thought of as analogous to Nagle’s algorithm in TCP. … once we get <code>batch.size</code> worth of records for a partition it will be sent immediately regardless of this setting … The default changed from 0 to 5 in Apache Kafka 4.0 as the efficiency gains from larger batches typically result in similar or lower producer latency despite the increased linger.”</p>
  </div>
  <div>
    {table(["Setting", f"Default ({KV})", "Meaning"], DEFAULTS, "xs")}
    <p class="small muted" style="margin-top:1mm">Defaults from the <code>define(…)</code> calls in <code>ProducerConfig.java</code> and <code>ConsumerConfig.java</code> at tag {KV}. <code>acks</code> is not measured here: with one broker the leader is the only in-sync replica, so <code>acks=all</code> and <code>acks=1</code> wait for the same write.</p>
  </div>
</div>
<h2>Measured: the same producer at two rates and three linger times</h2>
{prod_html}
{src(f"Apache Kafka {KV}: clients/…/producer/ProducerConfig.java (linger.ms, batch.size, acks, enable.idempotence)", "results: deepdive/logs/kafka-producer.txt, kafka-broker.txt")}
''', chapter=K11, color=CQ, bm="11 · Kafka")

fetch_html = PENDING
if FETCH:
    d, w = FETCH[0], FETCH[1]
    fetch_html = f'''{table(["Consumer", "p50 ms", "p90 ms", "p99 ms", "max ms"], [(f[0], *(f"{v:.1f}" for v in f[1:])) for f in FETCH], "xs")}
    {ticks([f"<b>With the default <code>fetch.min.bytes=1</code></b> the broker answered as soon as a record arrived: p50 {d[1]:.1f} ms from send to <code>poll()</code>.",
            f"<b>With <code>fetch.min.bytes=1000000</code></b> one record never filled a fetch, so the broker held each fetch until <code>fetch.max.wait.ms</code>: p50 {w[1]:.0f} ms, max {w[4]:.0f} ms. A record that arrived early in a waiting fetch waited longest."], CQ)}'''
parts_html = PENDING
if PARTS:
    idle = sum(1 for _, n in PARTS if n == 0)
    parts_html = f'''{table(["Consumer", "Partitions assigned"], [(c, str(n)) for c, n in PARTS], "xs")}
    <p class="small" style="margin-top:1mm">The <code>KafkaConsumer</code> Javadoc: the group divides the partitions “so that each partition is assigned to exactly one consumer in the group”. Here {idle} of the {len(PARTS)} consumers had nothing to read. </p>'''

page("kafka2", f'''
{sub(K11, "Consumer fetching, partitions and max.poll.interval.ms", CQ)}
<div class="two top" style="grid-template-columns:1fr 1fr;gap:3mm">
  <div class="mech" style="--accent:{CQ}">
    <h3><code>fetch.min.bytes</code> and <code>fetch.max.wait.ms</code></h3>
    <p class="rfc">“If insufficient data is available the request will wait for that much data to accumulate before answering the request.” <code>fetch.max.wait.ms</code>: “The maximum amount of time the server will block before answering the fetch request” when there is not enough data for <code>fetch.min.bytes</code>. — <code>ConsumerConfig.java</code></p>
  </div>
  <div>
    <h2 style="margin-top:0">Measured: one record every 100 ms</h2>
    {fetch_html}
  </div>
</div>
<div class="two top" style="grid-template-columns:1fr 1fr;gap:3mm;margin-top:2mm">
  <div>
    <h2 style="margin-top:0">Measured: 4 consumers, 2 partitions</h2>
    {parts_html}
  </div>
  <div>
    <h2 style="margin-top:0">Measured: processing longer than <code>max.poll.interval.ms</code></h2>
    {code(POLL or "(waiting for the next CI run)", "real output", kind="plain", cls="xs out wrap")}
    <p class="small" style="margin-top:1mm">The client documentation: “If poll() is not called before expiration of this timeout, then the consumer is considered failed and the group will rebalance in order to reassign the partitions to another member.” The 6 s of processing exceeded the 3 s set here; the commit was then refused. The default is 300,000 ms.</p>
  </div>
</div>
<div class="two top" style="grid-template-columns:1.1fr 1fr;gap:3mm;margin-top:2mm">
  {code(dsrc("kafka/KafkaLatency.java", "  static void pollInterval()", "\n  }"), "KafkaLatency.java — slow processing", cls="xs")}
  {ticks(["<b>End-to-end latency includes the consumer’s fetch wait.</b> Raising <code>fetch.min.bytes</code> trades latency for fewer fetch responses; the wait is bounded by <code>fetch.max.wait.ms</code>.",
          "<b>The number of partitions caps the number of consumers that do work</b> in one group.",
          "<b>Keep the time to process one <code>poll()</code>’s records below <code>max.poll.interval.ms</code></b>, by processing faster or lowering <code>max.poll.records</code> (default 500); otherwise the consumer leaves the group and its commit fails."], CQ)}
</div>
{src(f"Apache Kafka {KV}: clients/…/consumer/ConsumerConfig.java, KafkaConsumer.java (Javadoc), CommonClientConfigs.java (MAX_POLL_INTERVAL_MS_DOC)", "results: deepdive/logs/kafka-fetch.txt, kafka-partitions.txt, kafka-pollinterval.txt")}
''', chapter=K11, color=CQ)
