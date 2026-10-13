"""Regenerates the guide's screenshots from the fresh outputs (run after regenerate.sh, before build.py).
- img/jacoco-unit-index-crop.png    the class table of the unit-only JaCoCo report
- img/jacoco-unit-orderapi-crop.png lines 14-31 (and the top of 32) of OrderApi.java in that report
- img/playwright-checkout.png       the screenshot Playwright took in CI, cropped"""
import pathlib
from PIL import Image
from playwright.sync_api import sync_playwright

G = pathlib.Path(__file__).parent
J, IMG = G / "java", G / "img"
UNIT = J / "coverage" / "html-unit" / "shop"

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1100, "height": 900}, device_scale_factor=2)

    pg.goto((UNIT / "index.html").as_uri())
    pg.locator("table.coverage").screenshot(path=str(IMG / "jacoco-unit-index-crop.png"))

    pg.goto((UNIT / "OrderApi.java.html").as_uri())
    # JaCoCo ids only lines with code: crop from line 14 to just above line 32
    top, nxt = pg.locator("#L14").bounding_box(), pg.locator("#L32").bounding_box()
    pre = pg.locator("pre.source").bounding_box()
    pg.screenshot(path=str(IMG / "jacoco-unit-orderapi-crop.png"), full_page=True,
                  clip={"x": pre["x"], "y": top["y"] - 4, "width": min(pre["width"], 900),
                        "height": nxt["y"] - top["y"] + 2})
    b.close()

src = J / "ci-logs" / "extras" / "twoBooksGetTheBulkDiscount.png"
Image.open(src).crop((0, 0, 560, 260)).save(IMG / "playwright-checkout.png")
for f in ["jacoco-unit-index-crop.png", "jacoco-unit-orderapi-crop.png", "playwright-checkout.png"]:
    print(f, Image.open(IMG / f).size)
