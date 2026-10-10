#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""EN-computable keys that no [hashes] entry of the ini (with PPSSPP wildcard rules) nor en_alias_reuse covers.
usage: en_uncovered.py textures.ini.orig"""
import re, csv, sys
keys = set(); mids = set(); dats = set()
for line in open(sys.argv[1], encoding='utf-8', errors='replace'):
    m = re.match(r'^([0-9a-f]{24})(?:_\d+)?\s*=', line.strip())
    if m:
        k = m.group(1); keys.add(k)
        if k[16:] == '00000000': mids.add(k[8:16])
        if k[8:16] == '00000000': dats.add(k[16:])
rows = list(csv.DictReader(open('out/all_keys_en.csv')))
for r in rows: r['other_files'] = ''
alias = {l.split(' = ')[0] for l in open('out/en_alias_reuse.txt')}
files = {}
for r in rows: files.setdefault(r['key'], set()).add(r['file'])
seen = set(); out = []
for r in rows:
    k = r['key']
    if k in seen: continue
    seen.add(k)
    if k in keys or k[8:16] in mids or k[16:] in dats or k in alias: continue
    r['other_files'] = ';'.join(sorted(files[k] - {r['file']})[:5]); out.append(r)
with open('out/en_uncovered.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(out)
print('EN unique keys', len(seen), 'uncovered', len(out))
