#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Relative check: does another upscaled PNG of the pack match the native image better than the mapped one?
A: downscale (BOX /4) every upscaled PNG of the pack -> work/ds/*.npy + 32x32 thumbs.
B: for every computable ini entry: shortlist by thumb L1, then full block metric; flag when the mapped file is clearly beaten."""
import sys, os, pickle, hashlib, csv
import numpy as np
from PIL import Image
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mapping_check as M, mapping_check2 as M2, decode
OURS = ('/english_remacri/', '/ui_text_remacri/', '/extra/', '/english/')
BASE = M.BASE; DS = os.path.join(BASE, 'work/ds'); os.makedirs(DS, exist_ok=True)

def dsname(rel): return os.path.join(DS, hashlib.md5(rel.encode()).hexdigest() + '.npy')

def thumb(a):
    return np.asarray(Image.fromarray(a.astype(np.uint8), 'RGBA').resize((32, 32), Image.BOX)).astype(np.float32)

def prep(rel):
    out = dsname(rel)
    try:
        im = Image.open(os.path.join(M.PACK, rel)).convert('RGBA')
    except Exception:
        return None
    W, H = im.size[0] // 4, im.size[1] // 4
    if W < 1 or H < 1: return None
    if not os.path.exists(out):
        np.save(out, np.asarray(im.resize((W, H), Image.BOX)))
    a = np.load(out)
    return rel, (W, H), thumb(a)

def tdist(a, b):
    w = np.maximum(a[..., 3], b[..., 3]) / 255.0
    return float((np.abs(a[..., :3] - b[..., :3]).mean(-1) * w).sum() / max(w.sum(), 1) + np.abs(a[..., 3] - b[..., 3]).mean())

TH = None
def _init():
    global TH
    M._init()
    TH = pickle.load(open(os.path.join(BASE, 'work/thumbs.pkl'), 'rb'))

def full(nat, rel):
    sm = np.load(dsname(rel)).astype(np.float32)
    if sm.shape != nat.shape: return None
    d = M2.blockdiff(nat, sm)
    return float(d.mean()), float(d.max())

def check(entry):
    k, p = entry
    r = M._RECS.get(k)
    if r is None or not os.path.exists(dsname(p)): return None
    nat = decode.decode(r).astype(np.float32); H, W = nat.shape[:2]
    group = [g for g in TH.get((W, H), []) if not any(x in g[0] for x in OURS)]
    nt = thumb(nat)
    cands = sorted(group, key=lambda x: tdist(nt, x[1]))[:6]
    names = [c[0] for c in cands]
    if p not in names: names.append(p)
    res = {}
    for rel in names:
        f = full(nat, rel)
        if f: res[rel] = f
    if p not in res: return None
    best = min(res, key=lambda x: res[x][0] + 0.5 * res[x][1])
    return dict(key=k, path=p, file=r['file'], W=W, H=H, mapped=res[p], best=best, bestscore=res[best])

if __name__ == '__main__':
    ents = M.ini_entries(os.path.join(M.PACK, 'textures.ini'))
    rels = sorted({p for _, p in ents} | {os.path.relpath(os.path.join(d, f), M.PACK) for root in ('ai_upscaled', 'upscaled')
                    for d, _, fs in os.walk(os.path.join(M.PACK, root)) for f in fs if f.endswith('.png')})
    if not os.path.exists(os.path.join(BASE, 'work/thumbs.pkl')):
        with ProcessPoolExecutor() as ex:
            th = [x for x in ex.map(prep, rels, chunksize=16) if x]
        g = {}
        for rel, dims, t in th: g.setdefault(dims, []).append((rel, t))
        pickle.dump(g, open(os.path.join(BASE, 'work/thumbs.pkl'), 'wb'))
        print('prepared', len(th))
    with ProcessPoolExecutor(initializer=_init) as ex:
        res = [x for x in ex.map(check, ents, chunksize=16) if x]
    pickle.dump(res, open(os.path.join(BASE, 'work/mapcheck3.pkl'), 'wb'))
    print('checked', len(res))
