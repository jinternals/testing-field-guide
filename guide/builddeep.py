#!/usr/bin/env python3
"""Builds the deep-dive book's HTML; `render.py deep` turns it into the PDF."""
import importlib, sys
import lib
lib.FOOT_LINKS = [("toc", "↑ Contents"), ("method", "How it was measured"), ("dindex", "Index")]
lib.META_DESC = "Java performance deep dives: TCP, timeouts, pools, latency, JIT, GC, virtual threads, containers, memory model"
MODULES = ["dd1", "dd2", "dd3", "dd4", "dd5", "dd_front", "dd_back"]
for m in MODULES:
    try:
        importlib.import_module(m)
    except ModuleNotFoundError as e:
        if e.name != m:
            raise
        print("skip", m, file=sys.stderr)
ORDER = ["dcover", "toc", "method", "nagle", "nagle2", "conn", "conn2", "timeouts", "timeouts2", "pools", "pools2", "co", "co2",
         "jit", "jit2", "gc", "gc2", "vt", "vt2", "box", "box2", "jmm", "jmm2", "dsources", "dindex"]
ORDER = [k for k in ORDER if any(p[0] == k for p in lib.PAGES)]
lib.PAGES.sort(key=lambda p: ORDER.index(p[0]))
assert [p[0] for p in lib.PAGES] == ORDER, [p[0] for p in lib.PAGES]
lib.STRICT = True
doc, nums, outline = lib.render("Java Performance Deep Dives", "Deep Dives · Java")
(lib.ROOT / "deep.html").write_text(doc)
(lib.ROOT / "deep-outline.txt").write_text("\n".join(f"{p}\t{t}" for p, t in outline))
print("pages:", len(lib.PAGES))
