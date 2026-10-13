"""WCAG 2.1 AA contrast audit of every text element in guide.html (HTML text and SVG text)."""
import asyncio, json, pathlib
from playwright.async_api import async_playwright
JS = r"""() => {
  const parse = (c) => {
    if (!c) return null;
    let m = c.match(/rgba?\(([^)]+)\)/);
    if (m) { const p = m[1].split(/[ ,\/]+/).filter(Boolean).map(Number); return [p[0], p[1], p[2], p.length > 3 ? p[3] : 1]; }
    m = c.match(/color\(srgb ([^)]+)\)/);
    if (m) { const p = m[1].split(/[ \/]+/).filter(Boolean).map(Number); return [p[0]*255, p[1]*255, p[2]*255, p.length > 3 ? p[3] : 1]; }
    return null;
  };
  const lum = (c) => { const f = v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
                       return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2]); };
  const blend = (fg, bg) => [0,1,2].map(i => fg[i] * fg[3] + bg[i] * (1 - fg[3])).concat([1]);
  const bgOf = (el) => {
    const stack = [];
    for (let e = el; e; e = e.parentElement) {
      const cs = getComputedStyle(e);
      const bimg = cs.backgroundImage;
      const b = parse(cs.backgroundColor);
      if (b && b[3] > 0) { stack.push(b); if (b[3] >= 1) break; }
    }
    let bg = [255,255,255,1];
    for (let i = stack.length - 1; i >= 0; i--) bg = blend(stack[i], bg);
    return bg;
  };
  const out = [];
  const pages = [...document.querySelectorAll('section.page')];
  pages.forEach((pg, pi) => {
    const walker = document.createTreeWalker(pg, NodeFilter.SHOW_TEXT);
    const seen = new Set();
    while (walker.nextNode()) {
      const t = walker.currentNode; if (!t.textContent.trim()) continue;
      const el = t.parentElement; if (seen.has(el)) continue; seen.add(el);
      if (el.closest('[aria-hidden="true"]')) continue;
      const cs = getComputedStyle(el);
      if (cs.visibility === 'hidden' || cs.display === 'none') continue;
      let fg, bg, size = parseFloat(cs.fontSize), bold = parseInt(cs.fontWeight) >= 700;
      if (el.closest('svg')) {
        fg = parse(cs.fill); if (!fg) continue;
        bg = bgOf(el.closest('svg'));
        const tb = el.getBoundingClientRect(), cx = tb.x + tb.width / 2, cy = tb.y + tb.height / 2;
        for (const r of el.closest('svg').querySelectorAll('rect,path,circle')) {   // shapes painted under the text
          if (r.compareDocumentPosition(el) & Node.DOCUMENT_POSITION_PRECEDING) continue;  // drawn after the text
          const rb = r.getBoundingClientRect();
          if (cx < rb.left || cx > rb.right || cy < rb.top || cy > rb.bottom) continue;
          const rs = getComputedStyle(r), f = parse(rs.fill);
          if (!f) continue;
          const a = parseFloat(rs.fillOpacity) * parseFloat(rs.opacity) * f[3];
          bg = blend([f[0], f[1], f[2], a], bg);
        }
      } else { fg = parse(cs.color); bg = bgOf(el); }
      if (!fg) continue;
      const opacity = parseFloat(cs.opacity);
      if (fg[3] < 1) fg = blend(fg, bg);
      const L1 = lum(fg), L2 = lum(bg); const ratio = (Math.max(L1, L2) + 0.05) / (Math.min(L1, L2) + 0.05);
      const large = size >= 24 || (bold && size >= 18.66);
      const need = large ? 3 : 4.5;
      if (ratio < need) out.push({page: pi + 1, text: t.textContent.trim().slice(0, 40), ratio: +ratio.toFixed(2), need, fg: fg.map(Math.round).slice(0,3).join(','), bg: bg.map(Math.round).slice(0,3).join(','), cls: el.className && el.className.baseVal !== undefined ? el.className.baseVal : el.className});
    }
  });
  return out;
}"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await b.new_page()
        await pg.goto((pathlib.Path("guide.html").resolve()).as_uri()); await pg.evaluate("document.fonts.ready")
        res = await pg.evaluate(JS); await b.close()
    print(len(res), "failing text elements")
    from collections import Counter
    c = Counter((r["fg"], r["bg"], r["need"]) for r in res)
    for (fg, bg, need), n in c.most_common(30):
        ex = next(r for r in res if (r["fg"], r["bg"], r["need"]) == (fg, bg, need))
        print(f"{n:4d}  fg {fg:<13} bg {bg:<13} ratio {ex['ratio']:<5} need {need}  e.g. p{ex['page']} '{ex['text']}' cls={ex['cls']}")
    json.dump(res, open("contrast-report.json", "w"), indent=1)
asyncio.run(main())
import sys
if json.load(open("contrast-report.json")):
    sys.exit("contrast failures")
