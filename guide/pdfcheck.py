"""PDF checks: every font embedded, tagged, document language set."""
import sys
from books import book
from pypdf import PdfReader

r = PdfReader(book()["pdf"])
root = r.trailer["/Root"]
problems = []
if root.get("/Lang") != "en":
    problems.append("document language is not set")
if not root.get("/MarkInfo", {}).get("/Marked"):
    problems.append("PDF is not tagged")
missing = set()
for page in r.pages:
    fonts = page.get("/Resources", {}).get("/Font", {})
    for f in fonts.values():
        f = f.get_object()
        if f.get("/Subtype") == "/Type3":      # glyphs drawn inline: embedded by nature
            continue
        desc = f.get("/FontDescriptor")
        if desc is None and "/DescendantFonts" in f:
            desc = f["/DescendantFonts"][0].get_object().get("/FontDescriptor")
        desc = desc.get_object() if desc else None
        if desc is None or not any(k in desc for k in ("/FontFile", "/FontFile2", "/FontFile3")):
            missing.add(str(f.get("/BaseFont")))
if missing:
    problems.append("fonts not embedded: " + ", ".join(sorted(missing)))
print(f"{len(r.pages)} pages, {len(r.outline)} top-level bookmarks")
if problems:
    sys.exit("; ".join(problems))
print("ok: fonts embedded, tagged, language set")
