#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Local (block) mismatch metrics for ini mappings: catches small wrong regions (e.g. a different digit)."""
import sys, os, pickle
import numpy as np
from PIL import Image, ImageFilter
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mapping_check as M, decode
BASE = M.BASE

def blur(a):
    im = Image.fromarray(a.astype(np.uint8), 'RGBA')
    return np.asarray(im.filter(ImageFilter.GaussianBlur(1.0))).astype(np.float32)

def blockdiff(nat, sm, B=8):
    a, b = blur(nat), blur(sm)
    w = np.maximum(a[..., 3], b[..., 3]) / 255.0
    d = np.abs(a[..., :3] - b[..., :3]).mean(-1) * w + np.abs(a[..., 3] - b[..., 3])
    H, W = d.shape; B = min(B, H, W)
    d = d[:H // B * B, :W // B * B].reshape(H // B, B, W // B, B).mean((1, 3))
    return d

def check(entry):
    k, p = entry
    r = M._RECS.get(k); fp = os.path.join(M.PACK, p)
    if r is None or not os.path.exists(fp): return None
    nat = decode.decode(r).astype(np.float32); H, W = nat.shape[:2]
    try: sm, f = M.load_small(fp, W, H)
    except Exception: return None
    d = blockdiff(nat, sm)
    return (k, p, float(d.mean()), float(np.median(d)), float(d.max()), float(np.percentile(d, 98)), r['file'], W, H)

if __name__ == '__main__':
    ents = M.ini_entries(os.path.join(M.PACK, 'textures.ini'))
    with ProcessPoolExecutor(initializer=M._init) as ex:
        res = [x for x in ex.map(check, ents, chunksize=32) if x]
    pickle.dump(res, open(os.path.join(BASE, 'work/mapcheck2.pkl'), 'wb'))
    mx = np.array([x[4] for x in res]); mean = np.array([x[2] for x in res])
    print(len(res), 'max-block pct', {q: round(float(np.percentile(mx, q)), 1) for q in (50, 90, 99, 99.5)}, 'mean pct', {q: round(float(np.percentile(mean, q)), 1) for q in (50, 99)})
