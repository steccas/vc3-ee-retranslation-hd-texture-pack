# SPDX-License-Identifier: GPL-3.0-or-later
import sys, os, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gim, packkeys
from collections import Counter
recs = pickle.load(open(sys.argv[1], 'rb'))
keys = packkeys.load(sys.argv[2])
bydata = {}
for k in keys: bydata.setdefault(k[16:], []).append(k)
hyp = Counter(); matched = 0; um = Counter()
for r in recs:
    w2, h2 = 1 << gim.pow2log(r['w']), 1 << gim.pow2log(r['h'])
    pitch_px = r['pitch'] * 8 // r['bpp']
    cands = {
        'bufw=pitch': pitch_px & gim.ALIGNMASK16[r['fmt']] or pitch_px,
        'bufw=w': r['w'],
        'bufw=w2': w2,
    }
    found = False
    for hn, bw in cands.items():
        for dn, (W, H) in {'pow2': (w2, h2), 'raw': (r['w'], r['h'])}.items():
            h = '%08x' % gim.data_hash(r['pix'], r['fmt'], bw, W, H)
            if h in bydata:
                hyp[(hn, dn)] += 1; found = True
    matched += found
    if not found: um[(r['fmt'], r['order'], r['w'], r['h'])] += 1
print('records', len(recs), 'datahash matched', matched)
print(hyp)
print('unmatched top', um.most_common(15))
