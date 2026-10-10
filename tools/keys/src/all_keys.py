#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Dump every computable texture key of a decrypted DATA.BIN to CSV (also keeps a pickle for analysis)."""
import sys, os, csv, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scan, texkey, gim
recs = scan.records(sys.argv[1])
rows = []
for r in recs:
    r['key'] = texkey.compute_key(r)
    lw, lh, bufw = texkey.ge_params(r)
    rows.append(dict(key=r['key'], file=r['file'], gim_offset=hex(r['gimoff']), w=r['w'], h=r['h'],
                     tex_w=1 << lw, tex_h=1 << lh, format=gim.FMTNAME[r['fmt']],
                     clut_format=gim.FMTNAME.get(r.get('palfmt'), ''), swizzled=r['order']))
with open(sys.argv[2], 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
if len(sys.argv) > 3: pickle.dump(recs, open(sys.argv[3], 'wb'))
print(len(rows), 'rows', len({r['key'] for r in rows}), 'unique keys')
