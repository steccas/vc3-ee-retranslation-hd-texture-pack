#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Which [hashes] entries of a textures.ini can fire for the textures computable from a DATA.BIN (via all_keys_*.csv).
Applies PPSSPP's LookupWildcard rules (ignoreAddress): exact, CLUT-only (data=0), data-only (mid=0)."""
import sys, csv, re
from collections import Counter
ini, en_csv, jp_csv, out_restore = sys.argv[1:5]
def keyset(p):
    ks = {r['key'] for r in csv.DictReader(open(p))}
    return ks, {k[8:16] for k in ks}, {k[16:] for k in ks}
EN, ENm, END = keyset(en_csv); JP, JPm, JPD = keyset(jp_csv)
def active(k, S, M, D):
    mid, dat = k[8:16], k[16:]
    if k in S: return 'exact'
    if dat == '00000000' and mid in M: return 'wild-clut'
    if mid == '00000000' and dat in D: return 'wild-data'
    return ''
entries = []; sec = None
for line in open(ini, encoding='utf-8', errors='replace'):
    s = line.strip()
    if s.startswith('['): sec = s; continue
    if sec != '[hashes]': continue
    m = re.match(r'^([0-9a-f]{24})(?:_\d+)?\s*=\s*(.*)$', s)
    if m: entries.append((m.group(1), m.group(2)))
def cat(path):
    p = path.lower()
    return 'spanish' if '/spanish/' in p else 'japan' if '/japan/' in p else ('ignore(empty)' if not p else 'other')
stat = Counter(); restore = []
for k, v in entries:
    a_en = active(k, EN, ENm, END); a_jp = active(k, JP, JPm, JPD)
    c = cat(v)
    stat[(c, 'total')] += 1
    if a_en: stat[(c, 'active EN')] += 1
    if a_jp: stat[(c, 'active JP')] += 1
    if a_jp and not a_en: stat[(c, 'JP-only (lost in EN)')] += 1
    if c == 'spanish' and a_en: restore.append(f'{k} = {v}')
with open(out_restore, 'w') as f: f.write('\n'.join(restore) + '\n')
for c in ('spanish', 'japan', 'other', 'ignore(empty)'):
    print(c, {k[1]: v for k, v in stat.items() if k[0] == c})
print('TOTAL entries', len(entries), 'active EN', sum(v for k, v in stat.items() if k[1] == 'active EN'))
print('restore_spanish:', len(restore))
