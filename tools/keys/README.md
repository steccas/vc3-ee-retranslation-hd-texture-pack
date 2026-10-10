# Offline PPSSPP texture-replacement keys for VC3 Extra Edition (ULJM05957)

This folder holds the tools that decrypt the game data, find every GIM texture in it and compute the
key PPSSPP's texture replacement uses for it, without playing the game. They were used to find the
textures changed by the English ReTranslation and the ones efonte's pack didn't cover, and to check
every mapping in the final `textures.ini`.

Nothing here contains game data. You need your own ISOs and efonte's pack zip.

## Result: the key can be computed offline, exactly

PPSSPP's replacement key (`hash = xxh64`, `ignoreAddress`, `ignoreMipmap`) can be computed exactly
from the GIM files inside `DATA.BIN`.

Validation against efonte's pack (`original/` + `textures.ini`, 11,789 keys):

| Measure | Value |
|---|---|
| GIM textures in the JP `DATA.BIN` (image + palette, if any) | 9,784 (7,441 unique keys) |
| Computed key present in the pack | **6,815 (69.7%)**; the decoded image is **pixel-identical** to the pack PNG in 6,815/6,815 cases |
| Image present in the pack under another key (formula error) | 26 (always the same 256x256 CLUT4 texture, repeated in 9 files × 3; the game draws it with `clutformat` mask 0xF0 / another palette format, i.e. GE state set at runtime) |
| Image not in the pack (never dumped by efonte, or JP versions of text textures that are Spanish in the pack) | 2,899 (+44 with the same data hash but a different CLUT) |
| **Formula reliability** (image in the pack with non-trivial content) | **6,815 / 6,841 = 99.6%** |
| Pack keys produced by the JP data | 5,695 / 11,789 (48%); the rest are aliases, runtime palette variants (`backgrounds_with_effects`, `characters_effects`) and Spanish maps |

512-high textures match in 91% of cases (442/485): PPSSPP's `maxSeenV` rule rarely matters here.

## How the key is computed (PPSSPP v1.20.3/1.20.4; the hash code is identical in both and reproduces dumps made in 2020)

File name = `%016llx%08x` of (`cachekey`, `hash`). With `ignoreAddress` the high half of `cachekey`
(the address) is 0, so the key is `00000000` + `MID` + `DATA`.

- **DATA** = `TextureReplacer::ComputeHash`: `XXH64(seed 0xBACD7814)` truncated to the low 32 bits,
  computed on the raw texture bytes as they sit in PSP RAM (so **swizzled**, if the GIM is swizzled;
  PPSSPP doesn't unswizzle before hashing). Only level 0 and the GE size `w=2^lw`, `h=2^lh` count:
  - if `bufw <= w`: one hash over `bpp*(bufw*h + (w-bufw))/8` contiguous bytes;
  - otherwise (narrow, padded textures, e.g. CLUT4 16x16 with `bufw=32`): for each row
    `r = r*11 ^ (u32)XXH64(row of w*bpp/8 bytes)`, with stride `bufw*bpp/8`;
  - `bufw` = GIM pitch in pixels (row aligned to `pitch_align`, 16 bytes), masked with `textureAlignMask16`;
  - if `h==512` and a `maxSeenV<512` exists, PPSSPP uses `h=maxSeenV`. That value is only known at
    runtime; the pack defines no `[hashranges]`.
- **MID** = `dim ^ cluthash`, with `dim = (log2 h << 8) | log2 w` (e.g. `0x0506` = 64x32). For CLUT
  formats (4/8/16/32 bit): `cluthash = XXH32(clut_bytes, seed 0xC0108888) ^ clutformat`, where:
  - `clut_bytes` = the bytes loaded by the last CLOAD, i.e. `n_entries * bytes_per_entry` of the GIM
    palette (32 for 16×4444/5551, 64 for 16×8888, 1024 for 256×8888);
  - `clutformat` = the full GE word of command 0xC5: `0xC500FF00 | palfmt` (mask 0xFF, shift 0, start 0).

  For non-CLUT formats, MID = `dim`.

Sources (PPSSPP): `GPU/Common/TextureReplacer.cpp` (`ComputeHash`, `HashName`, `LookupWildcard`),
`TextureCacheCommon.cpp/.h` (`CacheKey`, `SetTexture`, `LoadClut`),
`GPU/Vulkan/TextureCacheVulkan.cpp` (`UpdateCurrentClut`). The Python code is a reimplementation;
no PPSSPP code is copied.

## Data chain

1. `PSP_GAME/INSDIR/DATA.BIN` is a PGD file (key_index 1, drm_type 1). The `vkey` is recovered from
   the header MAC (libkirk's `bbmac_getkey`), so no game key is needed; it's the same for JP and EN.
   Tool: `src/pgddec.c`, built against PPSSPP's `ext/libkirk`.
2. The decrypted file is a CRI **CPK** archive with 10,147 files, compressed with CRILAYLA
   (`src/cpk.py` + `src/crilayla.c`).
3. Textures are **GIM** (`MIG.00.1PSP`) inside `HTX` (HTEX/HTSF), `MLX`, `HTF`, `MMF`, `HCL` and `ABR`.
   `.PAC` files contain GIMs compressed with a proprietary LZ (see "PAC files" below). There are also
   palette-only GIMs (`LKCHARSLOW.MLX` etc.): runtime palette swaps, whose keys don't come from a single GIM.
4. Texture formats: almost all CLUT4 or CLUT8, 85% swizzled, with 8888/5551/4444 palettes.

## Textures changed by the English patch

- At file level, 372 of 10,147 CPK files change: 244 MXE, 69 MTP (text and scripts) and **59 MLX** (UI).
  No HTX, PAC or HTF. The EN EBOOT contains no GIM. The main dialogue font isn't a GIM but a glyph
  cache built at runtime, so it can't be computed offline. The patch release notes list exactly these
  areas as "New textures": Gallian map, chapter titles, board, deployment and battle UI, boss name plates.
  DLC is out of scope.
- The 59 MLX contain 224 GIMs. 47 are identical in JP (34 of them are in the pack, an indirect check of
  the parser). The other **177 occurrences are 143 new EN keys**, all with changed pixels (no palette-only
  change, no size change).
- Main formats: CLUT4/CLUT8 with 8888 palettes. Sizes: 512x128 (41), 512x256 (47), then small UI
  textures. Main files: `LKIF_MLX_SLG` (43), `LKIF_MLX_SLG_SUB` (18), `LKIF_MLX_BRIEFING` (13), the
  episode titles `LKIF_EP_TITLExx`, `BOSS_DIRECTION_0xx`, `IF_MLX_*` (title, save, march).
- **Direct validation**: for **86 of the 143** EN keys, the JP texture in the same slot gives a key that
  really exists in the pack. The patch only changes pixels (size, format, bufw and CLUT layout stay the
  same), so those slots are verified directly. The other 57 are slots efonte never dumped in JP.
- LunaMoo's 128x8 number font (`font1`, JP key `0000000023bead2481be28c3`, from `LKIF_MLX_SLG`) was
  changed by the patch and has a new EN key (`00000000b230d06c50691347`).
- Only one texture is 512 high (`maxSeenV` caveat).
- No EN key was already in the pack. The other way round, the pack had **84 of the JP keys** that the
  patch replaces: with the English ISO those replacements never trigger and the textures show at native
  resolution.

### Re-encodings without a visual change

Of the 143 EN-changed keys, **74 decode to an image identical to a JP texture** (indices and palette
reordered). In 59 cases an upscaled PNG already exists in the pack and can be reused with an alias
(`out/en_alias_reuse.txt`). Example: the 64x64 button icons `a095b1469ce73a3a` exist in
`LKIF_MLX_COMMON.MLX` and `LKIF_MLX_SLG.MLX`; the patch re-encoded only the SLG copy (new key
`4b263fc11877371f`), so both keys are needed.

In-game dump check: 25 dumps made with "Save new textures" on the English ISO are all computable from
the EN data (22 in the 143 EN-changed keys, 2 minimaps not covered by the pack, 1 JP key of an icon
also present in another file).

### Lists produced

- `out/en_changed_textures.csv`: key, source file, GIM offset, occurrences/other files, w/h, tex_w/tex_h
  (GE size = dump size), bufw, format, CLUT format, swizzle, mips, matching JP key and its pack file, caveats.
- `out/en_changed_png/<key>.png`: 143 RGBA previews at GE size (power of two), named by key.
- `out/all_keys_en.csv`, `out/all_keys_jp.csv`: every computable texture, 9,784 rows each
  (7,453 and 7,441 unique keys).
- `out/restore_spanish.txt`: the `/spanish/` entries of efonte's ini that are active with the EN ISO.
  Only **2**: `a095b1469ce73a3a` (button icons) and `2469764b2ff3ce6c` (a sticker). The other 591 are
  Spanish versions of slots that have a `/japan/` or JP counterpart, so they never show in the EN game.
- `out/en_alias_reuse.txt`: 59 aliases from EN keys to existing upscales.
- `out/en_uncovered.csv`: EN keys that no ini entry (with PPSSPP's wildcard rules) nor alias covers.
- Entries of efonte's ini active for EN (of 11,792, `LookupWildcard` rules): **5,623**.

  | Group | Active EN / total |
  |---|---|
  | `/japan/` | 380/422 (the 41 lost are the slots changed by the patch) |
  | other | 5,239/10,768 |
  | `/spanish/` | 2/593 |
  | empty rules (ignore) | 2/9 |

  The inactive "other" entries are mostly runtime palette variants or PAC content, so this is a lower bound.

## Uncovered EN textures

`src/export_uncovered.py` exports the uncovered keys to `out/uncovered_png/<category>/<key>.png`
(RGBA, power-of-two size) and splits them into `out/uncovered_todo.csv` (to upscale) and
`out/uncovered_skip.csv` (to skip, with the reason: alpha masks or single-colour gradients, tiny ≤8px,
small grayscale, blank/flat). Against the pack installed at the time: 1,689 keys, 1,579 todo, 110 skip.

Categories: character portraits for events/dialogue (`EC*`), battle minimaps (`ODIF_BA_MAP*`, 299),
busts and close-ups (`BC*`), weapon model textures, UI (`LKIF_*`, `IF_*`; part of it has Japanese text
the patch didn't translate), accessories (`ACCE_*`), ground (`OMAP_*`), 3D model textures (`LK*`),
battle faces, tutorial events.

**Runtime palette variants.** The game clearly uses them: in the pack, 382 data hashes appear with
several CLUTs (up to 99), e.g. in `backgrounds_with_effects` and `characters_effects` (fades and flashes
done by changing the palette); and `DATA.BIN` has palette-only GIMs. These can't be computed offline,
and a "todo" texture may never appear in game with its base palette. "Save new textures" in game is
the final check.

## PAC files and palette variants

**PAC compression (`src/paclz.py`).** A PAC file is an `SCBN` container with chunks `F000…F0nn`. Each
chunk starts with the header `{0x8000, csize (header included), usize, 0x708}`, followed by the stream:
- byte `c < 0x80`: `c+1` literal bytes follow;
- byte `c >= 0x80`, followed by `b1`: backref with `dist = ((c & 0x7f) << 1 | b1 >> 7) + 1` and
  `len = (b1 & 0x7f) + 3`, copied byte by byte.

Check: 3,574 of 3,574 chunks decompress to the exact `usize`, consuming exactly `csize`. `scan.py`
expands PACs automatically. PAC files are byte-identical between JP and EN.

**PAC textures**: 2,086 occurrences, 697 unique keys, all CLUT4: vehicle textures `LOV_*` (tanks, APCs,
wheels). 536 were already in efonte's ini (77%): the formula works on PACs too.

**Palette variants** (palette-only GIMs), two matching rules:
1. *Positional, same file*: in PACs, palette chunks `F001…` apply in order to the CLUT images of the
   last image chunk (vehicle colours and camo). 1,282 keys; **1,041 are in efonte's ini (81%)**, so the
   rule is confirmed.
2. *Faction palettes*: `LKENPALETTE_EMPIRE` applies to models `LK065–072`, `LKENPALETTE_CR` to
   `LK073–080` + `LK319*`. Both pairs are confirmed by pack keys; for CLUT4 the game also loads
   256-entry CLUTs. 635 keys, only 46 in the pack (7%): these are all possible combinations, and only
   some appear in game. `LKENPALETTE_GARIA` → `LK081–088` + `LK318*` is inferred by analogy
   (394 keys, 0 in the pack). Faction keys should be treated as *speculative*.

Output: `out/uncovered_pac_png/`, `out/uncovered_palvar_png/` and the matching `*_todo.csv`/`*_skip.csv`;
the `rule` column gives the rule and `palette_source` the palette's origin.

## Mapping check of the assembled `textures.ini`

Tools: `src/mapping_check{,2,3,4}.py`, `src/sheet.py`. The native reference of each key is the texture
decoded from the data (EN and JP, PAC and palette variants included) or, if it can't be computed,
efonte's original dump. Each upscale is box-downscaled 4x and compared to the native image:
- with 4x4/8x8 block metrics after a light blur;
- with a metric for the "area N" label corner of the minimaps;
- relatively, against all other upscales of the same size in the pack: if another PNG clearly matches
  better, the mapping is wrong.

Result on the pack: all **14,314 entries with a path** are checkable (10,418 against the data, 3,896
against dumps), plus the 590 removed Spanish entries.
- **No wrong mappings.** No entry has another upscale that matches clearly better.
- No key collisions: no key maps to two different images.
- The 711 map and minimap entries were also checked by eye: the "area N" labels match.
- Outliers are deliberate retouches by efonte (redrawn 16x16 medals, SEGA logo, fonts) or ESRGAN sharpening.

The "area 3 instead of area 4" report can't be reproduced on ULJM05957. Possible explanation: efonte
dumped partly from ULJM05781 (original VC3, not E2) and the ini serves both games; on the other game
the same key can point to a different texture.

To rerun it:
1. Extract `ULJM05781/original/*`, `ULJM05781/textures.ini` and `ULJM05781/ai_upscaled/*spanish*` of
   efonte's zip into `$VC3_WORKDIR/work/pack/`.
2. Set `PACK_DIR` to the assembled pack folder (`.../ULJM05957`, with `textures.ini` and the original
   ini saved as `textures.ini.orig`).
3. Run `src/mapping_check.py` (builds the record cache in `work/`), then `src/mapping_check3.py` and
   `src/mapping_check4.py`, from `$VC3_WORKDIR`.

## Rerun

```bash
export JP_ISO=/path/to/"Senjou no Valkyria 3 E2 - Extra Edition (Japan).iso"
export EN_ISO=/path/to/"Valkyria Chronicles 3 E2 - English ReTranslation.iso"
export EFONTE_ZIP=/path/to/ULJM05781_v20200807-001.zip
export PPSSPP_SRC=/path/to/ppsspp          # v1.20.x checkout, for ext/libkirk
export CURRENT_INI=/path/to/ULJM05957/textures.ini   # optional
./run_all.sh                               # ~5-6 min; writes to tools/keys/work/ (or $VC3_WORKDIR)
```

| Variable | Default | Meaning |
|---|---|---|
| `JP_ISO`, `EN_ISO` | (required) | Japanese E2 ISO and the same ISO patched with the ReTranslation |
| `EFONTE_ZIP` | (required) | efonte's pack zip, read only |
| `PPSSPP_SRC` | (required to build `pgddec`) | PPSSPP source tree; `pgddec` links `ext/libkirk` |
| `VC3_WORKDIR` | `tools/keys/work` | where `dec/`, `pack/`, `work/` and `out/` are written |
| `CURRENT_INI` | unset | ini to measure coverage against (steps 7-8) |
| `PACK_DIR` | `$VC3_WORKDIR/pack/ULJM05957` | assembled pack folder, for `mapping_check*.py` |
| `CRILAYLA_LIB` | `src/libcrilayla.so` | CRILAYLA library; `cpk.py` falls back to pure Python if missing |
| `PYTHON`, `CC` | `python3`, `cc` | interpreter (with `xxhash`, `pillow`, `numpy`) and C compiler |

Other dependencies: `7z`, `unzip`.

Tools in `src/`:
- `pgddec.c`: PGD decryption (build: see `run_all.sh` step 0).
- `cpk.py`, `crilayla.c`: CPK reader and CRILAYLA decompressor.
- `paclz.py`: PAC chunk LZ decompressor.
- `gim.py`: GIM parser and key formula. `texkey.py`: GE parameters and full key.
- `scan.py`: scans every GIM in the CPK. `decode.py`: GIM → RGBA.
- `validate.py`, `packindex.py`, `packkeys.py`, `content_check.py`: validation against efonte's pack.
- `cpkdiff.py`: JP/EN diff at file level. `export_en.py`: CSV and PNG of the EN-changed textures.
- `all_keys.py`, `ini_active.py`, `en_reuse.py`, `en_uncovered.py`, `export_uncovered*.py`,
  `pac_palvar.py`: key lists, coverage, aliases, uncovered exports.
- `mapping_check*.py`, `sheet.py`: mapping check of an assembled pack.
- `match_data.py`, `match_clut.py`: the experiments used to work out `bufw` and the CLUT rule.

References: [VC3 file formats notes (unknownbrackets)](https://gist.github.com/unknownbrackets/78c4631a4091044d381432ffb7f1bae4),
[akorov/VC3ReTranslation](https://github.com/akorov/VC3ReTranslation).
