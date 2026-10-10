// SPDX-License-Identifier: GPL-3.0-or-later
// CRILAYLA decompressor (shared lib for ctypes, used by cpk.py). Returns 0 on success.
// Independent implementation written from the public description of the format in unknownbrackets'
// "Valkyria Chronicles 3 - File Formats" notes
// (https://gist.github.com/unknownbrackets/78c4631a4091044d381432ffb7f1bae4), which in turn credit the
// earlier CPK/CRILAYLA reverse engineering by hcs (Halley's Comet Software) and Luigi Auriemma.
// Build: cc -O2 -shared -fPIC -o libcrilayla.so crilayla.c
#include <stdint.h>
#include <string.h>
static const uint8_t *g_in; static long g_pos; static int g_left; static uint8_t g_pool;
static unsigned getbits(int n) {
    unsigned v = 0;
    while (n) {
        if (g_left == 0) { g_pool = g_in[g_pos--]; g_left = 8; }
        int take = g_left < n ? g_left : n;
        v = (v << take) | ((g_pool >> (g_left - take)) & ((1u << take) - 1));
        g_left -= take; n -= take;
    }
    return v;
}
int crilayla_decompress(const uint8_t *in, long insize, uint8_t *out, long outsize) {
    if (insize < 16 || memcmp(in, "CRILAYLA", 8)) return -1;
    uint32_t usize, hsize; memcpy(&usize, in + 8, 4); memcpy(&hsize, in + 12, 4);
    if (outsize < (long)usize + 0x100 || 16 + (long)hsize + 0x100 > insize) return -2;
    memcpy(out, in + 16 + hsize, 0x100);
    g_in = in; g_pos = 16 + (long)hsize - 1; g_left = 0;
    long outpos = 0x100 + (long)usize - 1, outend = 0x100;
    static const int vle[4] = {2, 3, 5, 8};
    while (outpos >= outend) {
        if (getbits(1)) {
            long backref = outpos + 3 + getbits(13);
            long length = 3; int lvl = 0;
            for (;;) {
                unsigned bits = getbits(vle[lvl]); length += bits;
                if (bits != (1u << vle[lvl]) - 1) break;
                if (lvl < 3) lvl++;
                else { do { bits = getbits(8); length += bits; } while (bits == 255); break; }
            }
            while (length-- && outpos >= 0) { out[outpos--] = out[backref--]; }
        } else {
            out[outpos--] = (uint8_t)getbits(8);
        }
        if (g_pos < 15) break;
    }
    return 0;
}
