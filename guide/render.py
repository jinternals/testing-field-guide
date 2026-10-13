import asyncio, pathlib, sys
from playwright.async_api import async_playwright
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, BooleanObject, DictionaryObject

ROOT = pathlib.Path(__file__).parent
RAW, OUT = ROOT / "raw.pdf", ROOT / "Testing-Field-Guide.pdf"

CHECK = """() => {
  const out=[];
  document.querySelectorAll('section.page').forEach((s,i)=>{
    const inner=s.querySelector('.inner'); const ib=inner.getBoundingClientRect();
    let maxB=0, maxR=0;
    inner.querySelectorAll('*').forEach(el=>{const r=el.getBoundingClientRect(); if(r.height>0&&r.width>0){maxB=Math.max(maxB,r.bottom); maxR=Math.max(maxR,r.right);}});
    const clip=[...s.querySelectorAll('pre')].filter(p=>p.scrollWidth>p.clientWidth+1).map(p=>p.closest('.code').querySelector('.code-title')?.innerText||'?');
    const overflowCells=[...s.querySelectorAll('td,th,.card,.concept-card,.note,.cbox,.q,.vs,.ck')].filter(e=>e.scrollWidth>e.clientWidth+2).length;
    out.push({page:i+1, id:s.id, spare_mm:+((ib.bottom-maxB)/3.78).toFixed(1), right_over_mm:+((maxR-ib.right)/3.78).toFixed(1), clipped_pre:clip, overflow:overflowCells});
  });
  return out;}"""

PROBLEMS = []

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page()
        await pg.goto((ROOT / "guide.html").as_uri())
        await pg.evaluate("document.fonts.ready")
        await pg.wait_for_timeout(300)
        fitted = await pg.evaluate("""() => { const out=[]; document.querySelectorAll('.code pre').forEach(p=>{
            if (getComputedStyle(p).whiteSpace!=='pre') return;
            let fs=parseFloat(getComputedStyle(p).fontSize); const start=fs;
            while (p.scrollWidth>p.clientWidth+1 && fs>8.25) { fs-=0.2; p.style.fontSize=fs+'px'; }
            if (fs<start) out.push((p.closest('.code').querySelector('.code-title')?.innerText||'?').split('\\n')[0]+' '+(fs*0.75).toFixed(2)+'pt'); });
            return out; }""")
        print("auto-fitted:", fitted)
        for r in await pg.evaluate(CHECK):
            hard = r["id"] != "p-cover" and (r["spare_mm"] < 0 or r["right_over_mm"] > 0.5 or r["clipped_pre"] or r["overflow"])
            flag = hard or (r["id"] != "p-cover" and r["spare_mm"] > 25)
            if hard:
                PROBLEMS.append(r["id"])
            print(("!! " if flag else "   ") + str(r))
        await pg.pdf(path=str(RAW), format="A4", print_background=True, prefer_css_page_size=True,
                     margin={"top": "0", "bottom": "0", "left": "0", "right": "0"}, tagged=True, outline=False)
        await b.close()

asyncio.run(main())

w = PdfWriter(clone_from=PdfReader(RAW))
parent = None
for line in (ROOT / "outline.txt").read_text().splitlines():
    pnum, title = line.split("\t", 1)
    if title.startswith("  "):
        w.add_outline_item(title.strip(), int(pnum) - 1, parent=parent)
    else:
        parent = w.add_outline_item(title.replace("&amp;", "&"), int(pnum) - 1)
w.page_mode = "/UseOutlines"
w.add_metadata({"/Title": "Testing Java Applications — Field Guide",
                "/Subject": "Unit, integration, API, end-to-end, performance and security testing in Java with JUnit 6, Mockito and AssertJ",
                "/Keywords": "Java, testing, JUnit 6, Mockito, AssertJ, TDD, mutation testing, Testcontainers"})
root = w._root_object
root[NameObject("/Lang")] = __import__("pypdf").generic.TextStringObject("en")
vp = DictionaryObject(); vp[NameObject("/DisplayDocTitle")] = BooleanObject(True)
root[NameObject("/ViewerPreferences")] = vp
with open(OUT, "wb") as f:
    w.write(f)
print("written", OUT.name, len(w.pages), "pages")
if PROBLEMS:
    sys.exit(f"layout problems on: {', '.join(PROBLEMS)}")
