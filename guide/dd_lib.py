"""Shared helpers for the deep-dive book: CI logs, experiment sources, the machine, citations."""
from lib import *

DD = JAVA / "ci-logs" / "deepdive"
OPS = JAVA / "ci-logs" / "ops"


def dlog(name):
    return (DD / name).read_text(errors="replace")


def dsrc(path, start=None, end=None, dedent=0):
    """A slice of an experiment's source, as run in CI."""
    return jfile(f"deepdive/src/main/java/deep/{path}", start, end, dedent=dedent)


def csrc(name, start=None, end=None):
    """A jcstress test from the concurrency module."""
    return jfile(f"concurrency/src/main/java/shop/{name}", start, end)


_m = dlog("machine.txt")
MACHINE = {
    "kernel": re.search(r"kernel (\S+)", _m).group(1),
    "cpus": int(re.search(r"cpus (\d+)", _m).group(1)),
    "java": re.search(r'version "([^"]+)"', _m).group(1),
    "hz": int(re.search(r"CONFIG_HZ=(\d+)", _m).group(1)),
    "sysctl": dict(re.findall(r"^(tcp_\w+|ip_\w+)\s+(.+)$", _m, re.M)),
}
_cpu = re.search(r"Model name: ?(.+)", _m)
MACHINE["cpu"] = _cpu.group(1).strip() if _cpu else "not recorded"
RUNNER = f"GitHub Actions · Linux {MACHINE['kernel']} · {MACHINE['cpus']} CPUs · JDK {MACHINE['java']}"

# chapter accents: network blue, queues amber, JVM purple, platform green
CN, CQ, CJ, CP = CH["2"], CH["4"], CH["3"], CH["6"]


def src(*items):
    """The primary sources a page relies on, printed at its foot."""
    return '<p class="srcs"><b>Sources</b> ' + " · ".join(items) + "</p>"


def chap(n, title):
    return f"{n:02d} · {title}"


def has(name):
    """A log that newer experiments write. Missing in CI is an error; locally the page shows a gap."""
    p = DD / name
    if p.exists():
        return True
    if __import__("os").environ.get("GITHUB_ACTIONS"):
        raise SystemExit(f"missing CI log: {name}")
    return False


PENDING = '<p class="small muted">(waiting for the next CI run)</p>'


def chart(series, xs, title, ylabel, logy=False, w=300, h=150, xlabel=""):
    """A line chart drawn from measured values. series: [(name, colour, [y…])], xs: category labels."""
    import math
    L, R, T, B = 40, 8, 18, 30
    vals = [v for _, _, ys in series for v in ys if v is not None and v > 0]
    lo, hi = (min(vals), max(vals))
    if logy:
        lo, hi = 10 ** math.floor(math.log10(lo)), 10 ** math.ceil(math.log10(hi))
        f = lambda v: T + (h - T - B) * (1 - (math.log10(v) - math.log10(lo)) / (math.log10(hi) - math.log10(lo)))
        ticks = [10 ** e for e in range(int(math.log10(lo)), int(math.log10(hi)) + 1)]
    else:
        lo = 0
        step = 10 ** math.floor(math.log10(hi)) / (2 if hi / 10 ** math.floor(math.log10(hi)) < 3 else 1)
        hi = math.ceil(hi / step) * step
        f = lambda v: T + (h - T - B) * (1 - v / hi)
        ticks = [k * step for k in range(int(hi / step) + 1)]
    xpos = lambda i: L + (w - L - R) * (i / (len(xs) - 1) if len(xs) > 1 else 0.5)
    b = [f'<text x="{L}" y="10" font-size="7.4" font-weight="700" fill="#0F172A">{title}</text>']
    for t in ticks:
        y = f(t)
        lab = (f"{t:g}" if t >= 1 else f"{t:g}")
        b.append(f'<line x1="{L}" y1="{y:.1f}" x2="{w - R}" y2="{y:.1f}" stroke="#E2E8F0" stroke-width=".6"/>')
        b.append(f'<text x="{L - 3}" y="{y + 2.2:.1f}" text-anchor="end" font-size="6.2" fill="#5B6474">{lab}</text>')
    b.append(f'<text x="8" y="{(T + h - B) / 2}" font-size="6.2" fill="#5B6474" transform="rotate(-90 8 {(T + h - B) / 2})" text-anchor="middle">{ylabel}</text>')
    for i, x in enumerate(xs):
        b.append(f'<text x="{xpos(i):.1f}" y="{h - B + 10}" text-anchor="middle" font-size="6.2" fill="#5B6474">{x}</text>')
    if xlabel:
        b.append(f'<text x="{(L + w - R) / 2}" y="{h - 4}" text-anchor="middle" font-size="6.2" fill="#5B6474">{xlabel}</text>')
    for k, (name, col, ys) in enumerate(series):
        pts = [(xpos(i), f(v)) for i, v in enumerate(ys) if v is not None and v > 0]
        b.append(f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pts)}" fill="none" stroke="{col}" stroke-width="1.6"/>')
        for x, y in pts:
            b.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="1.9" fill="{col}"/>')
        b.append(f'<rect x="{L + 4 + k * 0}" y="{T + 2 + k * 9}" width="7" height="2.5" fill="{col}"/>')
        b.append(f'<text x="{L + 14}" y="{T + 5 + k * 9}" font-size="6.4" fill="{col}" font-weight="600">{name}</text>')
    label = f"{title}. " + "; ".join(f"{n}: " + ", ".join(f"{x} → {v:g}" for x, v in zip(xs, ys) if v is not None) for n, _, ys in series)
    return svg("".join(b), w, h, label)
