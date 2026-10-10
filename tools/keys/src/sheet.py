# SPDX-License-Identifier: GPL-3.0-or-later
import sys, os, pickle, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mapping_check as M, mapping_check4 as M4
from PIL import Image, ImageDraw
M._init()
def sheet(items, out, T=160):
    """items: list of (key, path_mapped, path_fix or None, label)"""
    s = Image.new('RGBA', (3 * (T + 6), len(items) * (T + 14)), (40, 40, 40, 255)); dr = ImageDraw.Draw(s)
    for i, (k, p, fx, lab) in enumerate(items):
        nat, _ = M4.native(k)
        ims = [Image.fromarray(nat.astype(np.uint8))]
        for q in (p, fx):
            if not q: ims.append(None); continue
            fp = q if os.path.isabs(q) else (os.path.join(M.PACK, q) if os.path.exists(os.path.join(M.PACK, q)) else os.path.join(M4.ZIPUP, q))
            ims.append(Image.open(fp).convert('RGBA'))
        for j, im in enumerate(ims):
            if im is None: continue
            im = im.copy(); im.thumbnail((T, T), Image.NEAREST if j == 0 else Image.BOX)
            s.alpha_composite(im, (j * (T + 6), i * (T + 14)))
        dr.text((0, i * (T + 14) + T), lab[:90], fill=(255, 255, 0, 255))
    s.save(out)
