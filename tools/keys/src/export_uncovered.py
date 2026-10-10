#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Export uncovered EN keys to out/uncovered_png/<category>/<key>.png and classify todo/skip.
usage: export_uncovered.py work/en.pkl"""
import sys, os, csv, pickle, re
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import decode
from PIL import Image
from collections import defaultdict, Counter
en = pickle.load(open(sys.argv[1], 'rb'))
byk = defaultdict(list)
for r in en: byk[r['key']].append(r)
rows = list(csv.DictReader(open('out/en_uncovered.csv')))
# data-hash -> number of distinct CLUT variants among ALL EN textures (palette variants evidence)
var = defaultdict(set)
for r in en: var[r['key'][16:]].add(r['key'][8:16])

def category(f):
    n = f.upper()
    rules = [('minimaps', r'^ODIF_BA_MAP'), ('battle_faces', r'^ODIF_BA_(LARGE_)?FACE'), ('odif_ui', r'^ODIF_'),
             ('enemy_chars_EC', r'^EC\d'), ('battle_chars_BC', r'^BC\d'), ('accessories_ACCE', r'^ACCE_'),
             ('ground_OMAP', r'^OMAP_'), ('char_lowpoly_LKCHARSLOW', r'^LKCHARSLOW'),
             ('weapons', r'^(SWD|SMG|SRL|TPF|PGD|SWG|TSR|RFL|RFG|PSL|LMW|MGN|REH|DAL|SS|NBG|MRT|FTH|LNC|SHG|ATR|GRN|HMG|ART|TNK|MTR)[_\d]'),
             ('ui_LKIF', r'^LKIF_'), ('ui_IF', r'^IF_'), ('events_EV', r'^EV\d'), ('lk_models_LK', r'^LK\d'),
             ('battle_abr', r'\.ABR$')]
    for c, p in rules:
        if re.search(p, n): return c
    return 'other_' + re.sub(r'[\d_].*', '', n.split('.')[0])[:12]

out_dir = 'out/uncovered_png'; todo = []; skip = []
for row in rows:
    k = row['key']; r = byk[k][0]
    img = decode.decode(r)
    cat = category(row['file'])
    os.makedirs(os.path.join(out_dir, cat), exist_ok=True)
    Image.fromarray(img, 'RGBA').save(os.path.join(out_dir, cat, k + '.png'))
    sub = img[:r['h'], :r['w']]
    a = sub[:, :, 3]; rgb = sub[:, :, :3].reshape(-1, 3)
    ncol = len(np.unique(sub.reshape(-1, 4), axis=0))
    reasons = []
    if a.max() == 0: reasons.append('fully transparent')
    elif ncol <= 2: reasons.append('blank/flat (<=2 colours)')
    if min(r['w'], r['h']) <= 8: reasons.append('tiny (<=8px side)')
    if (rgb.max(0) - rgb.min(0)).max() <= 24 and a.max() > 0 and a.min() < 255 and ncol > 2:
        reasons.append('alpha mask / single-colour gradient')
    elif ncol > 2 and np.all(rgb[:, 0] == rgb[:, 1]) and np.all(rgb[:, 1] == rgb[:, 2]) and r['w'] * r['h'] <= 64 * 64:
        reasons.append('grayscale small (effect/mask?)')
    nv = len(var[k[16:]])
    if nv > 1: reasons.append(f'palette variants: same pixels with {nv} CLUTs')  # informative, not by itself a skip
    row.update(category=cat, colours=ncol, clut_variants=nv, png=os.path.join(cat, k + '.png'))
    hard = [x for x in reasons if not x.startswith('palette variants')]
    row['reason'] = ';'.join(reasons)
    (skip if hard else todo).append(row)
fields = list(rows[0].keys())
for name, L in (('out/uncovered_todo.csv', todo), ('out/uncovered_skip.csv', skip)):
    with open(name, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(L)
print('todo', len(todo), 'skip', len(skip))
print('by category todo:', Counter(r['category'] for r in todo).most_common())
print('by category skip:', Counter(r['category'] for r in skip).most_common())
print('skip reasons:', Counter(r['reason'].split(';')[0] for r in skip).most_common())
print('palette-variant keys in uncovered:', sum(int(r['clut_variants']) > 1 for r in rows))
