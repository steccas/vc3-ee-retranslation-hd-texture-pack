# SPDX-License-Identifier: GPL-3.0-or-later
import sys, os, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gim, packkeys
from collections import Counter
recs = pickle.load(open(sys.argv[1], 'rb'))
keys = packkeys.load(sys.argv[2])
bydata = {}
for k in keys: bydata.setdefault(k[16:], []).append(k)
res = Counter(); ex = []
for r in recs:
    w2, h2 = 1 << gim.pow2log(r['w']), 1 << gim.pow2log(r['h'])
    dim = (gim.pow2log(r['h']) << 8) | gim.pow2log(r['w'])
    pitch_px = r['pitch'] * 8 // r['bpp']
    bw = pitch_px & gim.ALIGNMASK16[r['fmt']] or pitch_px
    dh = '%08x' % gim.data_hash(r['pix'], r['fmt'], bw, w2, h2)
    if dh not in bydata or 'pal' not in r: continue
    targets = {int(k[8:16], 16) ^ dim for k in bydata[dh]}
    pb = gim.BPP[r['palfmt']] // 8
    hit = None
    for nbytes in sorted({r['palcount'] * pb, 32, 64, 512, 1024, (16 if r['fmt']==4 else 256) * pb}):
        ch = gim.clut_hash(r['pal'][:nbytes])
        for t in targets:
            cf = ch ^ t
            if (cf >> 24) == 0xC5 or cf < 0x1000000:
                hit = (nbytes == r['palcount']*pb, nbytes, hex(cf)); break
        if hit: break
    res[hit] += 1
    if not hit and len(ex) < 5: ex.append((r['file'], r['fmt'], r['palfmt'], r['palcount'], [hex(t) for t in targets]))
for k, v in res.most_common(30): print(v, k)
print(ex)
