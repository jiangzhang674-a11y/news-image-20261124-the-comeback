#!/usr/bin/env python3
"""THE COMEBACK — LOCAL BUILD TOOL ONLY (not the competition entrypoint).

Builds the front page from news/news-20261124.json and rasterises it with
Pillow + system fonts:
  output/frontpage.svg      intermediate, deterministic SVG
  output/entry.png           724 x 1024 px (inside the competition gate:
                            at most 1024 x 1024 px, at most 1 MiB)
  entry.png                  copy of output/entry.png at the repo root —
                            the pre-rendered asset the entrypoint main.py
                            copies to the grader's output directory.

The competition entrypoint is main.py (stdlib only, copy-only). This script
is never run in the sandbox; it only exists so the artwork can be rebuilt
and re-checked locally. It deliberately does NOT produce a 2480 x 3508
submission.png — that size breaks the gate and must not be in the repo.

Run:  python3 build_frontpage.py
Re-running produces a byte-identical entry.png.
"""

import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------- paths
HERE = Path(__file__).resolve().parent
BASE = HERE if (HERE / "news").is_dir() else HERE.parent
NEWS_PATH = BASE / "news" / "news-20261124.json"
OUT_DIR = BASE / "output"

# ---------------------------------------------------------------- canvas
W, H = 1240, 1754            # SVG units; A4 ratio 1 : 1.4142
M = 56                       # page margin
CW = W - 2 * M               # 1128 content width
PAPER = "#FAF6EF"
INK = "#141414"
ACCENT = "#9A1B1E"           # dark red for kickers / rules
GREY = "#555555"
GREEN = "#1F6B3A"

FONTS = {
    "serif-bold": "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
    "serif": "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
    "serif-italic": "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf",
    "sans-bold": "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "sans": "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
}

_font_cache = {}


def font(key, size):
    k = (key, int(round(size)))
    if k not in _font_cache:
        _font_cache[k] = ImageFont.truetype(FONTS[key], int(round(size)))
    return _font_cache[k]


def text_w(text, key, size):
    return font(key, size).getlength(text)


def wrap(text, key, size, max_w):
    """Greedy word wrap using real font metrics; returns list of lines."""
    words, lines, cur = text.split(), [], ""
    for word in words:
        trial = (cur + " " + word).strip()
        if text_w(trial, key, size) <= max_w - 4:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def fit_lines(text, key, start_size, max_lines, max_w, min_size=40):
    """Shrink the font until the text wraps into at most max_lines lines."""
    size = start_size
    while size > min_size:
        lines = wrap(text, key, size, max_w)
        if len(lines) <= max_lines:
            return size, lines
        size -= 4
    return size, wrap(text, key, size, max_w)


def headline_lines(text, key, start_size, max_w, min_size=40):
    """Headline on one line if it fits, else two balanced lines.

    Tries every word split and keeps the one whose longest line is
    shortest, so 'HUANG IS BACK' / 'AT NVIDIA' instead of a ragged break.
    """
    size = start_size
    while size > min_size:
        if text_w(text, key, size) <= max_w - 4:
            return size, [text]
        words = text.split()
        best = None
        for i in range(1, len(words)):
            a, b = " ".join(words[:i]), " ".join(words[i:])
            w = max(text_w(a, key, size), text_w(b, key, size))
            if w <= max_w - 4 and (best is None or w < best[0]):
                best = (w, [a, b])
        if best is not None:
            return size, best[1]
        size -= 4
    return size, wrap(text, key, size, max_w)


# ---------------------------------------------------------------- SVG doc
class SVG:
    def __init__(self):
        self.el = []

    def rect(self, x, y, w, h, fill, stroke=None, sw=0):
        s = f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{fill}"'
        if stroke:
            s += f' stroke="{stroke}" stroke-width="{sw}"'
        self.el.append(s + " />")

    def line(self, x1, y1, x2, y2, stroke, sw):
        self.el.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{stroke}" stroke-width="{sw}" />')

    def circle(self, cx, cy, r, fill, stroke=None, sw=0):
        s = f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{fill}"'
        if stroke:
            s += f' stroke="{stroke}" stroke-width="{sw}"'
        self.el.append(s + " />")

    def text(self, x, y, s, key, size, fill=INK, anchor="start"):
        self.el.append(
            f'<text x="{x:.1f}" y="{y:.1f}" font-family="{key}" '
            f'font-size="{size}" fill="{fill}" text-anchor="{anchor}">'
            f"{escape(s)}</text>")

    def doc(self):
        body = "\n".join(self.el)
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'viewBox="0 0 {W} {H}">\n'
            f'<rect x="0" y="0" width="{W}" height="{H}" fill="{PAPER}" />\n'
            f"{body}\n</svg>\n")


# ---------------------------------------------------------------- layout
def badge(svg, x, y, n):
    """Numbered story badge: accent square + white number."""
    svg.rect(x, y - 20, 26, 26, ACCENT)
    svg.text(x + 13, y, str(n), "sans-bold", 19, fill="#FFFFFF", anchor="middle")


def build(data):
    svg = SVG()
    stories = {s["id"]: s for s in data["stories"]}
    lead = stories["huang-nvidia"]

    # ---- masthead
    svg.rect(M, 28, CW, 4, INK)
    mast = "THE COMEBACK"
    mast_size = 148
    while text_w(mast, "serif-bold", mast_size) > CW and mast_size > 60:
        mast_size -= 4
    svg.text(W / 2, 182, mast, "serif-bold", mast_size, anchor="middle")
    svg.rect(M, 202, CW, 5, INK)
    svg.rect(M, 212, CW, 2, INK)
    # ---- dateline
    svg.text(M, 250, "Tuesday 24 November 2026", "sans-bold", 25)
    svg.text(W - M, 250, "NINE STORIES FROM AROUND THE GLOBE", "sans-bold", 25, anchor="end")
    svg.rect(M, 268, CW, 2, INK)

    y = 304  # cursor (baseline of next kicker)

    # ---- lead story (No. 1)
    badge(svg, M, y, "1")
    svg.text(M + 40, y, lead["kicker"], "sans-bold", 26, fill=ACCENT)
    y += 14
    size, lines = headline_lines(lead["headline"], "serif-bold", 100, CW)
    assert len(lines) <= 2, f"lead headline still {len(lines)} lines"
    for ln in lines:
        y += 88
        svg.text(M, y, ln, "serif-bold", size)
    y += 22
    for ln in wrap(lead["standfirst"], "serif-italic", 32, CW):
        y += 35
        svg.text(M, y, ln, "serif-italic", 32)
    # stat strip: +31% / $4.0T / 11 DAYS — the three required figures
    y += 22
    box_w, box_h, gap = (CW - 2 * 18) / 3, 88, 18
    for i, st in enumerate(lead["stats"]):
        bx = M + i * (box_w + gap)
        svg.rect(bx, y, box_w, box_h, "#FFFFFF", stroke=INK, sw=2)
        svg.text(bx + box_w / 2, y + 52, st["value"], "sans-bold", 48, anchor="middle")
        svg.text(bx + box_w / 2, y + 80, st["label"], "sans", 21, fill=GREY, anchor="middle")
    y += box_h + 20
    # v3: lead body dropped — its facts are already in the standfirst and
    # the stat strip; the space goes to the 9th story (Tiangong) below.
    svg.rect(M, y, CW, 3, INK)
    y += 26

    # ---- stories 2-4: numbered medium blocks
    mid = [stories["myanmar-icj"], stories["climate-cop31"], stories["ukraine-libya"]]
    for num, st in zip(("2", "3", "4"), mid):
        badge(svg, M, y, num)
        svg.text(M + 40, y, st["kicker"], "sans-bold", 25, fill=ACCENT)
        y += 12
        size, lines = headline_lines(st["headline"], "serif-bold", 50, CW)
        assert len(lines) <= 2, f"headline {st['id']} still {len(lines)} lines"
        for ln in lines:
            y += 48
            svg.text(M, y, ln, "serif-bold", size)
        y += 8
        blines = wrap(st["body"][0], "serif", 24, CW)
        assert len(blines) <= 2, f"body {st['id']} wraps to {len(blines)} lines"
        for ln in blines:
            y += 28
            svg.text(M, y, ln, "serif", 24)
        y += 10
        svg.rect(M, y, CW, 2, INK)
        y += 22

    # ---- stories 5-8: 2x2 brief grid
    grid = [stories["nepal-quake"], stories["gaza-strikes"],
            stories["awacs-poland"], stories["factory-fire"]]
    col_w = (CW - 36) / 2
    card_h, row_gap = 118, 10
    grid_top = y
    for row in range(2):
        for col in range(2):
            st = grid[row * 2 + col]
            num = str(5 + row * 2 + col)
            cx = M + col * (col_w + 36)
            cy = grid_top + row * (card_h + row_gap)
            badge(svg, cx, cy, num)
            svg.text(cx + 40, cy, st["kicker"], "sans-bold", 21, fill=ACCENT)
            size, lines = fit_lines(st["headline"], "serif-bold", 30, 2, col_w)
            hy = cy + 38
            for ln in lines:
                svg.text(cx, hy, ln, "serif-bold", size)
                hy += 36
            by = hy + 4
            blines = wrap(st["body"][0], "serif", 20, col_w)
            assert len(blines) <= 2, f"grid body {st['id']} wraps to {len(blines)} lines"
            for ln in blines:
                svg.text(cx, by, ln, "serif", 20)
                by += 26
    svg.line(M + col_w + 18, grid_top - 6, M + col_w + 18,
             grid_top + 2 * card_h + row_gap, GREY, 1)
    y = grid_top + 2 * card_h + row_gap + 14

    # ---- story 9: ALSO strip, full width (v3: space + named person)
    st9 = stories["tiangong-shenzhou24"]
    y += 12
    badge(svg, M, y, "9")
    svg.text(M + 40, y, st9["kicker"], "sans-bold", 24, fill=ACCENT)
    y += 12
    size, lines = headline_lines(st9["headline"], "serif-bold", 40, CW)
    assert len(lines) <= 1, f"strip headline {len(lines)} lines"
    for ln in lines:
        y += 42
        svg.text(M, y, ln, "serif-bold", size)
    y += 4
    blines = wrap(st9["body"][0], "serif", 23, CW)
    assert len(blines) <= 2, f"strip body wraps to {len(blines)} lines"
    for ln in blines:
        y += 26
        svg.text(M, y, ln, "serif", 23)
    y += 6

    # ---- market strip (verified numbers only: +31% and $4.0T)
    svg.rect(M, y, CW, 42, INK)
    svg.text(W / 2, y + 29, "MARKETS — NVIDIA +31% AS HUANG RETURNS · VALUE BACK NEAR $4.0T",
             "sans-bold", 22, fill="#FFFFFF", anchor="middle")
    y += 42 + 6

    # ---- footer
    assert y <= 1700, f"layout overflow: y={y}"
    svg.rect(M, y, CW, 2, INK)
    svg.text(M, y + 30, "THE COMEBACK — Tuesday 24 November 2026",
             "sans-bold", 20)
    return svg.doc()


# ---------------------------------------------------------------- rasterise
def rasterise(svg_text, out_path, target_w, target_h):
    root = ET.fromstring(svg_text)
    scale = target_w / W
    assert abs(target_h - H * scale) < 2, "target size breaks A4 ratio"
    img = Image.new("RGB", (target_w, target_h), PAPER)
    d = ImageDraw.Draw(img)

    def S(v):
        return v * scale

    for el in root:
        tag = el.tag.split("}")[-1]
        if tag == "rect":
            x, y = S(float(el.get("x"))), S(float(el.get("y")))
            w, h = S(float(el.get("width"))), S(float(el.get("height")))
            fill = el.get("fill")
            sw = float(el.get("stroke-width", "0")) * scale
            d.rectangle([x, y, x + w, y + h], fill=fill,
                        outline=el.get("stroke"), width=max(1, int(round(sw))) if sw else 1)
        elif tag == "line":
            d.line([S(float(el.get("x1"))), S(float(el.get("y1"))),
                    S(float(el.get("x2"))), S(float(el.get("y2")))],
                   fill=el.get("stroke"), width=max(1, int(round(float(el.get("stroke-width", "1")) * scale))))
        elif tag == "circle":
            cx, cy, r = S(float(el.get("cx"))), S(float(el.get("cy"))), S(float(el.get("r")))
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=el.get("fill"),
                      outline=el.get("stroke"))
        elif tag == "text":
            key = el.get("font-family")
            size = float(el.get("font-size")) * scale
            fnt = font(key, size)
            anchor = {"start": "ls", "middle": "ms", "end": "rs"}[el.get("text-anchor", "start")]
            d.text((S(float(el.get("x"))), S(float(el.get("y")))),
                   el.text or "", font=fnt, fill=el.get("fill"), anchor=anchor)
    img.save(out_path, format="PNG")
    return img


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    data = json.loads(NEWS_PATH.read_text(encoding="utf-8"))
    svg_text = build(data)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "frontpage.svg").write_text(svg_text, encoding="utf-8")

    sub = OUT_DIR / "submission.png"
    if sub.exists():
        sub.unlink()  # 2480 x 3508 breaks the gate; never ship it
    entry = OUT_DIR / "entry.png"
    rasterise(svg_text, entry, 724, 1024)
    # pre-rendered asset at the repo root, for the copy-only entrypoint
    import shutil
    shutil.copyfile(entry, BASE / "entry.png")

    im = Image.open(entry)
    print(f"{entry.name}: {im.size[0]}x{im.size[1]}  {entry.stat().st_size} bytes  "
          f"sha256={sha256(entry)[:16]}...")
    # determinism: run the rasteriser a second time and compare bytes
    again = OUT_DIR / ".again.png"
    rasterise(svg_text, again, 724, 1024)
    assert sha256(again) == sha256(entry), "non-deterministic output!"
    again.unlink()
    print("determinism: OK (two runs byte-identical)")
    print(f"svg: {(OUT_DIR / 'frontpage.svg').stat().st_size} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
