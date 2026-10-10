#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Absolute local check for every ini entry (installed ini + ini.orig): native = computed texture or efonte's original dump PNG."""
import sys, os, re, pickle
import numpy as np
from PIL import Image
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mapping_check as M, mapping_check2 as M2, mapping_check3 as M3, decode
BASE = M.BASE
DUMPS = {}
for d, _, fs in os.walk(os.path.join(BASE, 'work/pack/ULJM05781/original')):
    for f in fs:
        m = re.match(r'^([0-9a-f]{24})\.png$', f)
        if m: DUMPS.setdefault(m.group(1), os.path.join(d, f))
ZIPUP = os.path.join(BASE, 'work/pack/ULJM05781')

def native(k):
    r = M._RECS.get(k)
    if r is not None: return decode.decode(r).astype(np.float32), 'computed'
    if k in DUMPS: return np.asarray(Image.open(DUMPS[k]).convert('RGBA')).astype(np.float32), 'dump'
    return None, None

def blocks(nat, sm, B=4):
    a, b = M2.blur(nat), M2.blur(sm)
    w = np.maximum(a[..., 3], b[..., 3]) / 255.0
    d = np.abs(a[..., :3] - b[..., :3]).mean(-1) * w + np.abs(a[..., 3] - b[..., 3])
    H, W = d.shape; B = min(B, H, W)
    return d[:H // B * B, :W // B * B].reshape(H // B, B, W // B, B).mean((1, 3))

def check(entry):
    k, p, src = entry
    nat, how = native(k)
    if nat is None: return None
    fp = os.path.join(M.PACK, p)
    if not os.path.exists(fp):
        fp = os.path.join(ZIPUP, p)  # removed spanish entries: upscale only in the zip (extracted on demand)
        if not os.path.exists(fp): return (k, p, src, how, None, None, None, None)
    H, W = nat.shape[:2]
    try: sm, f = M.load_small(fp, W, H)
    except Exception: return None
    d = blocks(nat, sm)
    return (k, p, src, how, float(d.mean()), float(np.percentile(d, 90)), float(d.max()), (W, H))

if __name__ == '__main__':
    ents = [(k, p, 'installed') for k, p in M.ini_entries(os.path.join(M.PACK, 'textures.ini'))]
    have = {k for k, _, _ in ents}
    ents += [(k, p, 'orig-only') for k, p in M.ini_entries(os.path.join(M.PACK, 'textures.ini.orig')) if k not in have]
    with ProcessPoolExecutor(initializer=M._init) as ex:
        res = [x for x in ex.map(check, ents, chunksize=32) if x]
    pickle.dump(res, open(os.path.join(BASE, 'work/mapcheck4.pkl'), 'wb'))
    from collections import Counter
    print(len(ents), 'entries;', Counter((x[2], x[3], x[4] is not None) for x in res))
