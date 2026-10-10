# SPDX-License-Identifier: GPL-3.0-or-later
"""Decode a scanned GIM record to RGBA (numpy), at PPSSPP's texture size (2^lw x 2^lh)."""
import numpy as np, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gim

def unswizzle(buf, pitch, rows):
    """PSP swizzle: 16-byte x 8-row blocks, row-major blocks."""
    bw = pitch // 16
    rows8 = (rows + 7) // 8 * 8
    a = np.frombuffer(buf[:pitch * rows8].ljust(pitch * rows8, b'\0'), np.uint8)
    a = a.reshape(rows8 // 8, bw, 8, 16).transpose(0, 2, 1, 3).reshape(rows8, pitch)
    return a[:rows]

def expand_colors(raw, fmt):
    if fmt == 3:
        return np.frombuffer(raw, np.uint8).reshape(-1, 4).copy()
    v = np.frombuffer(raw, '<u2').astype(np.uint32)
    if fmt == 0:
        r, g, b = v & 31, (v >> 5) & 63, (v >> 11) & 31
        return np.stack([(r << 3) | (r >> 2), (g << 2) | (g >> 4), (b << 3) | (b >> 2), np.full_like(v, 255)], 1).astype(np.uint8)
    if fmt == 1:
        r, g, b, a = v & 31, (v >> 5) & 31, (v >> 10) & 31, v >> 15
        return np.stack([(r << 3) | (r >> 2), (g << 3) | (g >> 2), (b << 3) | (b >> 2), a * 255], 1).astype(np.uint8)
    if fmt == 2:
        return np.stack([(v & 15) * 17, ((v >> 4) & 15) * 17, ((v >> 8) & 15) * 17, (v >> 12) * 17], 1).astype(np.uint8)
    raise ValueError(fmt)

def decode(r, full=True):
    fmt, w, h = r['fmt'], r['w'], r['h']
    pitch = r['pitch']; bpp = r['bpp']
    rows = r['hal']
    raw = r['pix'][:pitch * rows]
    a = unswizzle(raw, pitch, rows) if r['order'] == 1 else np.frombuffer(raw.ljust(pitch * rows, b'\0'), np.uint8).reshape(rows, pitch)
    if fmt == 4:
        idx = np.empty((rows, pitch * 2), np.uint16); idx[:, 0::2] = a & 15; idx[:, 1::2] = a >> 4
    elif fmt == 5:
        idx = a.astype(np.uint16)
    elif fmt in (0, 1, 2, 3):
        px = expand_colors(a.tobytes(), fmt).reshape(rows, -1, 4)
        idx = None
    else:
        return None
    if idx is not None:
        n = r['palcount']; pal = expand_colors(r['pal'][:n * gim.BPP[r['palfmt']] // 8], r['palfmt'])
        pal = np.concatenate([pal, np.zeros((256, 4), np.uint8)])
        px = pal[idx]
    img = px[:h, :w]
    if full:
        W, H = 1 << gim.pow2log(w), 1 << gim.pow2log(h)
        out = np.zeros((H, W, 4), np.uint8); out[:h, :w] = img; img = out
    return img
