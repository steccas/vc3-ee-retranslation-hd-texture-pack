#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""PAC textures + palette-variant combinations: keys, coverage vs an ini, PNG export, todo/skip CSVs.
usage: pac_palvar.py dec/DATA_EN.BIN <textures.ini to check coverage> [<ini.orig for validation>]"""
import sys, os, re, csv, pickle
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scan, texkey, gim, decode
from PIL import Image
from collections import defaultdict, Counter
import export_uncovered_lib as X

recs = scan.records(sys.argv[1]); pals = list(scan.PALETTES)
for r in recs: r['key'] = texkey.compute_key(r)
base = {r['key'] for r in recs}

def ini_keys(path):
    keys = set()
    for line in open(path, encoding='utf-8', errors='replace'):
        m = re.match(r'^([0-9a-f]{24})(?:_\d+)?\s*=', line.strip())
        if m: keys.add(m.group(1))
    mids = {k[8:16] for k in keys if k[16:] == '00000000'}; dats = {k[16:] for k in keys if k[8:16] == '00000000'}
    return lambda k: k in keys or k[8:16] in mids or k[16:] in dats
covered = ini_keys(sys.argv[2])
orig = ini_keys(sys.argv[3]) if len(sys.argv) > 3 else None

def with_pal(r, p):
    q = dict(r); q.update(palfmt=p['palfmt'], palcount=p['palcount'], pal=p['pal']); q['key'] = texkey.compute_key(q)
    q['palsrc'] = f"{p['file']}@{hex(p['gimoff'])}"; return q

# --- palette variant combinations
combos = {}
items = defaultdict(list)
for r in recs: items[r['file'].split('/')[0]].append(('img', r['file'], r['gimoff'], r))
for p in pals: items[p['file'].split('/')[0]].append(('pal', p['file'], p['gimoff'], p))
# rule 1: positional, inside the same top-level file (PAC: palette chunks F001.. apply in order to the CLUT images of the last image chunk)
for top, L in items.items():
    if not any(t == 'pal' for t, *_ in L): continue
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
                for r, p in zip(cl, P):
                    q = with_pal(r, p)
                    if q['key'] not in base: q['rule'] = 'positional'; combos.setdefault(q['key'], q)
# rule 2: enemy-faction palette files applied to the model families (LKENPALETTE_EMPIRE -> LK065-072, CR -> LK073-080 + LK319*,
# both confirmed by pack keys; GARIA -> LK081-088 + LK318* inferred by analogy)
fam = {'LKENPALETTE_EMPIRE.MLX': (r'^LK0(6[5-9]|7[0-2])', 'confirmed'), 'LKENPALETTE_CR.MLX': (r'^LK(07[3-9]|080|319)', 'confirmed'),
       'LKENPALETTE_GARIA.MLX': (r'^LK(08[1-8]|318)', 'inferred'), 'CANVAS_F00_PLT.HCL': (r'^CANVAS_F00\.HTX', 'confirmed')}
for pf, (pat, conf) in fam.items():
    P = [p for p in pals if p['file'] == pf]
    for r in recs:
        if r['fmt'] not in (4, 5) or not re.match(pat, r['file']): continue
        need = 16 if r['fmt'] == 4 else 256
        for p in P:
            if r['fmt'] == 5 and p['palcount'] < 256: continue  # CLUT8 needs a 256-entry CLUT; CLUT4 may use 16 or 256 (game loads full CLUT)
            q = with_pal(r, p)
            if q['key'] not in base: q['rule'] = 'faction-' + conf; combos.setdefault(q['key'], q)

def report(name, L):
    u = {}
    for q in L: u.setdefault(q['key'], q)
    print(f'[{name}] unique keys {len(u)}; covered by installed ini {sum(covered(k) for k in u)}' +
          (f'; present in original efonte ini {sum(orig(k) for k in u)}' if orig else ''))
    if L and 'rule' in L[0]:
        for rule in sorted({q['rule'] for q in u.values()}):
            ks = [k for k, q in u.items() if q['rule'] == rule]
            print(f'   rule {rule}: {len(ks)} keys' + (f', in original ini {sum(orig(k) for k in ks)}' if orig else ''))
    return {k: q for k, q in u.items() if not covered(k)}

pac = [r for r in recs if '/' in r['file']]
unc_pac = report('PAC base textures', pac)
unc_pv = report('palette variants', list(combos.values()))
X.export(unc_pac, 'out/uncovered_pac_png', 'out/uncovered_pac_todo.csv', 'out/uncovered_pac_skip.csv', recs)
X.export(unc_pv, 'out/uncovered_palvar_png', 'out/uncovered_palvar_todo.csv', 'out/uncovered_palvar_skip.csv', recs)
