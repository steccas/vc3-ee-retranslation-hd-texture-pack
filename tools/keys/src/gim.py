#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""GIM (MIG.00.1PSP) parser + PPSSPP texture-replacement key computation."""
import struct, xxhash

BPP = {0:16,1:16,2:16,3:32,4:4,5:8,6:16,7:32,8:4,9:8,10:8}
ALIGNMASK16 = {0:0x7F8,1:0x7F8,2:0x7F8,3:0x7FC,4:0x7E0,5:0x7F0,6:0x7F8,7:0x7FC,8:0x7FF,9:0x7FF,10:0x7FF}  # textureAlignMask16
FMTNAME = {0:'5650',1:'5551',2:'4444',3:'8888',4:'CLUT4',5:'CLUT8',6:'CLUT16',7:'CLUT32',8:'DXT1',9:'DXT3',10:'DXT5'}

def _imghdr(buf, p):
    (hs, ref, fmt, order, w, h, bpp, palign, halign, dim, r1, r2,
     idx, pstart, pend, pmask, ltype, lcount, ftype, fcount) = struct.unpack_from('<HHHHHHHHHHHHIIIIHHHH', buf, p)
    offs = [struct.unpack_from('<I', buf, p + idx + 4*i)[0] for i in range(max(1, lcount) * max(1, fcount))]
    return dict(fmt=fmt, order=order, w=w, h=h, bpp=bpp, palign=palign, halign=halign,
                lcount=lcount, fcount=fcount, base=p, offs=offs, pstart=pstart, pend=pend)

def parse_gim(buf, start):
    """Return list of dicts {image, palette} for a GIM beginning at buf[start] ('MIG.00.1PSP')."""
    res = []
    def walk(p, end, pal_ctx):
        while p + 16 <= end:
            bid, _, size, nxt, doff = struct.unpack_from('<HHIII', buf, p)
            if size < 16 or p + size > len(buf): break
            if bid in (2, 3):
                walk(p + nxt, p + size, {})
            elif bid == 4:
                pal_ctx['image'] = _imghdr(buf, p + doff); res.append(pal_ctx)
            elif bid == 5:
                pal_ctx['palette'] = _imghdr(buf, p + doff)
            p += size
    walk(start + 16, len(buf), {})
    return res

def pow2log(n):
    l = 0
    while (1 << l) < n: l += 1
    return l

def xxh64_32(b):
    return xxhash.xxh64_intdigest(b, 0xBACD7814) & 0xFFFFFFFF

def data_hash(mem, fmt, bufw, w, h):
    """TextureReplacer::ComputeHash (XXH64 mode, no hashranges/reduceHash). mem = bytes starting at texaddr."""
    bpp = BPP[fmt]
    if bufw <= w:
        total = bufw * h + (w - bufw)
        size = (bpp * total) // 8
        return xxh64_32(bytes(mem[:size]))
    bpl = (bpp * w) // 8; stride = (bpp * bufw) // 8
    r = 0
    for y in range(h):
        r = ((r * 11) ^ xxh64_32(bytes(mem[y*stride:y*stride+bpl]))) & 0xFFFFFFFF
    return r

def clut_hash(clutbytes):
    return xxhash.xxh32_intdigest(bytes(clutbytes), 0xC0108888)

def key(dim, datahash, fmt, clutbytes=None, clutformat=None):
    mid = dim
    if fmt in (4, 5, 6, 7):
        mid ^= (clut_hash(clutbytes) ^ clutformat) & 0xFFFFFFFF
    return '%016x%08x' % (mid & 0xFFFFFFFF, datahash)
