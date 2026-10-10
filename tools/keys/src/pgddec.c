// SPDX-License-Identifier: GPL-3.0-or-later
// pgddec: decrypt a PSP PGD-wrapped file using libkirk (amctrl.c) as shipped in PPSSPP's ext/libkirk.
// If no key is given, the vkey is recovered from the header MAC (bbmac_getkey), like PPSSPP does when key_ptr==NULL.
//
// This file contains no libkirk code; it must be compiled and linked against libkirk from a PPSSPP
// checkout (see run_all.sh). libkirk credits: KIRK engine by Draan with coyotebean, Davee, hitchhikr,
// kgsws, liquidzigong, Mathieulh, Proxima, SilverSpring (GPL-3.0-or-later); amctrl.c reverse-engineered
// by tpu; bn.c/ec.c by Segher Boessenkool (GPL-2.0 or GPL-3.0); AES.c (rijndael-alg-fst, public domain); SHA1.c (David Ireland,
// after A.M. Kuchling; no license notice). A compiled pgddec binary is therefore covered by the GPL version 3.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "kirk_engine.h"
#include "amctrl.h"
static KirkState kirk;
int main(int argc, char **argv) {
    if (argc < 3) { fprintf(stderr, "usage: pgddec in.pgd out.bin [hexkey16]\n"); return 1; }
    FILE *fi = fopen(argv[1], "rb"); if (!fi) { perror("in"); return 1; }
    u8 hdr[0x90]; if (fread(hdr, 1, 0x90, fi) != 0x90) return 1;
    kirk_init(&kirk);
    u8 key[16], *kp = NULL;
    if (argc > 3) { for (int i = 0; i < 16; i++) sscanf(argv[3] + 2*i, "%2hhx", &key[i]); kp = key; }
    PGD_DESC *pgd = pgd_open(&kirk, hdr, 2, kp);
    if (!pgd) { fprintf(stderr, "pgd_open failed\n"); return 2; }
    fprintf(stderr, "vkey=");
    for (int i = 0; i < 16; i++) fprintf(stderr, "%02x", pgd->vkey[i]);
    fprintf(stderr, " data_size=%u block_size=%u data_offset=0x%x blocks=%u\n", pgd->data_size, pgd->block_size, pgd->data_offset, pgd->block_nr);
    FILE *fo = fopen(argv[2], "wb"); if (!fo) { perror("out"); return 1; }
    u32 remain = pgd->data_size;
    for (u32 b = 0; remain; b++) {
        fseek(fi, pgd->data_offset + (long)b * pgd->block_size, SEEK_SET);
        memset(pgd->block_buf, 0, pgd->block_size);
        fread(pgd->block_buf, 1, pgd->block_size, fi);
        pgd_decrypt_block(&kirk, pgd, b);
        u32 n = remain < pgd->block_size ? remain : pgd->block_size;
        fwrite(pgd->block_buf, 1, n, fo); remain -= n;
    }
    fclose(fo); fclose(fi); pgd_close(pgd);
    return 0;
}
