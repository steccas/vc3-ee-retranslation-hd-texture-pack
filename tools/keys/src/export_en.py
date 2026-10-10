#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Export the EN-changed textures: CSV (key, source, dims, format...) + PNG previews named by key."""
import sys, os, pickle, csv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import decode, gim, texkey, packkeys
from PIL import Image
from collections import defaultdict
base = os.path.abspath(os.environ.get('VC3_WORKDIR', os.getcwd()))  # run_all.sh working directory
jp = pickle.load(open(os.path.join(base, 'work/jp_keyed.pkl'), 'rb'))
en = pickle.load(open(os.path.join(base, 'work/en_keyed.pkl'), 'rb'))
pack = packkeys.load(os.path.join(base, 'pack/ULJM05781'))
jpk = {r['key'] for r in jp}
jp_by_loc = {(r['file'], r['gimoff'], r['frame']): r for r in jp}
jp_by_file = defaultdict(list)
for r in jp: jp_by_file[r['file']].append(r)
out = os.path.join(base, 'out'); png = os.path.join(out, 'en_changed_png'); os.makedirs(png, exist_ok=True)
groups = defaultdict(list)
for r in en:
    if r['key'] not in jpk: groups[r['key']].append(r)
rows = []
for k, rs in sorted(groups.items()):
    r = rs[0]
    lw, lh, bufw = texkey.ge_params(r)
    # JP counterpart: same index of the GIM inside the same file
    idx = [x for x in en if x['file'] == r['file']].index(r)
    jl = jp_by_file[r['file']]
    j = jl[idx] if idx < len(jl) else None
    change = ''
    if j:
        if (j['w'], j['h'], j['fmt']) != (r['w'], r['h'], r['fmt']): change = 'resized/reformatted'
        elif j['pix'][:j['pixlen']] == r['pix'][:r['pixlen']]: change = 'palette only'
        else: change = 'pixels'
    flags = []
    if r['h'] == 512 or (1 << lh) == 512: flags.append('h512-maxSeenV')
    if (r['w'], r['h']) != (1 << lw, 1 << lh): flags.append('non-pow2')
    if r['fmt'] in (4, 5, 6, 7) and 'pal' not in r: flags.append('no-palette')
    img = decode.decode(r)
    Image.fromarray(img, 'RGBA').save(os.path.join(png, k + '.png'))
    rows.append(dict(key=k, file=r['file'], gim_offset=hex(r['gimoff']), occurrences=len(rs),
                     other_files=';'.join(sorted({x['file'] for x in rs[1:]})),
                     w=r['w'], h=r['h'], tex_w=1 << lw, tex_h=1 << lh, bufw=bufw,
                     format=gim.FMTNAME[r['fmt']], clut_format=gim.FMTNAME.get(r.get('palfmt'), ''),
                     clut_entries=r.get('palcount', ''), swizzled=r['order'], mip_levels=r['levels'],
                     jp_key=j['key'] if j else '', jp_key_in_pack=(j['key'] in pack) if j else '',
                     jp_pack_file=';'.join(sorted(pack.get(j['key'], [])))[:200] if j else '',
                     change=change, caveats=';'.join(flags)))
with open(os.path.join(out, 'en_changed_textures.csv'), 'w', newline='') as f:
    wtr = csv.DictWriter(f, fieldnames=list(rows[0].keys())); wtr.writeheader(); wtr.writerows(rows)
print(len(rows), 'unique EN-changed keys;', sum(len(v) for v in groups.values()), 'GIM occurrences')
from collections import Counter
print(Counter(r['change'] for r in rows)); print(Counter(r['caveats'] for r in rows))
print('JP counterpart in pack:', Counter(r['jp_key_in_pack'] for r in rows))
