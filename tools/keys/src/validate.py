# SPDX-License-Identifier: GPL-3.0-or-later
import sys, os, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import texkey, packkeys
from collections import Counter
recs = pickle.load(open(sys.argv[1], 'rb'))
keys = packkeys.load(sys.argv[2])
inpack_data = {k[16:] for k in keys}
full = 0; dataonly = 0; none = 0; produced = set(); uniq = set()
for r in recs:
    k = texkey.compute_key(r)
    if k is None: none += 1; continue
    k2 = texkey.compute_key(r, 0xF0) if r['fmt'] in (4,5,6,7) else None
    uniq.add(k)
    r['key'] = k
    if k in keys or (k2 and k2 in keys):
        full += 1; produced.add(k if k in keys else k2); r['inpack'] = True
    elif k[16:] in inpack_data:
        dataonly += 1; r['inpack'] = 'data-only'
    else:
        r['inpack'] = False
n = len(recs)
print(f'records {n}, unique keys {len(uniq)}')
print(f'full-key match {full} ({100*full/n:.1f}%), data-hash only {dataonly}, no key {none}, unmatched {n-full-dataonly-none}')
print(f'pack keys {len(keys)}, produced by JP data {len(produced)} ({100*len(produced)/len(keys):.1f}%)')
cat = Counter()
for k in keys:
    if k not in produced:
        for p in keys[k]:
            cat[p.split('/')[:4].__str__() if not p.startswith('ini') else 'ini-only'] += 1; break
print('pack keys not produced, by folder:'); [print(' ', v, c) for c, v in cat.most_common(25)]
pickle.dump(recs, open(sys.argv[1].replace('.pkl', '_keyed.pkl'), 'wb'))
