# SPDX-License-Identifier: GPL-3.0-or-later
"""Shared PNG export + todo/skip classification (same rules as export_uncovered.py)."""
import os, csv, re
import numpy as np
from PIL import Image
from collections import Counter, defaultdict
import decode, gim, texkey

def category(f):
    n = f.upper()
    rules = [('pac_units_LOV', r'^LOV_\d'), ('pac_LOV_' , r'^LOV_'), ('minimaps', r'^ODIF_BA_MAP'), ('battle_faces', r'^ODIF_BA_(LARGE_)?FACE'),
             ('odif_ui', r'^ODIF_'), ('enemy_chars_EC', r'^EC\d'), ('battle_chars_BC', r'^BC\d'), ('accessories_ACCE', r'^ACCE_'),
             ('ground_OMAP', r'^OMAP_'), ('char_lowpoly_LKCHARSLOW', r'^LKCHARSLOW'),
             ('weapons', r'^(SWD|SMG|SRL|TPF|PGD|SWG|TSR|RFL|RFG|PSL|LMW|MGN|REH|DAL|SS|NBG)[_\d]'),
             ('ui_LKIF', r'^LKIF_'), ('ui_IF', r'^IF_'), ('events_EV', r'^EV\d'), ('lk_models_LK', r'^LK\d'), ('canvas', r'^CANVAS'),
             ('battle_abr', r'\.ABR$')]
    for c, p in rules:
        if re.search(p, n): return c if not c.endswith('_') else c + re.sub(r'[\d_].*', '', n[4:].split('.')[0])[:8]
    return 'other_' + re.sub(r'[\d_].*', '', n.split('.')[0])[:12]

def classify(img, r):
    sub = img[:r['h'], :r['w']]; a = sub[:, :, 3]; rgb = sub[:, :, :3].reshape(-1, 3)
    ncol = len(np.unique(sub.reshape(-1, 4), axis=0)); reasons = []
    if a.max() == 0: reasons.append('fully transparent')
    elif ncol <= 2: reasons.append('blank/flat (<=2 colours)')
    if min(r['w'], r['h']) <= 8: reasons.append('tiny (<=8px side)')
    if (rgb.max(0) - rgb.min(0)).max() <= 24 and a.max() > 0 and a.min() < 255 and ncol > 2:
        reasons.append('alpha mask / single-colour gradient')
    elif ncol > 2 and np.all(rgb[:, 0] == rgb[:, 1]) and np.all(rgb[:, 1] == rgb[:, 2]) and r['w'] * r['h'] <= 64 * 64:
        reasons.append('grayscale small (effect/mask?)')
    return ncol, reasons

def export(items, out_dir, todo_csv, skip_csv, all_recs):
    files = defaultdict(set)
    for r in all_recs: files[r['key']].add(r['file'])
    todo, skip = [], []
    for k, r in sorted(items.items()):
        img = decode.decode(r); cat = category(r['file'])
        os.makedirs(os.path.join(out_dir, cat), exist_ok=True)
        Image.fromarray(img, 'RGBA').save(os.path.join(out_dir, cat, k + '.png'))
        ncol, reasons = classify(img, r)
        lw, lh, _ = texkey.ge_params(r)
        row = dict(key=k, file=r['file'], gim_offset=hex(r['gimoff']), palette_source=r.get('palsrc', ''), rule=r.get('rule', ''),
                   w=r['w'], h=r['h'], tex_w=1 << lw, tex_h=1 << lh, format=gim.FMTNAME[r['fmt']],
                   clut_format=gim.FMTNAME.get(r.get('palfmt'), ''), swizzled=r['order'], category=cat, colours=ncol,
                   png=os.path.join(cat, k + '.png'), reason=';'.join(reasons))
        (skip if reasons else todo).append(row)
    for name, L in ((todo_csv, todo), (skip_csv, skip)):
        with open(name, 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list((todo or skip)[0].keys()) if (todo or skip) else ['key']); w.writeheader(); w.writerows(L)
    print(f'  -> {out_dir}: todo {len(todo)}, skip {len(skip)}; todo by category {Counter(r["category"] for r in todo).most_common(8)}')
    print(f'     skip reasons {Counter(r["reason"].split(";")[0] for r in skip).most_common()}')
