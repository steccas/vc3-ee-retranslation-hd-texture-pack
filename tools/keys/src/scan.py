#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Scan a decrypted DATA.BIN (CPK) for GIM textures and emit records (pickle)."""
import sys, os, pickle, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cpk, gim

import struct, paclz

def iter_blobs(path):
    """Yield (name, data) for every CPK file; PAC files are expanded into their LZ-compressed chunks."""
    c = cpk.CPK(path)
    for e in c.entries:
        d = c.read(e)
        if e['name'].upper().endswith('.PAC') and d[:4] == b'SCBN':
            p = 0x20
            while p + 0x30 <= len(d):
                m = d[p:p+4]; sz, hs, fl = struct.unpack_from('<III', d, p + 4)
                if m == b'EOFC': break
                if struct.unpack_from('<I', d, p + hs)[0] == 0x8000:
                    yield e['name'] + '/' + m.decode('ascii', 'replace'), paclz.decompress(d, p + hs)[0]
                p += hs + sz
        else:
            yield e['name'], d

PALETTES = []  # palette-only GIMs found during the last scan: dict(file, gimoff, palfmt, palcount, pal)

def iter_gims(path):
    PALETTES.clear()
    for name, d in iter_blobs(path):
        e = {'name': name}
        p = d.find(b'MIG.00.1PSP')
        while p >= 0:
            try:
                ts = gim.parse_gim(d, p)
                if not ts:
                    for t in _palonly(d, p): PALETTES.append(dict(file=e['name'], gimoff=p, **t))
                for t in ts:
                    yield e['name'], p, d, t
            except Exception as ex:
                print('parse error', e['name'], hex(p), ex, file=sys.stderr)
            p = d.find(b'MIG.00.1PSP', p + 1)

def _palonly(d, start):
    """Palette blocks (id 5) of a GIM that has no image block."""
    res = []
    def walk(p, end):
        while p + 16 <= end:
            bid, _, size, nxt, doff = struct.unpack_from('<HHIII', d, p)
            if size < 16 or p + size > len(d): break
            if bid in (2, 3): walk(p + nxt, p + size)
            elif bid == 5:
                h = gim._imghdr(d, p + doff); n = h['w'] * max(1, h['h']); po = h['base'] + h['offs'][0]
                res.append(dict(palfmt=h['fmt'], palcount=n, pal=bytes(d[po:po + n * gim.BPP[h['fmt']] // 8])))
            p += size
    walk(start + 16, len(d))
    return res

def records(path):
    out = []
    for name, goff, d, t in iter_gims(path):
        im = t.get('image'); pal = t.get('palette')
        if not im: continue
        fmt = im['fmt']; bpp = gim.BPP.get(fmt)
        if bpp is None: continue
        w, h = im['w'], im['h']
        rowbytes = (w * bpp + 7) // 8
        pa = im['palign'] or 1
        rowbytes_al = (rowbytes + pa - 1) // pa * pa
        ha = im['halign'] or 1
        h_al = (h + ha - 1) // ha * ha
        for fi in range(max(1, im['fcount'])):
            lvl0 = im['base'] + im['offs'][fi * max(1, im['lcount'])] if im['lcount'] else im['base'] + im['pstart']
            size0 = rowbytes_al * h_al
            r = dict(file=name, gimoff=goff, frame=fi, fmt=fmt, order=im['order'], w=w, h=h, bpp=bpp,
                     pitch=rowbytes_al, hal=h_al, levels=im['lcount'], frames=im['fcount'],
                     pix=bytes(d[lvl0:lvl0 + size0 + 4096]), pixlen=size0)
            if pal:
                pfmt = pal['fmt']; pbpp = gim.BPP[pfmt]
                n = pal['w'] * max(1, pal['h'])
                po = pal['base'] + pal['offs'][0]
                r.update(palfmt=pfmt, palcount=n, pal=bytes(d[po:po + n * pbpp // 8 + 2048]))
            out.append(r)
    return out

if __name__ == '__main__':
    recs = records(sys.argv[1])
    pickle.dump(recs, open(sys.argv[2], 'wb'))
    print(len(recs), 'textures')
