# Valkyria Chronicles 3 Extra Edition: English ReTranslation-ready AI upscaled texture pack (PPSSPP)

A version of **efonte's AI upscaled texture pack** for *Valkyria Chronicles 3 Extra Edition*
(ULJM05957) that works with the **English ReTranslation** by akorov. efonte's pack
([original post](https://forums.ppsspp.org/showthread.php?tid=26728&pid=137985#pid137985)) is the base
for everything here: it was only extended, using his model and settings so the style matches.

Forum thread: <https://forums.ppsspp.org/showthread.php?tid=26728>

> **efonte:** if you'd rather this didn't re-host your work, or you want something changed or merged
> into your pack, just say so and it will be taken down or adjusted.

## Downloads

All files are on the [**Releases page (v1)**](https://github.com/steccas/vc3-ee-retranslation-hd-texture-pack/releases/tag/v1).

| Package | File | Size | SHA256 |
|---|---|---|---|
| **Full pack** (ready to use) | `VC3_E2_EN_texture_pack_20261002.zip`, published in 4 parts `.zip.001` … `.zip.004` | 6.82 GiB (7,325,142,836 bytes) | `92100028fe6589d71397402b7226a1ed2fcc4c748637062cf23095db06a1e0e9` (joined zip) |
| **Add-on only** (needs efonte's pack) | `VC3_ReTL_texture_addon.zip` | 1.22 GiB (1,310,044,070 bytes) | `a29f0b5b3885c97b7b46ea4d8bc31baddc3d8493722d3c540b0795be8bfa465e` |

The full pack is split because GitHub limits each release file to 2 GiB. Download **all four parts**
into the same folder, plus `SHA256SUMS.txt` if you want to check them, then:

- **Windows:** open `VC3_E2_EN_texture_pack_20261002.zip.001` with [7-Zip](https://www.7-zip.org/)
  and extract: 7-Zip joins the parts by itself. (Or join them first with
  `copy /b VC3_E2_EN_texture_pack_20261002.zip.001+VC3_E2_EN_texture_pack_20261002.zip.002+VC3_E2_EN_texture_pack_20261002.zip.003+VC3_E2_EN_texture_pack_20261002.zip.004 VC3_E2_EN_texture_pack_20261002.zip`.)
- **Linux / macOS:**
  ```bash
  cat VC3_E2_EN_texture_pack_20261002.zip.0* > VC3_E2_EN_texture_pack_20261002.zip
  sha256sum VC3_E2_EN_texture_pack_20261002.zip    # macOS: shasum -a 256
  # or check everything you downloaded at once:
  sha256sum -c --ignore-missing SHA256SUMS.txt
  ```
- **Android:** join the parts on a PC first (as above), then copy the joined zip or the extracted
  folder to the device.

## What it is

- **Full pack:** one ready-to-use pack for **VC3 Extra Edition (ULJM05957)** patched with the English
  ReTranslation (v20260625). It contains efonte's pack, the additions below and a cleaned
  `textures.ini`. You don't need to download efonte's pack separately.
- **Add-on (optional):** only the new files plus the new `textures.ini`, for people who already have
  efonte's pack.

## What's new compared to efonte's pack

- **143 textures changed by the ReTranslation**, now upscaled: title screen, main menu, Gallian map,
  chapter titles, Combat Report, deployment/battle UI, boss name plates and number fonts.
  The patch gives them new hashes, so without this they show at native resolution.
- **49 UI textures with text**, redone with a model that handles text better: LEVEL UP, FAILED,
  SUCCESS, Congratulations!, OPEN FIRE, ORDER sheets, digits, months…
- **2,930 textures the original pack didn't cover**, upscaled with efonte's model:
  - character portraits for events and battles;
  - 299 battle minimaps;
  - weapons, accessories and ground;
  - vehicles and their camo/faction palette variants.
- **Odioregistrarme's 7 hand-made HD textures** (post #3 of the thread) are included: the Gallia and
  Empire flags, the turn icons and a few small UI icons. They replace the AI versions.
- **Cleaned `textures.ini`:** 591 Spanish-only entries removed, because they never trigger with the
  English ISO. The 2 Spanish entries the English version still uses are kept.
- **Lossless PNG recompression** with oxipng. Pixels are identical and file names unchanged.
- **Not included:** efonte's `original/` native dumps. If you want them, get them from his link in
  post #1.

## Install

**Full pack**
1. Join the parts (see [Downloads](#downloads)) and extract `VC3_E2_EN_texture_pack_20261002.zip` into
   `PSP/TEXTURES/`. You should end up with `PSP/TEXTURES/ULJM05957/textures.ini`.
   - If you already have a `ULJM05957` folder, remove or rename it first. Don't merge the two folders.
2. Keep the folder name **ULJM05957**: that's the disc ID of the ReTranslation ISO (Extra Edition).
3. In PPSSPP, turn on **Settings → Tools → Developer tools → Texture replacement → Replace textures**.

**Add-on (if you already have efonte's pack)**
1. efonte's zip extracts to a `ULJM05781` folder. Put it in `PSP/TEXTURES/` and rename it to **`ULJM05957`**.
2. Extract the add-on into `PSP/TEXTURES/` (the archive already contains the `ULJM05957/` folder).
   Overwrite `textures.ini` when asked.
3. Optional: add Odioregistrarme's textures from post #3 (overwrite). The full pack already has them.

Tested on PPSSPP 1.20.4 (PC Linux) and Android (AYN Thor).

## How it was made (short version)

- The textures weren't dumped by playing. `DATA.BIN` was decrypted (PGD → CRI CPK/CRILAYLA → GIM,
  plus the LZ compression inside the `.PAC` files), then PPSSPP's replacement keys were computed
  offline (xxh64, `ignoreAddress`).
- **Checking the keys:**
  - against efonte's original dumps: 6,815 textures matched pixel-for-pixel, 99.6% of the ones that
    could be checked;
  - against in-game dumps on the English ISO: 25/25.
- **Main upscale:** `4x_fatal_Anime_500000_G_4x_FatalPixels_340000_G_interp_075`, efonte's exact model,
  rebuilt from the two parent models. On 150 sample textures it reproduces his output exactly.
- **Text/UI** (the 143 + 49 textures above): `4x_foolhardy_Remacri`.
- **Mapping check:** every entry of the pack was compared with the decoded game data (all 711
  map/minimap entries included). No wrong mappings and no key collisions on ULJM05957.

## Tools

The source code of the extraction, key computation, validation and upscaling pipeline is in
[`tools/`](tools/README.md):

- [`tools/keys/`](tools/keys/README.md): PGD decryption, CPK/CRILAYLA/GIM/PAC readers, offline PPSSPP
  key computation, validation and mapping checks (`run_all.sh`).
- [`tools/upscale/`](tools/upscale/README.md): the bit-exact ESRGAN upscaler, model interpolation,
  validation and the text-model comparison.

No game data, decrypted files, binaries or model weights are included. Paths are passed through
environment variables, documented in [`tools/README.md`](tools/README.md).

## Known limits

- **Dialogue font:** it's a runtime glyph cache, so it can't be precomputed. A texture upscaling shader
  in PPSSPP helps there.
- **Short palette fades/flashes:** the game generates them at runtime, so they aren't covered.
- **Untranslated Japanese text:** text the ReTranslation left in Japanese stays Japanese, just sharper.
- **DLC:** no DLC textures.
- **ReTranslation version:** made for v20260625. A later version that changes textures may need an
  update of this pack.
- **"Area 3 instead of area 4" (post #3):** not reproducible on ULJM05957. It may only affect the
  original release, ULJM05781. If you see it on Extra Edition, please post the texture name from
  "Save new textures" in the forum thread or open an issue.

## License

- **Free and non-commercial.** The ESRGAN models used (4x-Fatal-Anime, 4x-Fatal-Pixels, 4x Remacri)
  are all CC BY-NC-SA 4.0, so the texture additions are shared under the same terms
  ([CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/), see [`LICENSE`](LICENSE)):
  credit the authors, no commercial use, share derivatives under the same license.
- **Everyone else's work stays theirs:** efonte's and Odioregistrarme's work belongs to them, and the
  original game artwork belongs to SEGA.
- **Tools:** the code in `tools/` is GPL-3.0-or-later ([`tools/LICENSE`](tools/LICENSE)).

Details in [`LICENSES.md`](LICENSES.md).

## Credits

See [`CREDITS.md`](CREDITS.md). In short: efonte (the original pack), Odioregistrarme (hand-made HD
textures), LunaMoo (fonts), akorov and the VC3 ReTranslation team, twittman and foolhardy (models),
PPSSPP and the libkirk authors, unknownbrackets (file format notes).

The extraction and hashing tools and the scripts were written with the help of an AI assistant
(Claude). Everything was checked against real dumps.

## Changelog

- **v1 (2026-10-02):** first release. Full English-ready pack plus an optional add-on.
