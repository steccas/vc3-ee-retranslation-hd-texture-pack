# ESRGAN 4x upscaling in the style of efonte's pack (Valkyria Chronicles 3)

Pipeline to upscale new textures 4x (for example the English text textures) **with exactly the same
process** as efonte's PPSSPP pack `ULJM05781_v20200807-001.zip`. On a sample of 150 textures taken from
that zip, the default settings reproduce the pack **bit-exactly** (RGB and alpha). The only differences
are ±1 on a few pixels every ~10⁵, from floating-point noise.

Model weights are not in this repository: download them yourself (see "Models") and check them against
`models/SHA256SUMS` and `models/candidates/SHA256SUMS`.

## Usage

```bash
cd tools/upscale
python upscale.py INPUT_DIR OUTPUT_DIR
```

- Recursive. Keeps relative path and file name (the PPSSPP hash) and always writes PNG.
- Skips files that already exist in the output; `--overwrite` redoes them.
- Uses the GPU automatically if `torch.cuda.is_available()` (ROCm/HIP too), else the CPU.
  Force it with `--device cpu` / `--device cuda`.
- RGBA: RGB goes through the model. Alpha is replicated to 3 channels, goes through the same model, and
  the 3rd output channel is kept, exactly as in the pack.
- Images larger than `--tile` (default 512 source px) are split into tiles with a 32 px overlap and
  feathered blending. No original in the pack is larger than 512×512, so it never triggers there.
  Test on a 512×512 forced to tile 256: PSNR 62 dB vs the untiled version, i.e. invisible seams.
- Speed on an RX 9070 XT: ~0.1 s for a 256×256 texture, ~0.5 s for 512×512 (fp32). The CPU is fine for
  a few textures.
- On ROCm, MIOpen compiles kernels for each new size on the first run, which is slow.
  `upscale.py` sets `MIOPEN_FIND_MODE=FAST` to shorten this.

**RGB vs RGBA.** An opaque RGBA input gets the dimmed alpha the pack has (≈244). An **RGB** input with
no alpha (e.g. a texture edited in GIMP and exported without alpha) comes out RGB, so 100% opaque. All
pack originals are RGBA: save edited textures **as RGBA** for consistency.

Non-default options:

| option | effect |
|---|---|
| `--keep-opaque` | if the source alpha is all 255, the output stays 255. **The pack doesn't do this**: the model darkens white, so opaque textures in the pack have alpha ≈244 (min 233 at the edges). Leave it off for consistency with the rest of the pack. |
| `--alpha model-mean / bicubic / lanczos / nearest` | other alpha methods (validated: worse, see below) |
| `--pad-mode reflect / replicate / wrap` | edge padding before upscaling, cropped afterwards (validated: worse for the default model) |
| `--half` | fp16 on GPU: faster, small numerical differences |
| `--model PATH` | another `.pth` / `.safetensors` |

## Models (`models/`)

| file | origin |
|---|---|
| `4x_fatal_Anime_500000_G.pth` | OpenModelDB "4x-Fatal-Anime" (twittman) |
| `4x_FatalPixels_340000_G.pth` | OpenModelDB "4x-Fatal-Pixels" (twittman) |
| `…_interp_075.pth` | **default**. Rebuilt with `make_interp.py` = **0.25·Anime + 0.75·FatalPixels** |
| `…_interp_025.pth` | 0.75·Anime + 0.25·FatalPixels (opposite direction, rejected) |
| `…_interp_050.pth` | 0.5/0.5 (comparison only) |

Full SHA256 of all five: `models/SHA256SUMS` (the two parents match OpenModelDB; the interpolated ones
are what `make_interp.py` produces from them).

The original interpolated `.pth` isn't available online. Its name comes from **IEU
(ImageEnhancingUtility, ptrsuder/IEU.Core)**, which writes `{A}_{B}_interp_{alpha}` with
`(1-alpha)*A + alpha*B` (`Scripts/interpModels.py`), dropping the decimal point (hence `075`). An IEU
issue (#18) mentions this exact model on game textures with alpha. `make_interp.py` uses the same
formula, and the validation confirms the direction.

Model license: CC BY-NC-SA 4.0 (twittman; Remacri: foolhardy).

## Validation (`validation/`)

Originals come from `original/sorted/` of efonte's zip, references from `ai_upscaled/` of the same zip
(same file name; 9,818 pairs, all RGBA and all exactly 4×). The zip is opened read only; set
`EFONTE_ZIP` to its path. Metrics: PSNR / SSIM / % identical pixels, RGB and alpha evaluated separately.

**Run 2**: 150 textures stratified over 69 subfolders (models 53, ui 32, portraits 24, effects 18,
maps 9, backgrounds 6, foliages 5, foregrounds 3). Sizes from 8×16 to 512×512. 99 have real alpha.

| variant | median RGB PSNR | RGB SSIM | identical RGB | identical alpha (99 with alpha) | identical opaque alpha (51) |
|---|---|---|---|---|---|
| **interp_075 (0.25A+0.75P), no pad, alpha = model channel 3** | **95.4 dB** (≈∞) | **1.0000** | **150/150**¹ | **99/99**¹ | **51/51**¹ |
| interp_075, pad replicate | 42.5 dB | 0.977 | 0/150 | 0/99 (86% pixels) | 0/51 |
| interp_025 (0.75A+0.25P) | 28.3 dB | 0.915 | 0/150 | 0/99 | 0/51 |

¹ "Identical" means ≥99.9% equal pixels. The measured minimum is 99.988%, max diff 1 (fp noise): the
files are not byte-identical.

Alpha with interp_075 and no pad, on the 99 textures with alpha: channel 3 = 99 dB / 100% identical;
channel mean = 46.0 dB; channel 1 = 37.8 dB; lanczos = 25.0 dB; bicubic = 24.7 dB; nearest = 23.1 dB.

**Run 1**: 120 textures, backgrounds/effects only (the first sampling had a bug), all 5 models.
Median RGB PSNR: interp_075 = bit-exact 120/120, reflect pad 46.0, replicate pad 45.0, interp_050 34.0,
Pixels 29.2, interp_025 29.2, Anime 25.8.

Other checks:
- `white_probe.py` / `white_exact.py`: an all-white alpha through interp_075 gives exactly the pack's
  alpha (mode 244, edges ~239, min 233). That "fingerprint" identified the model, the padding (none)
  and the channel.
- `e2e.py`: full CLI on 10 random textures, 10/10 identical to the pack (max diff 1). The CPU result
  matches the GPU within ±1.
- `tile_check.py`: tiling stays under the visible threshold (≥55 dB even with tile 128).

To repeat (from `tools/upscale/`): `python validation/index_zip.py` (builds `validation/index.json`),
then `python validation/validate.py 150 short NAME` (3 variants) or `validation/validate.py 150 full NAME`
(all 5 models plus paddings).

The sample doesn't include the ~7 hand-redrawn `ai_upscaled/ui` files. No post-processed image was found.

## Environment

- Python with `torch` (CUDA or ROCm build), `spandrel` 0.4.2, `pillow`, `numpy`; `scikit-image` only
  for the validation.
- `torchvision` (a spandrel dependency) must match your torch build. With a distribution-provided ROCm
  torch, install the matching ROCm wheel with `--no-deps`
  (e.g. `pip install --no-deps "torchvision==X+rocm7.Y" --index-url https://download.pytorch.org/whl/rocm7.Y`),
  otherwise `import spandrel` fails with `operator torchvision::nms does not exist`.

## Model comparison for text/UI (`compare/`)

`compare/build.py` writes `compare/index.html` (a local page with no external resources), labelled crop
sheets and `metrics.csv`:
- 28 text-heavy textures (`en_changed_png` plus `ui_IF`) and 6 non-text ones from the pack;
- each sheet shows original, nearest 4x, `interp_075` and the other 11 models/blends, with 2× crops;
- `compare/alpha_sheet.py` writes `compare/alpha_check.png`: alpha alone and composited on a light
  background, to check halos.

Inputs: run `compare/contact.py` first (it builds `compare/_contact/list.txt` from the key tools'
output). Env: `KEYS_OUT` = the `out/` folder of `tools/keys/run_all.sh` (default
`tools/keys/work/out`), `EFONTE_ZIP`. Model outputs are cached in `compare/out/`.

Candidate models in `models/candidates/` (hashes in `models/candidates/SHA256SUMS`), all from OpenModelDB
or the author's HF mirrors, sha256 = OpenModelDB: AnimeSharp, UltraSharp, UltraSharpV2 (DAT2),
UltraSharpV2 Lite (RealPLKSR), 2x-AnimeSharpV4 (RCAN, applied twice), FatePlus-lite (made for PSP
games), NMKD Siax, Remacri, and two 50/50 blends with `interp_075`.

**Outcome, judged by eye. The metrics in index.html are only hints.**

| Model | Outcome |
|---|---|
| **Remacri** | The most faithful on bitmap fonts, digits and menus. The only one that renders `0123456789?/∞` (128×8 texture) exactly and doesn't warp SELECT START, NO ENTRY, Carry Hp Ammo. Solid whites, clean alpha. |
| AnimeSharp | Second. Best on microscopic blackletter text on parchment (Combat Report), but slightly mangles the "8" of the pixel digits. |
| `interp_075` (default) | Invents strokes in small digits (2, 4, 8). Dims whites (alpha ≈244), so white text on a light background looks veiled. |
| UltraSharp | Gets letters wrong ("A", "8"). |
| UltraSharpV2 DAT2 | Hallucinates digits and striped lines in small text; also ~10× slower. |
| Siax | Adds noise. |
| FatePlus | Similar style to the default, same digit flaws. |
| AnimeSharpV4 | **Rejected**: erases thin white strokes on black (text turns dark, same on CPU and GPU; maybe an RCAN detection issue in spandrel 0.4.2). |
| Blends with `interp_075` | Inherit the white dimming (AnimeSharp blend: alpha ≈242) and add nothing. |

Recommended for text/UI textures:

```bash
python upscale.py IN OUT --model models/candidates/4x_foolhardy_Remacri.pth --pad-mode replicate
```

Without padding Remacri dirties the edges (alpha 0 becomes up to 12, alpha 255 drops to 239). With
`--pad-mode replicate` the edges stay clean (0 → ≤2, 255 → 255). For non-text textures (portraits, maps,
models) keep the default `interp_075`, which matches the pack's style exactly.

## Selecting the UI textures with text (`ui_text/`)

`ui_text/contact_ui.py` builds contact sheets of the uncovered UI textures (`work/_review/`);
`ui_text/classify.py` records the visual review (which ones have text and go through Remacri) and writes
`work/ui_text_select.csv`. The review notes are in Italian. Env: `KEYS_OUT`, `FONT` (TTF for labels).
