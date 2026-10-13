"""Guards for the guide's prose: every sentence that interprets an output is checked against that output.
If a fresh run tells a different story, this fails and the PDF is not published."""
import csv, pathlib, re, sys

J = pathlib.Path(__file__).parent / "java"
read = lambda p: (J / p).read_text(errors="replace")
problems = []


def claim(ok, text):
    print(("ok   " if ok else "FAIL ") + text)
    if not ok:
        problems.append(text)


# PIT: one survivor before the fix (OrderApi.stop, a removed void call), none after
before = list(csv.reader(open(J / "pit-mutations-before.csv")))
surv = [r for r in before if r[5] == "SURVIVED"]
claim(len(surv) == 1 and surv[0][3] == "stop" and "VoidMethodCall" in surv[0][2],
      "PIT run 1: exactly one survivor, the removed call in OrderApi.stop()")
after = list(csv.reader(open(J / "pit-reports/mutations.csv")))
claim(all(r[5] in ("KILLED", "TIMED_OUT") for r in after), "PIT run 2: every mutant detected")
claim("Killed" in read("pit-output-stronger.txt"), "PIT STRONGER run completed")

# Coverage: unit misses OrderApi, merged reaches 100% lines and branches
cov = read("coverage-output.txt")
merged = cov.split("== MERGED")[1]
claim(re.search(r"TOTAL\s+(\d+)/\1\s+100%\s+(\d+)/\2\s+100%", merged) is not None, "merged coverage is 100% lines and branches")
unit = cov.split("== UNIT")[1].split("== INTEGRATION")[0]
claim(re.search(r"OrderApi\s+0/\d+\s+0%", unit) is not None, "unit tests alone leave OrderApi at 0%")

# JaCoCo unit report (the screenshot): OrderApi 0%, every other class 100%
idx = read("coverage/html-unit/shop/index.html")
rows = dict(re.findall(r'class="el_class">(\w+)</a></td><td class="bar"[^>]*>.*?</td><td class="ctr2"[^>]*>(\d+%)', idx))
claim(rows.get("OrderApi") == "0%" and all(v == "100%" for k, v in rows.items() if k != "OrderApi") and len(rows) > 5,
      f"JaCoCo unit report: OrderApi 0%, the other {len(rows) - 1} classes 100%")

# Parallel unit tests: each parallel run is faster than every sequential run
par = read("parallel-output.txt")
ms = lambda part: [int(x) for x in re.findall(r"finished after (\d+) ms", part)]
seq_ms, par_ms = ms(par.split("# parallel")[0]), ms(par.split("# parallel")[1])
claim(len(seq_ms) == 3 and len(par_ms) == 3 and max(par_ms) < min(seq_ms), f"parallel {par_ms} ms beats sequential {seq_ms} ms")

# Load test: the Nagle / delayed-ACK stall, and the fix
p50 = lambda t: float(re.search(r"users=1 .*?\np50\s+([\d.]+) ms", t, re.S).group(1))
slow, fast = p50(read("load-output.txt")), p50(read("load-output-nodelay.txt"))
claim(slow > 30 and slow > 10 * fast, f"Nagle stall: single-user p50 {slow} ms vs {fast} ms with TCP_NODELAY")

# Mutant demo: weak tests stay green on the mutant, boundary tests catch it
demo = read("demo-output.txt")
weak = demo.split("===== MUTANT: weak tests =====")[1].split("=====")[0]
bound = demo.split("===== MUTANT: boundary tests =====")[1]
claim("[X]" not in weak and "✘" not in weak, "weak tests pass on the mutant")
claim("[X]" in bound or "✘" in bound, "boundary tests fail on the mutant")

# Duplicate-test verdicts name these exact matches
red = read("redundancy-java.txt")
for m in ["ItemTest.InvalidQuantity.rejected#1  ≡  ItemTest.InvalidQuantity.rejected#2  ≡  ItemTest.InvalidQuantity.rejected#3",
          "DiscountPolicyTest.percentForSubtotal#4  ≡  DiscountPolicyTest.percentForSubtotal#5",
          "PasswordPolicyTest.passwordWithoutDigitIsReported  ≡  PasswordPolicyTest.passwordWithoutUpperCaseIsReported",
          "OrderApiTest.pathTricksAreJustNotFound  ≡  OrderApiTest.unknownOrderReturns404"]:
    claim(m in red, "duplicate match still present: " + m.split("  ")[0])

# CPD: the default thresholds find nothing, 25 tokens finds duplicates
cpd = dict(re.findall(r"--minimum-tokens (\d+) .*\n(\d+)", read("cpd-output.txt")))
claim("exit code: 4" in read("cpd-output.txt").split("--minimum-tokens 25")[1], "CPD exits 4 when it finds duplicates")
claim(cpd["100"] == "0" and cpd["50"] == "0" and int(cpd["25"]) > 0, f"CPD: 0 at 100 and 50 tokens, {cpd['25']} at 25")

# CI-sourced claims
cache = read("ci-logs/gradle/gradle-cache.log").split("--build-cache\n")[-1]
claim("Task :test FROM-CACHE" in cache, "build cache: the second run restored :test from the cache")
n_suite = int(re.search(r"(\d+) tests successful", read("suite-output.txt")).group(1))
shards = sum(int(re.search(r"tests run in this shard: (\d+)", read(f"ci-logs/shard-{i}/shard.log")).group(1)) for i in (1, 2))
claim(shards == n_suite, f"shards ran {shards} tests = the whole suite ({n_suite})")
claim("missing the following keys: status" in read("ci-logs/extras/pact-breaking.log"), "Pact caught the renamed field")
claim("Architecture Violation" in read("ci-logs/spring/spring-verify.log"), "ArchUnit reported the planted violation")
claim("violates unique constraint" in read("ci-logs/spring/spring-verify.log"), "PostgreSQL rejected the duplicate reference")

if problems:
    sys.exit(f"{len(problems)} claim(s) no longer hold")
