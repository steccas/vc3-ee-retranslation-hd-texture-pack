# SPDX-License-Identifier: GPL-3.0-or-later
"""Compute the PPSSPP replacement key (xxh64, ignoreAddress, ignoreMipmap) for a scanned GIM record."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gim

def ge_params(r):
    lw, lh = gim.pow2log(r['w']), gim.pow2log(r['h'])
    pitch_px = r['pitch'] * 8 // r['bpp']
    bufw = (pitch_px & gim.ALIGNMASK16[r['fmt']]) or pitch_px
    return lw, lh, bufw

def compute_key(r, clutmask=0xFF):
    lw, lh, bufw = ge_params(r)
    dim = (lh << 8) | lw
    dh = gim.data_hash(r['pix'], r['fmt'], bufw, 1 << lw, 1 << lh)
    if r['fmt'] in (4, 5, 6, 7):
        if 'pal' not in r: return None
        nbytes = r['palcount'] * gim.BPP[r['palfmt']] // 8
        clutformat = 0xC5000000 | (clutmask << 8) | r['palfmt']
        return gim.key(dim, dh, r['fmt'], r['pal'][:nbytes], clutformat)
    return gim.key(dim, dh, r['fmt'])
