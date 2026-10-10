# SPDX-License-Identifier: GPL-3.0-or-later
"""alpha-only crops (grayscale alpha, 2x zoom) + composite on light bg, for halo checks -> compare/alpha_check.png"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build import *  # noqa
items = load_inputs()
sel = [it for it in items if it.get('idx') in (0, 5, 150, 66, 17)]
models = [m for m in MODELS if m[0].split()[0] in ('interp_075', 'AnimeSharp', 'Remacri', 'UltraSharp', 'FatePlus-lite', 'blend')]
Fs = font(13)
rows = []
for it in sel:
    src = np.array(it['img']); x, y, cw, ch = CROPS.get(it['idx']) or pick_crop(src)
    box = (x * 4, y * 4, (x + cw) * 4, (y + ch) * 4)
    row = []
    for lab, p in models:
        o = Image.open(HERE / 'out' / p.stem / f"{it['name']}.png").convert('RGBA')
        a = o.getchannel('A').crop(box).convert('RGB')
        light = Image.alpha_composite(Image.new('RGBA', o.size, (235, 225, 200, 255)), o).convert('RGB').crop(box)
        row.append((lab, a, light))
    rows.append((it, row))
W = 256 * 2; Hh = 128 * 2
sheet = Image.new('RGB', (len(models) * (W // 2 + 6), len(rows) * (Hh + 22)), (20, 20, 20)); d = ImageDraw.Draw(sheet)
for r, (it, row) in enumerate(rows):
    for c, (lab, a, light) in enumerate(row):
        X, Y = c * (W // 2 + 6), r * (Hh + 22)
        d.text((X, Y + 2), lab[:38], fill=(255, 220, 90), font=Fs)
        sheet.paste(a.resize((W // 2, Hh // 2)), (X, Y + 20)); sheet.paste(light.resize((W // 2, Hh // 2)), (X, Y + 20 + Hh // 2))
sheet.save(HERE / 'alpha_check.png'); print(sheet.size)
