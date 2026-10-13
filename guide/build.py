#!/usr/bin/env python3
"""Builds the Testing Field Guide HTML; render.py turns it into the PDF."""
import importlib, sys
import lib
for m in ["ch1", "ch2", "ch3", "ch4", "ch5", "ch6", "ch4t", "ch6q", "ch6p", "ch6c", "chx", "chy", "back"]:
    try:
        importlib.import_module(m)
    except ModuleNotFoundError as e:
        if e.name != m: raise
        print("skip", m, file=sys.stderr)
ORDER = ["cover", "toc", "why", "pyramid", "whattotest", "design", "setup", "junit", "assert", "params", "extensions", "observe", "doubles", "mockito", "mockito2", "mockpit", "legacy",
         "integ", "spring", "txtrap", "migrations", "messaging", "email", "cloud", "authmock", "wiremock", "contract", "tricky", "e2e", "perf", "sec", "tdd", "cov", "pit", "pitci", "itcov", "dupes", "plugins", "archunit", "parallel", "singleton", "speed", "ci", "conventions", "interview", "cheat", "check", "index"]
lib.PAGES.sort(key=lambda p: ORDER.index(p[0]))
assert [p[0] for p in lib.PAGES] == ORDER, [p[0] for p in lib.PAGES]
lib.STRICT = True
doc, nums, outline = lib.render("Testing Java Applications — Field Guide", "Testing · Field Guide")
(lib.ROOT / "guide.html").write_text(doc)
import ch1, html as _h
lines = []
for p, t in outline:
    lines.append(f"{p}\t{t}")
    for num, title, subt, col, items in ch1.TOC:
        if t.startswith(num + " ·"):
            for it, key in items:
                lines.append(f"{nums[key]}\t  {_h.unescape(it)}")
(lib.ROOT / "outline.txt").write_text("\n".join(lines))
print("pages:", len(lib.PAGES))
