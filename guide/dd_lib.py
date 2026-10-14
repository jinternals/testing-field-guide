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
