#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""For each EN-changed key, find JP textures that decode to the identical RGBA image (patch re-encoded the GIM
without visual change) and an existing pack PNG to alias it to. Updates out/en_changed_textures.csv, writes out/en_alias_reuse.txt.
usage: en_reuse.py work/jp.pkl work/en.pkl textures.ini.orig"""
import pickle, sys, os, csv, hashlib, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import decode, texkey
from collections import defaultdict
jp = pickle.load(open(sys.argv[1], 'rb')); en = pickle.load(open(sys.argv[2], 'rb'))
for L in (jp, en):
    for r in L: r.setdefault('key', texkey.compute_key(r))
jpimg = defaultdict(set)
for r in jp:
    img = decode.decode(r)
    if img is not None: jpimg[hashlib.md5(img.tobytes()).hexdigest()].add(r['key'])
inimap = {}
for line in open(sys.argv[3], encoding='utf-8', errors='replace'):
    m = re.match(r'^([0-9a-f]{24})\s*=\s*(\S+)', line.strip())
    if m: inimap[m.group(1)] = m.group(2)
rows = list(csv.DictReader(open('out/en_changed_textures.csv')))
enby = {r['key']: r for r in en}
for row in rows:
    same = sorted(jpimg.get(hashlib.md5(decode.decode(enby[row['key']]).tobytes()).hexdigest(), ()))
    row['visually_identical_jp_keys'] = ';'.join(same)
    row['reusable_pack_png'] = next((inimap[k] for k in same if inimap.get(k)), '')
with open('out/en_changed_textures.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
with open('out/en_alias_reuse.txt', 'w') as f:
    for r in rows:
        if r['reusable_pack_png']: f.write(f"{r['key']} = {r['reusable_pack_png']}\n")
print('visually identical:', sum(bool(r['visually_identical_jp_keys']) for r in rows), 'reusable:', sum(bool(r['reusable_pack_png']) for r in rows), 'of', len(rows))
