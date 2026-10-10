# SPDX-License-Identifier: GPL-3.0-or-later
"""Validation by image content: is the JP texture's image in the pack, and under which key?"""
import sys, os, pickle, hashlib, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import decode, texkey
from collections import Counter, defaultdict
recs = pickle.load(open('work/jp_keyed.pkl', 'rb'))
idx = pickle.load(open('work/packidx.pkl', 'rb'))
print('pack pngs', len(idx), 'unreadable', sum(1 for x in idx if x[3] is None))
byfull = defaultdict(set); byrgb = defaultdict(set)
for p, w, h, m, mr in idx:
    k = re.search(r'([0-9a-f]{24})', os.path.basename(p))
    if m and k: byfull[m].add(k.group(1)); byrgb[mr].add(k.group(1))
stat = Counter(); wrong = []
for r in recs:
    img = decode.decode(r)
    if img is None: stat['nodecode'] += 1; continue
    m = hashlib.md5(img.tobytes()).hexdigest(); mr = hashlib.md5(img[:, :, :3].tobytes()).hexdigest()
    r['md5'] = m
    ks = byfull.get(m)
    import numpy as _np
    if ks and len(_np.unique(img.reshape(-1, 4), axis=0)) <= 2: stat["(trivial <=2-colour image, ambiguous)"] += 1; r["trivial"] = True
    if r['inpack'] is True:
        stat['key match'] += 1
        stat['key match & image identical' if ks and r['key'] in ks else 'key match, image differs'] += 1
    elif ks:
        stat['image in pack under other key'] += 1
        wrong.append((r['file'], r['key'], sorted(ks)[:4], r['fmt'], r.get('palfmt'), r['w'], r['h']))
    else:
        stat['image not in pack' + (' (data-hash match)' if r['inpack'] == 'data-only' else '')] += 1
for k, v in sorted(stat.items()): print(f'{v:6d}  {k}')
print('examples of formula errors:')
for x in wrong[:20]: print(' ', x)
pickle.dump(wrong, open('work/formula_errors.pkl', 'wb'))
pickle.dump(recs, open('work/jp_keyed.pkl', 'wb'))
