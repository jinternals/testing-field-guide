"""Writes Testing-Field-Guide.html: guide.html with fonts and images inlined, so the one file
opens in any browser (and prints to the same PDF). CI commits it to docs/ next to the PDF."""
from books import book
import base64, pathlib, re

G = pathlib.Path(__file__).parent
MIME = {".woff2": "font/woff2", ".png": "image/png", ".svg": "image/svg+xml", ".jpg": "image/jpeg"}


def data(rel):
    p = G / rel
    return f"data:{MIME[p.suffix]};base64," + base64.b64encode(p.read_bytes()).decode()


B = book()
OUT = B["pdf"].replace(".pdf", ".html")
h = (G / B["html"]).read_text()
h = re.sub(r"url\('((?:node_modules|img)/[^']+)'\)", lambda m: f"url('{data(m.group(1))}')", h)
h = re.sub(r'src="(img/[^"]+)"', lambda m: f'src="{data(m.group(1))}"', h)
left = re.findall(r"""(?:url\(['"]?|src=")(?!data:|#|https?:)([^'")]+)""", h)
assert not left, f"still external: {left[:5]}"
(G / OUT).write_text(h)
print(f"{OUT} {len(h) / 1e6:.1f} MB, self-contained")
