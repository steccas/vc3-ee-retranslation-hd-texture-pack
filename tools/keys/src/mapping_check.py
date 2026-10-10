#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Check that every [hashes] entry of the installed ini maps a computable key to an upscale whose downscale matches the native image.
Phase 1 builds key->record (EN+JP, PAC, palette variants), phase 2 scores entries in parallel."""
import sys, os, re, pickle, csv
import numpy as np
from PIL import Image
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scan, texkey, decode
from collections import defaultdict
# PACK_DIR: the installed/assembled pack folder to check (contains textures.ini, optionally textures.ini.orig)
# VC3_WORKDIR: the working directory used by run_all.sh (holds dec/, work/, out/); default: current directory
BASE = os.path.abspath(os.environ.get('VC3_WORKDIR', os.getcwd()))
PACK = os.path.abspath(os.environ.get('PACK_DIR', os.path.join(BASE, 'pack', 'ULJM05957')))
CACHE = os.path.join(BASE, 'work/mapcheck_records.pkl')

def build():
    allrec = {}
    for v in ('EN', 'JP'):
        recs = scan.records(os.path.join(BASE, f'dec/DATA_{v}.BIN')); pals = list(scan.PALETTES)
        for r in recs:
            r['key'] = texkey.compute_key(r); allrec.setdefault(r['key'], r)
        # palette variants (same rules as pac_palvar.py)
        items = defaultdict(list)
        for r in recs: items[r['file'].split('/')[0]].append(('img', r['file'], r['gimoff'], r))
        for p in pals: items[p['file'].split('/')[0]].append(('pal', p['file'], p['gimoff'], p))
        def add(r, p):
            q = dict(r); q.update(palfmt=p['palfmt'], palcount=p['palcount'], pal=p['pal']); q['key'] = texkey.compute_key(q)
            q['file'] = r['file'] + ' +pal ' + p['file']; allrec.setdefault(q['key'], q)
        for top, L in items.items():
            groups = []
            for t, f, o, x in sorted(L, key=lambda z: (z[1], z[2])):
                if not groups or groups[-1][0] != f: groups.append([f, [], []])
                (groups[-1][1] if t == 'img' else groups[-1][2]).append(x)
            imgs = None
            for f, I, P in groups:
                if I: imgs = I
                src = I or imgs
                if P and src:
                    cl = [r for r in src if r['fmt'] in (4, 5)]
                    if len(cl) == len(P):
                        for r, p in zip(cl, P): add(r, p)
        fam = {'LKENPALETTE_EMPIRE.MLX': r'^LK0(6[5-9]|7[0-2])', 'LKENPALETTE_CR.MLX': r'^LK(07[3-9]|080|319)',
               'LKENPALETTE_GARIA.MLX': r'^LK(08[1-8]|318)', 'CANVAS_F00_PLT.HCL': r'^CANVAS_F00\.HTX'}
        for pf, pat in fam.items():
            P = [p for p in pals if p['file'] == pf]
            for r in recs:
                if r['fmt'] in (4, 5) and re.match(pat, r['file']):
                    for p in P:
                        if r['fmt'] == 5 and p['palcount'] < 256: continue
                        add(r, p)
    # keep only what we need to decode
    slim = {k: {x: r[x] for x in ('file', 'gimoff', 'fmt', 'order', 'w', 'h', 'bpp', 'pitch', 'hal', 'pix', 'pixlen', 'palfmt', 'palcount', 'pal') if x in r} for k, r in allrec.items()}
    for r in slim.values(): r['pix'] = r['pix'][:r['pitch'] * r['hal']]
    pickle.dump(slim, open(CACHE, 'wb'))
    return slim

def ini_entries(path):
    out = []; sec = None
    for line in open(path, encoding='utf-8', errors='replace'):
        s = line.strip()
        if s.startswith('['): sec = s; continue
        if sec != '[hashes]': continue
        m = re.match(r'^([0-9a-f]{24})(?:_\d+)?\s*=\s*(\S+)', s)
        if m: out.append((m.group(1), m.group(2)))
    return out

def load_small(path, W, H):
    im = Image.open(path).convert('RGBA')
    if im.size == (W, H): return np.asarray(im).astype(np.float32), 1.0
    f = im.size[0] / W
    return np.asarray(im.resize((W, H), Image.BOX)).astype(np.float32), f

def score(a, b):
    """mean abs diff: RGB weighted by max alpha (transparent pixels don't count) + alpha diff."""
    w = np.maximum(a[..., 3], b[..., 3]) / 255.0
    rgb = (np.abs(a[..., :3] - b[..., :3]).mean(-1) * w).sum() / max(w.sum(), 1)
    al = np.abs(a[..., 3] - b[..., 3]).mean()
    return float(rgb + al)

_RECS = None
def _init():
    global _RECS
    _RECS = pickle.load(open(CACHE, 'rb'))

def check(entry):
    k, p = entry
    r = _RECS.get(k)
    fp = os.path.join(PACK, p)
    if r is None: return (k, p, 'not computable', None, None)
    if not os.path.exists(fp): return (k, p, 'missing file', None, None)
    nat = decode.decode(r).astype(np.float32)
    H, W = nat.shape[:2]
    try:
        sm, f = load_small(fp, W, H)
    except Exception as ex:
        return (k, p, 'unreadable ' + str(ex)[:40], None, None)
    return (k, p, 'ok', score(nat, sm), round(f, 3))

if __name__ == '__main__':
    if not os.path.exists(CACHE): build()
    ents = ini_entries(os.path.join(PACK, 'textures.ini'))
    with ProcessPoolExecutor(initializer=_init) as ex:
        res = list(ex.map(check, ents, chunksize=32))
    pickle.dump(res, open(os.path.join(BASE, 'work/mapcheck_scores.pkl'), 'wb'))
    from collections import Counter
    print(Counter(x[2] if not x[2].startswith('unreadable') else 'unreadable' for x in res))
    sc = np.array([x[3] for x in res if x[3] is not None])
    print('scores percentiles', {q: round(float(np.percentile(sc, q)), 2) for q in (50, 90, 95, 98, 99, 99.5, 99.9)})
