#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Decompressor for VC3 PAC chunk LZ (hypothesis under test)."""
import struct
def decompress(buf, off=0):
    magic, csize, usize, unk = struct.unpack_from('<4I', buf, off)
    p = off + 16; end = off + csize
    out = bytearray()
    while p < end and len(out) < usize:
        c = buf[p]; p += 1
        if c < 0x80:
            n = c + 1; out += buf[p:p+n]; p += n
        else:
            b1 = buf[p]; p += 1
            d = (((c & 0x7f) << 1) | (b1 >> 7)) + 1
            n = (b1 & 0x7f) + 3
            if d > len(out): raise ValueError('bad distance %d at out %d in %d' % (d, len(out), p))
            for _ in range(n): out.append(out[-d])
    return bytes(out), p - off, usize, csize
