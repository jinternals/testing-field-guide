"""Page machinery, highlighters and helpers shared by build.py (same design system as the HTTP, Caching and LB guides)."""
import html, re, pathlib

ROOT = pathlib.Path(__file__).parent
JAVA = ROOT / "java"
FS = "node_modules/@fontsource"

# chapter colours (all ≥ 4.5:1 on the paper colour, so they are safe for small text)
CH = {"1": "#0F766E", "2": "#1D4ED8", "3": "#6D28D9", "4": "#B45309", "5": "#B91C1C", "6": "#047857"}
# test-level colours, used consistently on every page
LV = {"unit": "#1D4ED8", "integration": "#92400E", "contract": "#6D28D9", "e2e": "#B91C1C",
      "perf": "#0E7490", "security": "#9F1239", "static": "#5B6474"}
# test double colours
DB = {"dummy": "#5B6474", "stub": "#0E7490", "spy": "#854D0E", "mock": "#6D28D9", "fake": "#047857"}


def esc(s):
    return html.escape(s, quote=False)


def chip(text, c):
    return f'<span class="mb" style="--c:{c}">{text}</span>'


def badge(text, c):
    return f'<span class="sc" style="--c:{c}">{text}</span>'


def lv(name, label=None):
    return chip(label or name, LV[name])


def dbl(name):
    return chip(name, DB[name])


# ----------------------------------------------------------------------------
# highlighters
# ----------------------------------------------------------------------------
JAVA_KW = ("abstract assert boolean break byte case catch char class const continue default do double else enum extends "
           "final finally float for goto if implements import instanceof int interface long native new package private "
           "protected public return short static strictfp super switch synchronized this throw throws transient try void "
           "volatile while var record yield sealed permits true false null").split()
JTOK = re.compile(
    r'(?P<com>//[^\n]*|/\*.*?\*/)'
    r'|(?P<str>"(?:\\.|[^"\\\n])*"|\'(?:\\.|[^\'\\\n])\')'
    r'|(?P<ann>@[A-Za-z_][\w.]*)'
    r'|(?P<kw>\b(?:' + "|".join(JAVA_KW) + r')\b)'
    r'|(?P<num>\b\d[\d_]*(?:\.\d+)?[LlFfDd]?\b)'
    r'|(?P<fn>\b[a-z_]\w*(?=\())', re.S)

def hl_java(raw):
    out, pos = [], 0
    for m in JTOK.finditer(raw):
        out.append(esc(raw[pos:m.start()]))
        cls = {"com": "t-com", "str": "t-str", "ann": "t-ann", "kw": "t-kw", "num": "t-num", "fn": "t-fn"}[m.lastgroup]
        out.append(f'<span class="{cls}">{esc(m.group(0))}</span>')
        pos = m.end()
    out.append(esc(raw[pos:]))
    return "".join(out)

XTOK = re.compile(r'(?P<com><!--.*?-->)|(?P<tag></?[\w.:-]+>?|/?>)|(?P<str>"[^"]*")', re.S)
def hl_xml(raw):
    out, pos = [], 0
    for m in XTOK.finditer(raw):
        out.append(esc(raw[pos:m.start()]))
        cls = {"com": "t-com", "tag": "t-hdr", "str": "t-str"}[m.lastgroup]
        out.append(f'<span class="{cls}">{esc(m.group(0))}</span>')
        pos = m.end()
    out.append(esc(raw[pos:]))
    return "".join(out)

def hl_props(raw):
    out = []
    for line in raw.split("\n"):
        if line.strip().startswith("#"):
            out.append(f'<span class="t-com">{esc(line)}</span>')
        elif "=" in line:
            k, v = line.split("=", 1)
            out.append(f'<span class="t-hdr">{esc(k)}</span><span class="t-dim">=</span><span class="t-str">{esc(v)}</span>')
        else:
            out.append(esc(line))
    return "\n".join(out)

def hl_sh(raw):
    out = []
    for line in raw.split("\n"):
        if line.startswith("$ "):
            out.append(f'<span class="t-dim">$</span> <span class="t-fn">{esc(line[2:])}</span>')
        elif line.strip().startswith("#"):
            out.append(f'<span class="t-com">{esc(line)}</span>')
        else:
            out.append(esc(line))
    return "\n".join(out)

def hl_out(raw):
    """JUnit console output: colour ✔/[OK] green and ✘/[X] red."""
    s = esc(raw)
    s = re.sub(r"(✔|\[OK\])", r'<span class="t-ok">\1</span>', s)
    s = re.sub(r"(✘|\[X\])", r'<span class="t-bad">\1</span>', s)
    s = re.sub(r"(^|\n)(Test run finished.*)", r'\1<span class="t-dim">\2</span>', s)
    return s

HL = {"java": hl_java, "xml": hl_xml, "props": hl_props, "sh": hl_sh, "out": hl_out, "plain": esc}


def code(raw, title=None, kind="java", cls="", right=None, label=None):
    raw = raw.strip("\n")
    body = HL[kind](raw)
    r = f'<span class="ct-r">{right}</span>' if right else ""
    t = f'<div class="code-title"><span class="dots" aria-hidden="true"><i></i><i></i><i></i></span>{title}{r}</div>' if title else ""
    extra = " out" if kind == "out" else ""
    aria = f' role="figure" aria-label="{html.escape(label or (title or "code"), quote=True)}"'
    return f'<div class="code {cls}{extra}"{aria}>{t}<pre>{body}</pre></div>'


def jfile(name, start=None, end=None, keep_imports=False, test=True, dedent=0):
    """Read a Java source file from the tested project. start/end are substrings marking the slice (inclusive)."""
    base = JAVA / ("src/test/java/shop" if test else "src/main/java/shop")
    p = base / name if (base / name).exists() else JAVA / name
    s = p.read_text()
    lines = s.split("\n")
    if not keep_imports:
        lines = [l for l in lines if not l.startswith(("package ", "import "))]
        while lines and not lines[0].strip():
            lines.pop(0)
    s = "\n".join(lines)
    if start:
        i = s.index(start)
        s = s[s.rfind("\n", 0, i) + 1:]
    if end:
        j = s.index(end) + len(end)
        s = s[:j]
    if dedent:
        s = "\n".join(l[dedent:] if l[:dedent].strip() == "" else l for l in s.split("\n"))
    return s.rstrip()


def capture(name):
    return (JAVA / name).read_text()


# ----------------------------------------------------------------------------
# page machinery
# ----------------------------------------------------------------------------
STRICT = False
PAGES = []   # (key, content, chapter, color, cls, bookmark)

def page(key, content, chapter=None, color="#0F172A", cls="", bm=None):
    PAGES.append((key, content, chapter, color, cls, bm))

def ref(key, label=None):
    return f'<a class="xref" href="#p-{key}">{label or "p." + "@@" + key + "@@"}</a>'

def head(num, kicker, title, lede, color):
    return f'''
    <div class="ch-head" style="--accent:{color}">
      <div class="ch-num" aria-hidden="true">{num}</div>
      <div><div class="kicker">{kicker}</div><h1>{title}</h1><p class="lede">{lede}</p></div>
    </div>'''

def sub(kicker, title, color):
    return f'<div class="sec-head" style="--accent:{color}"><div class="kicker">{kicker}</div><h1 class="h-sub">{title}</h1></div>'

def note(text, kind="tip", label=None):
    labels = {"tip": "Tip", "warn": "Watch out", "rule": "Rule of thumb", "info": "Good to know"}
    return f'<div class="note {kind}"><b class="nl">{label or labels[kind]}</b>{text}</div>'

def table(heads, rows, cls="", first_bold=True):
    th = "".join(f"<th>{h}</th>" for h in heads) if heads else ""
    tr = "".join("<tr>" + "".join(
        f"<td{' class=\"nm\"' if (j == 0 and first_bold) else ''}>{c}</td>" for j, c in enumerate(r)) + "</tr>" for r in rows)
    return f'<table class="tbl {cls}">{"<thead><tr>" + th + "</tr></thead>" if th else ""}<tbody>{tr}</tbody></table>'

def ticks(items, color=None, tight=True):
    st = f' style="--tick:{color}"' if color else ""
    return f'<ul class="ticks{" tight" if tight else ""}"{st}>' + "".join(f"<li>{i}</li>" for i in items) + "</ul>"

def dd(ok_h, ok, bad_h, bad):
    return (f'<div class="dd2"><div class="ok"><div class="h">{ok_h}</div><ul>{"".join(f"<li>{x}</li>" for x in ok)}</ul></div>'
            f'<div class="bad"><div class="h">{bad_h}</div><ul>{"".join(f"<li>{x}</li>" for x in bad)}</ul></div></div>')

def svg(body, w, h, label, cls="dg", style=""):
    return (f'<svg viewBox="0 0 {w} {h}" class="{cls}" role="img" aria-label="{html.escape(label, quote=True)}"'
            f'{f" style={chr(34)}{style}{chr(34)}" if style else ""}><title>{html.escape(label)}</title>{body}</svg>')

ARROW = ('<defs><marker id="{id}" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">'
         '<path d="M0,0 L8,4 L0,8 z" fill="{c}"/></marker></defs>')


# ----------------------------------------------------------------------------
# render
# ----------------------------------------------------------------------------
def ff(family, file, weight, style="normal"):
    return f"@font-face{{font-family:'{family}';src:url('{file}') format('woff2');font-weight:{weight};font-style:{style};}}"

FONTS = "\n".join([
    *[ff("Inter", f"{FS}/inter/files/inter-latin-{w}-normal.woff2", w) for w in (400, 500, 600, 700)],
    *[ff("Inter", f"{FS}/inter/files/inter-latin-{w}-italic.woff2", w, "italic") for w in (400, 600)],
    *[ff("JBM", f"{FS}/jetbrains-mono/files/jetbrains-mono-latin-{w}-normal.woff2", w) for w in (400, 500, 700)],
    *[ff("Fraunces", f"{FS}/fraunces/files/fraunces-latin-{w}-normal.woff2", w) for w in (300, 400, 600, 700, 800)],
    ff("Fraunces", f"{FS}/fraunces/files/fraunces-latin-400-italic.woff2", 400, "italic"),
])

def render(title, running):
    nums = {k: i for i, (k, *_) in enumerate(PAGES, 1)}
    body, n = [], len(PAGES)
    for i, (key, content, chapter, color, cls, bm) in enumerate(PAGES, 1):
        chrome = ""
        if i > 1:
            chrome = f'''<div class="run-head" aria-hidden="true"><span class="rh-l" style="--accent:{color}">{chapter}</span><span class="rh-r">{running}</span></div>
            <div class="run-foot-l"><a href="#p-toc">↑ Contents</a> · <a href="#p-cheat">Cheat sheet</a> · <a href="#p-index">Index</a></div>
            <div class="run-foot" aria-hidden="true"><span class="pn" style="--accent:{color}">{i:02d}</span><span class="pt">/ {n:02d}</span></div>'''
        body.append(f'<section class="page {cls}" id="p-{key}">{chrome}<div class="inner" style="--accent:{color}">{content}</div></section>')
    css = (ROOT / "style.css").read_text()
    doc = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{title}</title>
<meta name="author" content="Field Guide series"><meta name="description" content="Testing Java applications: a field guide">
<style>{FONTS}\n{css}</style></head><body>{"".join(body)}</body></html>'''
    doc = re.sub(r"@@(\w+)@@", lambda m: f"{nums[m.group(1)]:02d}" if m.group(1) in nums else (STRICT and (_ for _ in ()).throw(KeyError(m.group(1))) or "??"), doc)
    return doc, nums, [(nums[k], bm) for k, *_rest, bm in PAGES if bm]


def suite_tree(name, path="suite-output.txt"):
    """Sub-tree of one test class from the real JUnit console output, de-indented."""
    lines = capture(path).split("\n")
    i = next(k for k, l in enumerate(lines) if re.search(r"[├└]─ " + re.escape(name) + r" ✔", l))
    col = lines[i].index("─") - 1
    out = [lines[i][col:]]
    for l in lines[i + 1:]:
        if len(l) <= col or l[col] not in "│ ":
            break
        out.append(l[col:])
    out = [re.sub(r"^[├└]─ ", "", out[0])] + [l[3:] for l in out[1:]]
    return "\n".join(out)


def fail_block(method, path="failing-output.txt"):
    """The failure message the tree printer showed for one failing test method."""
    lines = capture(path).split("\n")
    i = next(k for k, l in enumerate(lines) if method + "()" in l and "[X]" in l)
    first = lines[i].split("[X]", 1)[1].strip()
    out = [first] if first else []
    for l in lines[i + 1:]:
        if re.match(r"^\s*[+'`]--", l) or not l.strip() or l.startswith("Failures"):
            break
        out.append(re.sub(r"^\s*[|]?\s{5}", "", l).replace("\t", "  "))
    return "\n".join(out)


N_TESTS = int(re.search(r"(\d+) tests successful", capture("suite-output.txt")).group(1))


# ---- versions, read from the build files (so the text can't drift from what the builds use) ----
def _build_versions():
    repo = ROOT.parent
    skip = {"java", "node_modules", "target", "build", ".git", ".venv"}
    found = {}
    def add(key, v):
        found.setdefault(key, set()).add(v)
    for p in repo.rglob("pom.xml"):
        if skip & set(p.relative_to(repo).parts):
            continue
        t = p.read_text()
        props = dict(re.findall(r"<([\w.-]+)>([^<${}]+)</\1>", (re.search(r"<properties>(.*?)</properties>", t, re.S) or [None, ""])[1]))
        for a, v in re.findall(r"<artifactId>([\w.-]+)</artifactId>\s*<version>([^<]+)</version>", t):
            add(a, re.sub(r"\$\{([\w.-]+)\}", lambda m: props.get(m.group(1), m.group(0)), v))
    for p in repo.rglob("build.gradle.kts"):
        if skip & set(p.relative_to(repo).parts):
            continue
        t = p.read_text()
        for i, v in re.findall(r'id\("([\w.-]+)"\) version "([^"]+)"', t):
            add(i, v)
        for a, v in re.findall(r'"[\w.-]+:([\w.-]+):(\d[^"]*)"', t):
            add(a, v)
    return found


_VERSIONS = _build_versions()


def V(key):
    """The one version the builds use for an artifactId or Gradle plugin id."""
    vs = _VERSIONS.get(key)
    if not vs or len(vs) != 1:
        raise SystemExit(f"version of {key}: {sorted(vs) if vs else 'not in any build file'}")
    return next(iter(vs))
