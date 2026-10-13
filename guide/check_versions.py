"""Every version number the guide states must be the one the builds use.
Collects x.y.z versions from the guide's text (outside code listings, which are cut from the real
files anyway) and fails if one does not appear in a build file, the wrapper, the workflow, or a
dependency list the CI builds printed. After a Dependabot bump, this points at the stale sentence."""
import html, pathlib, re, sys

G = pathlib.Path(__file__).parent
REPO = G.parent
VER = re.compile(r"(?<![\w.])\d+\.\d+\.\d+(?:\.\d+)?(?![\w.])")

sources = [p for p in REPO.rglob("*") if p.is_file() and not {"java", "node_modules", ".git", "target", "build", ".venv"} & set(p.relative_to(REPO).parts)
           and (p.name in ("pom.xml", "build.gradle.kts", "gradle-wrapper.properties", "regenerate.sh", "package.json") or p.suffix == ".yml")]
sources += [p for p in (G / "java" / "ci-logs").rglob("*.txt")]          # spring-deps.txt, mvn.txt, java.txt …
known = set()
for p in sources:
    known |= set(VER.findall(p.read_text(errors="replace")))

page = (G / "guide.html").read_text()
text = re.sub(r"<pre.*?</pre>|<style.*?</style>|<script.*?</script>", " ", page, flags=re.S)
text = html.unescape(re.sub(r"<[^>]+>", " ", text))
stated = {}
for m in VER.finditer(text):
    stated.setdefault(m.group(0), text[max(0, m.start() - 40):m.end() + 10].split("\n")[-1].strip())

missing = {v: ctx for v, ctx in stated.items() if v not in known}
print(f"{len(stated)} versions in the text, {len(known)} in {len(sources)} build files and CI dependency lists")
for v, ctx in sorted(missing.items()):
    print(f"NOT IN ANY BUILD FILE  {v:<12} …{ctx}")
if missing:
    sys.exit(f"{len(missing)} version(s) in the guide differ from the builds")
print("ok: every version in the text is the one the builds use")
