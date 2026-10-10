# Licenses

This repository and its release files contain work by several people under different terms.

| What | Where | License / owner |
|---|---|---|
| Texture **additions** made for this release: the upscales of the 143 ReTranslation textures, the 49 UI text textures, the 2,930 newly covered textures, and the cleaned `textures.ini` | release zips | [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/), full text in [`LICENSE`](LICENSE) |
| efonte's AI upscaled pack (all files taken from it, inside the full pack) | full pack | © efonte. Redistributed as part of a combined pack with credit; efonte can ask for it to be removed or changed |
| Odioregistrarme's 7 hand-made HD textures | full pack | © Odioregistrarme |
| LunaMoo's fonts (part of efonte's pack) | full pack | © LunaMoo |
| Original game artwork the textures derive from | everything | © SEGA. This is an unofficial fan project, not affiliated with or endorsed by SEGA |
| ESRGAN models used (4x-Fatal-Anime, 4x-Fatal-Pixels by twittman; 4x Remacri by foolhardy) | not included (hashes only) | CC BY-NC-SA 4.0 by their authors |
| Code and docs in [`tools/`](tools/) | `tools/` | GPL-3.0-or-later, full text in [`tools/LICENSE`](tools/LICENSE) |
| This README and the other docs at the root | root | CC BY-NC-SA 4.0 |

## Why CC BY-NC-SA 4.0 for the textures

The upscales are produced by models released under CC BY-NC-SA 4.0 (non-commercial, share-alike), and
efonte's pack, which they extend, was made the same way. Sharing the additions under the same license
keeps them non-commercial and makes derivatives stay under the same terms. Credit the authors listed in
[`CREDITS.md`](CREDITS.md).

## Why GPL-3.0-or-later for the tools

- `tools/keys/src/pgddec.c` contains no third-party code, but it is written to be compiled and linked
  against **libkirk** as shipped in PPSSPP's `ext/libkirk`:
  - `kirk_engine.c/.h` (Draan et al.): GPL-3.0-or-later;
  - `bn.c`, `ec.c` (Segher Boessenkool): GPL-2.0 or GPL-3.0;
  - `amctrl.c` (tpu), `AES.c` (public domain rijndael), `SHA1.c`: distributed by PPSSPP as part of its
    GPL-licensed tree.

  A compiled `pgddec` is therefore a GPLv3 work, and the simplest consistent choice is GPL-3.0-or-later
  for all the tools. No libkirk source is redistributed here: you build `pgddec` from your own PPSSPP
  checkout.
- `tools/keys/src/crilayla.c` and the pure-Python CRILAYLA decoder in `cpk.py` are independent
  implementations written from unknownbrackets' public description of the format (which credits the
  earlier reverse engineering by hcs and Luigi Auriemma). No code from other decompressors is copied.
- The key formula in `gim.py` / `texkey.py` reimplements the behaviour of PPSSPP's
  `TextureReplacer::ComputeHash` and texture cache (GPL-2.0-or-later) from reading its source; no PPSSPP
  code is copied.
- Everything else in `tools/` is original code for this project.

The tools contain no game data, keys of the game, decrypted files, binaries or model weights.
