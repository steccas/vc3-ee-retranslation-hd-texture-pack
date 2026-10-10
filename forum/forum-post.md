**Valkyria Chronicles 3 Extra Edition: English ReTranslation-ready AI upscaled pack (based on efonte's pack)**

Hi everyone. This is a version of **efonte's AI upscaled pack** ([original post #1](https://forums.ppsspp.org/showthread.php?tid=26728&pid=137985#pid137985)) for VC3 Extra Edition patched with the new [English ReTranslation](https://github.com/akorov/VC3ReTranslation) by akorov. efonte's pack is the base for everything here: I only extended it, using his model and settings so the style matches.

**Requires:** VC3 Extra Edition patched with the [English ReTranslation](https://github.com/akorov/VC3ReTranslation) (v20260625, from its [Releases page](https://github.com/akorov/VC3ReTranslation/releases)). The patch is applied to your own Japanese ISO with the scripts in that repository.

**efonte:** if you'd rather I didn't re-host your work, or you want something changed or merged into your pack, just tell me and I'll take it down or adjust it.

---

### What it is

- **Full pack:** one ready-to-use pack for **VC3 Extra Edition (ULJM05957)** patched with the English ReTranslation (v20260625). It contains efonte's pack, my additions and a cleaned `textures.ini`. You don't need to download efonte's pack separately.
- **Add-on (optional):** only the new files plus the new `textures.ini`, for people who already have efonte's pack.

### What's new compared to efonte's pack

- **143 textures changed by the ReTranslation**, now upscaled: title screen, main menu, Gallian map, chapter titles, Combat Report, deployment/battle UI, boss name plates and number fonts.
  - The patch gives them new hashes, so without this they show at native resolution.
- **49 UI textures with text**, redone with a model that handles text better: LEVEL UP, FAILED, SUCCESS, Congratulations!, OPEN FIRE, ORDER sheets, digits, months…
- **2,930 textures the original pack didn't cover**, upscaled with efonte's model:
  - character portraits for events and battles;
  - 299 battle minimaps;
  - weapons, accessories and ground;
  - vehicles and their camo/faction palette variants.
- **Odioregistrarme's 7 hand-made HD textures from post #3** are included: the Gallia and Empire flags ("HD maps of Gallia and the Empire" in his post), the turn icons and a few small UI icons. They replace the AI versions.
- **Cleaned `textures.ini`:** 591 Spanish-only entries removed, because they never trigger with the English ISO. 2 Spanish entries the English version still uses are kept.
- **Lossless PNG recompression of the whole pack, efonte's files included:** every PNG was recompressed with oxipng (`-o 4 --strip safe`, no alpha tricks). Each file was decoded before and after and checked pixel-for-pixel (RGBA): all identical, file names unchanged. The pack went from 8.37 GiB to 6.87 GiB (−18%), so it's smaller to download and store, especially on Android.
- **Not included:** efonte's `original/` native dumps. If you want them, get them from his MEGA link in post #1.

### Install

**Full pack**
1. Extract `VC3_E2_EN_texture_pack_20261002.zip` into `PSP/TEXTURES/`. You should end up with `PSP/TEXTURES/ULJM05957/textures.ini`.
   - If you already have a `ULJM05957` folder, remove or rename it first. Don't merge the two folders.
2. Keep the folder name **ULJM05957**: that's the disc ID of the ReTranslation ISO (Extra Edition).
3. In PPSSPP, turn on **Settings → Tools → Developer tools → Texture replacement → Replace textures**.

**Add-on (if you already have efonte's pack)**
1. efonte's zip extracts to a `ULJM05781` folder. Put it in `PSP/TEXTURES/` and rename it to **`ULJM05957`**.
2. Extract the add-on into `PSP/TEXTURES/` (the archive already contains the `ULJM05957/` folder). Overwrite `textures.ini` when asked.
3. Optional: add Odioregistrarme's textures from post #3 (overwrite). The full pack already has them.

Tested on PPSSPP 1.20.4 on PC (Linux) and on Android (AYN Thor).

### How it was made (short version, for the curious)

- I didn't dump these by playing. I decrypted `DATA.BIN` (PGD → CRI CPK/CRILAYLA → GIM, plus the LZ compression inside the `.PAC` files), then computed PPSSPP's replacement keys offline (xxh64, `ignoreAddress`).
- **Checking the keys:**
  - Against efonte's original dumps: 6,815 textures matched pixel-for-pixel, which is 99.6% of the ones that could be checked.
  - Against my own in-game dumps on the English ISO: 25/25.
- **Main upscale:** `4x_fatal_Anime_500000_G_4x_FatalPixels_340000_G_interp_075`, efonte's exact model, rebuilt from the two parent models. On 150 sample textures it reproduces his output exactly.
- **Text/UI** (the 143 + 49 textures above): `4x_foolhardy_Remacri`.
- **Mapping check:** I compared every entry of the pack with the decoded game data (all 711 map/minimap entries included). I found no wrong mappings and no key collisions on ULJM05957.

### Known limits

- **Dialogue font:** it's a runtime glyph cache, so it can't be precomputed. A texture upscaling shader in PPSSPP helps there.
- **Short palette fades/flashes:** the game generates them at runtime, so they aren't covered.
- **Untranslated Japanese text:** text the ReTranslation left in Japanese stays Japanese, just sharper.
- **DLC:** no DLC textures.
- **ReTranslation version:** made for v20260625. A later version that changes textures may need an update of this pack.
- **"Area 3 instead of area 4" (post #3):** I can't reproduce it on ULJM05957. It may only affect the original release, ULJM05781. If you see it on Extra Edition, please post the texture name from "Save new textures".

### Downloads

- **Full pack:** `VC3_E2_EN_texture_pack_20261002.zip`, 6.82 GiB (7,325,142,836 bytes)
  - GitHub release (4 parts `.zip.001`–`.004`, each under 2 GiB): [https://github.com/steccas/vc3-ee-retranslation-hd-texture-pack/releases/tag/v1](https://github.com/steccas/vc3-ee-retranslation-hd-texture-pack/releases/tag/v1)
  - Join them: on Windows open `.zip.001` with 7-Zip; on Linux/macOS `cat VC3_E2_EN_texture_pack_20261002.zip.0* > VC3_E2_EN_texture_pack_20261002.zip`.
  - SHA256: `92100028fe6589d71397402b7226a1ed2fcc4c748637062cf23095db06a1e0e9`
- **Add-on only** (needs efonte's pack): `VC3_ReTL_texture_addon.zip`, 1.22 GiB (1,310,044,070 bytes)
  - [https://github.com/steccas/vc3-ee-retranslation-hd-texture-pack/releases/download/v1/VC3_ReTL_texture_addon.zip](https://github.com/steccas/vc3-ee-retranslation-hd-texture-pack/releases/download/v1/VC3_ReTL_texture_addon.zip)
  - SHA256: `a29f0b5b3885c97b7b46ea4d8bc31baddc3d8493722d3c540b0795be8bfa465e`

### License

- **Free and non-commercial.** The ESRGAN models used (4x-Fatal-Anime, 4x-Fatal-Pixels, 4x Remacri) are all CC BY-NC-SA 4.0. So my additions are shared under the same terms ([CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/)): credit the authors, no commercial use, share derivatives under the same license.
- **Everyone else's work stays theirs:** efonte's and Odioregistrarme's work belongs to them, and the original game artwork belongs to SEGA.

### Credits

- **efonte:** the original AI upscaled pack (post #1). This release is built on it.
- **Odioregistrarme:** the hand-made HD flags, turn icons and UI icons included here (post #3), and the "area 3/4" report.
- **LunaMoo:** the fonts in efonte's pack.
- **ArcEnCiel:** the reduced (3x) mirror of efonte's pack for people hitting MEGA's limit (post #5).
- **IBNobody:** the notes on duplicate hashes and dialog bubbles (post #10).
  - The duplicates are real: 74 of the 143 ReTranslation textures have identical pixels but a new encoding, so they get a new hash.
- **chrome99001:** for asking for ReTranslation support (post #20).
- **akorov and the [VC3 ReTranslation](https://github.com/akorov/VC3ReTranslation) team:** the English ReTranslation.
- **Selvaria Team:** the Spanish translation the original pack was made for.
- **twittman:** the 4x-Fatal-Anime and 4x-Fatal-Pixels models (CC BY-NC-SA 4.0).
- **foolhardy:** the 4x Remacri model (CC BY-NC-SA 4.0).
- **PPSSPP (hrydgard and contributors):** the emulator, its texture replacement code, and the libkirk code used for PGD decryption.
- **unknownbrackets:** the [VC3 file formats notes](https://gist.github.com/unknownbrackets/78c4631a4091044d381432ffb7f1bae4).

The extraction and hashing tools and the scripts were written with the help of an AI assistant (Claude). Everything was checked against real dumps.

### Source and tools

Everything (README, tools to decrypt/compute the keys and to upscale, licenses) is on GitHub: [https://github.com/steccas/vc3-ee-retranslation-hd-texture-pack](https://github.com/steccas/vc3-ee-retranslation-hd-texture-pack).

### Changelog

- **v1 (2026-10-02):** first release. Full English-ready pack plus an optional add-on.
