"""Measures how wide 100 monospace characters render, in each Chromium variant.
484.0 px = glyph advances kept fractional; 500.0 px = each advance rounded to a whole pixel."""
import pathlib
from playwright.sync_api import sync_playwright

G = pathlib.Path(__file__).parent
probe = G / "_probe.html"
probe.write_text("""<html><head><style>
@font-face{font-family:JB;src:url(node_modules/@fontsource/jetbrains-mono/files/jetbrains-mono-latin-400-normal.woff2)}
span{font:8.0667px JB;white-space:pre}</style></head><body><span id=s>""" + "x" * 100 + "</span></body></html>")
VARIANTS = {"default": {}, "channel=chromium": {"channel": "chromium"},
            "hinting none": {"args": ["--font-render-hinting=none"]},
            "chromium + hinting none": {"channel": "chromium", "args": ["--font-render-hinting=none"]}}
with sync_playwright() as p:
    for name, kw in VARIANTS.items():
        b = p.chromium.launch(**kw)
        pg = b.new_page()
        pg.goto(probe.as_uri())
        pg.evaluate("document.fonts.ready")
        w = pg.evaluate("document.getElementById('s').getBoundingClientRect().width")
        print(f"{name:26} {b.version:16} {w:.1f} px")
        b.close()
probe.unlink()
