#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Minimal CRI CPK reader (UTF tables, TOC, CRILAYLA decompression)."""
import struct, sys, os

def read_utf(buf, off):
    assert buf[off:off+4] == b'@UTF', buf[off:off+4]
    size, rows_off, str_off, data_off, name_off, ncol, rowlen, nrows = struct.unpack('>IIIIIHHI', buf[off+4:off+32])
    base = off + 8
    t = buf[base:base+size]
    def s(o):
        e = t.index(b'\0', str_off + o)
        return t[str_off+o:e].decode('utf-8', 'replace')
    p = 24
    cols = []
    fmt = {0:'>B',1:'>b',2:'>H',3:'>h',4:'>I',5:'>i',6:'>Q',7:'>q',8:'>f'}
    def readval(typ, p):
        if typ in fmt:
            n = struct.calcsize(fmt[typ]); return struct.unpack(fmt[typ], t[p:p+n])[0], p+n
        if typ == 0xA:
            o = struct.unpack('>I', t[p:p+4])[0]; return s(o), p+4
        if typ == 0xB:
            o, n = struct.unpack('>II', t[p:p+8]); return t[data_off+o:data_off+o+n], p+8
        raise ValueError(typ)
    for _ in range(ncol):
        flags = t[p]; nameo = struct.unpack('>I', t[p+1:p+5])[0]; p += 5
        st, typ = flags & 0xF0, flags & 0x0F
        const = None
        if st == 0x30:
            const, p = readval(typ, p)
        cols.append((s(nameo), st, typ, const))
    rows = []
    for r in range(nrows):
        p = rows_off + r*rowlen
        row = {}
        for name, st, typ, const in cols:
            if st == 0x50:
                row[name], p = readval(typ, p)
            elif st == 0x30:
                row[name] = const
            else:
                row[name] = None
        rows.append(row)
    return s(name_off), rows

import ctypes
# Fast path: libcrilayla.so built from crilayla.c (see run_all.sh). Override the location with CRILAYLA_LIB.
# Falls back to the (slow) pure-Python decoder if the library is missing.
try:
    _lib = ctypes.CDLL(os.environ.get('CRILAYLA_LIB') or os.path.join(os.path.dirname(os.path.abspath(__file__)), 'libcrilayla.so'))
except OSError:
    _lib = None
def crilayla(data):
    if _lib is None:
        return crilayla_py(data)
    usize = struct.unpack('<I', data[8:12])[0]
    out = ctypes.create_string_buffer(usize + 0x100)
    r = _lib.crilayla_decompress(data, len(data), out, usize + 0x100)
    if r: raise ValueError('crilayla error %d' % r)
    return out.raw

def crilayla_py(data):
    """Decompress CRILAYLA (pure-python reference, slow)."""
    assert data[:8] == b'CRILAYLA'
    usize, hsize = struct.unpack('<II', data[8:16])
    out = bytearray(usize + 0x100)
    out[0:0x100] = data[16+hsize:16+hsize+0x100]
    inp = data
    end = 16 + hsize - 1
    bitpool = 0; bitsleft = 0; inpos = end
    outpos = 0x100 + usize - 1
    outend = 0x100
    def getbits(n):
        nonlocal bitpool, bitsleft, inpos
        v = 0
        while n:
            if bitsleft == 0:
                bitpool = inp[inpos]; bitsleft = 8; inpos -= 1
            take = min(bitsleft, n)
            v = (v << take) | ((bitpool >> (bitsleft - take)) & ((1 << take) - 1))
            bitsleft -= take; n -= take
        return v
    vle = (2, 3, 5, 8)
    while outpos >= outend:
        if getbits(1):
            backref = outpos + 3 + getbits(13)
            length = 3
            lvl = 0
            while True:
                bits = getbits(vle[lvl]); length += bits
                if bits != (1 << vle[lvl]) - 1: break
                if lvl < 3: lvl += 1
                else:
                    while True:
                        bits = getbits(8); length += bits
                        if bits != 255: break
                    break
            for _ in range(length):
                out[outpos] = out[backref]; outpos -= 1; backref -= 1
        else:
            out[outpos] = getbits(8); outpos -= 1
    return bytes(out[:0x100 + usize])

class CPK:
    def __init__(self, path):
        self.f = open(path, 'rb')
        head = self.f.read(0x800)
        assert head[:4] == b'CPK '
        _, rows = read_utf(head + self.f.read(0x10000), 0x10)
        self.header = rows[0]
        toc_off = self.header['TocOffset']; toc_size = self.header['TocSize']
        content_off = self.header['ContentOffset']
        self.f.seek(toc_off); tb = self.f.read(toc_size)
        assert tb[:4] == b'TOC '
        _, self.toc = read_utf(tb, 0x10)
        base = min(toc_off, content_off) if content_off else toc_off
        self.entries = []
        for r in self.toc:
            name = (r['DirName'] + '/' if r.get('DirName') else '') + r['FileName']
            self.entries.append(dict(name=name, offset=base + r['FileOffset'], size=r['FileSize'],
                                     extract=r['ExtractSize'], id=r.get('ID')))
    def read(self, e):
        self.f.seek(e['offset']); d = self.f.read(e['size'])
        if e['extract'] != e['size'] and d[:8] == b'CRILAYLA':
            d = crilayla(d)
        return d

if __name__ == '__main__':
    c = CPK(sys.argv[1])
    print(c.header)
    for e in c.entries[:int(sys.argv[2]) if len(sys.argv) > 2 else None]:
        print(e)
