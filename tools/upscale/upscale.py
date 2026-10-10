#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""4x ESRGAN upscaler that reproduces the style of efonte's Valkyria Chronicles 3 PPSSPP pack.

Usage:
    ./venv/bin/python upscale.py INPUT_DIR OUTPUT_DIR [options]

- Walks INPUT_DIR recursively (png/jpg/bmp/tga/webp), writes PNGs with the same relative path
  and filename into OUTPUT_DIR (so PPSSPP hash filenames are preserved).
- Skips files that already exist in OUTPUT_DIR (use --overwrite to redo).
- Uses the GPU automatically if torch.cuda is available (CUDA or ROCm/HIP), else CPU.
- RGBA: RGB goes through the model; alpha is upscaled separately (default: alpha as a
  grayscale image through the same model, which is what the pack did).
See README.md for the validation behind the defaults.
"""
import argparse
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("MIOPEN_FIND_MODE", "FAST")  # avoid long per-shape kernel searches on ROCm
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image

HERE = Path(__file__).resolve().parent
DEFAULT_MODEL = HERE / "models" / "4x_fatal_Anime_500000_G_4x_FatalPixels_340000_G_interp_075.pth"
EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".tga", ".webp"}


def pick_device(name="auto"):
    if name != "auto":
        return torch.device(name)
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def load_model(path, device, half=False):
    import spandrel
    desc = spandrel.ModelLoader(device="cpu").load_from_file(str(path))
    model = desc.model.eval().to(device)
    if half:
        model = model.half()
    for p in model.parameters():
        p.requires_grad_(False)
    return model, desc.scale


class Upscaler:
    def __init__(self, model_path=DEFAULT_MODEL, device="auto", pad=0, pad_mode="none",
                 tile=512, tile_overlap=32, alpha_mode="model", half=False,
                 keep_opaque=False):
        self.device = pick_device(device)
        self.half = half and self.device.type == "cuda"
        self.model, self.scale = load_model(model_path, self.device, self.half)
        # 2x models are applied twice to reach 4x; 4x models once
        self.passes = 1
        while self.scale ** self.passes < 4:
            self.passes += 1
        self.total_scale = self.scale ** self.passes
        self.pad = pad if pad_mode != "none" else 0
        self.pad_mode = pad_mode
        self.tile = tile
        self.overlap = tile_overlap
        self.alpha_mode = alpha_mode
        self.keep_opaque = keep_opaque

    # ---- core: float32 HxWx3 in [0,1] -> 4x float32 HxWx3 in [0,1]
    @torch.inference_mode()
    def _run(self, t):  # t: 1x3xHxW on device
        dtype = torch.float16 if self.half else torch.float32
        return self.model(t.to(dtype)).float().clamp_(0, 1)

    @torch.inference_mode()
    def _run_tiled(self, t):
        _, _, h, w = t.shape
        s = self.scale
        if self.tile <= 0 or (h <= self.tile and w <= self.tile):
            return self._run(t)
        out = torch.zeros((1, 3, h * s, w * s), device=t.device)
        weight = torch.zeros_like(out)
        step = self.tile - 2 * self.overlap
        ys = list(range(0, max(h - self.tile, 0) + 1, step))
        xs = list(range(0, max(w - self.tile, 0) + 1, step))
        if ys[-1] + self.tile < h:
            ys.append(h - self.tile)
        if xs[-1] + self.tile < w:
            xs.append(w - self.tile)
        for y in ys:
            for x in xs:
                y1, x1 = min(y + self.tile, h), min(x + self.tile, w)
                o = self._run(t[:, :, y:y1, x:x1])
                # feathered blending over the overlap region
                th, tw = (y1 - y) * s, (x1 - x) * s
                m = torch.ones((1, 1, th, tw), device=t.device)
                ov = self.overlap * s
                if ov > 0:
                    ramp = torch.linspace(0, 1, ov + 2, device=t.device)[1:-1]
                    if y > 0:
                        m[:, :, :ov, :] *= ramp.view(1, 1, -1, 1)
                    if y1 < h:
                        m[:, :, -ov:, :] *= ramp.flip(0).view(1, 1, -1, 1)
                    if x > 0:
                        m[:, :, :, :ov] *= ramp.view(1, 1, 1, -1)
                    if x1 < w:
                        m[:, :, :, -ov:] *= ramp.flip(0).view(1, 1, 1, -1)
                out[:, :, y * s:y1 * s, x * s:x1 * s] += o * m
                weight[:, :, y * s:y1 * s, x * s:x1 * s] += m
        return out / weight.clamp_min(1e-8)

    def upscale_rgb(self, arr):
        """arr: HxWx3 uint8 -> (4H)x(4W)x3 uint8"""
        t = torch.from_numpy(arr.astype(np.float32) / 255.0).permute(2, 0, 1)[None].to(self.device)
        p = self.pad
        if p > 0:
            mode = {"reflect": "reflect", "replicate": "replicate", "wrap": "circular"}[self.pad_mode]
            pp = p
            if mode == "reflect":  # reflect needs pad < size
                pp = min(p, t.shape[2] - 1, t.shape[3] - 1)
            if pp > 0:
                t = F.pad(t, (pp, pp, pp, pp), mode=mode)
            p = pp
        o = t
        for _ in range(self.passes):
            o = self._run_tiled(o)
        if p > 0:
            s = self.total_scale * p
            o = o[:, :, s:-s, s:-s]
        o = (o[0].permute(1, 2, 0).cpu().numpy() * 255.0).round().astype(np.uint8)
        return o

    def upscale_alpha(self, a, size):
        """a: HxW uint8 -> (4H)x(4W) uint8"""
        if self.keep_opaque and a.min() == 255:
            return np.full((size[1], size[0]), 255, np.uint8)
        if self.alpha_mode in ("model", "model-mean"):
            # alpha replicated to 3 channels and run through the same model. The pack keeps the
            # model's 3rd output channel: that reproduces efonte's alpha bit-exactly.
            o = self.upscale_rgb(np.repeat(a[..., None], 3, axis=2))
            if self.alpha_mode == "model":
                return o[..., 2].copy()
            return o.astype(np.float32).mean(axis=2).round().astype(np.uint8)
        m = {"nearest": Image.NEAREST, "bilinear": Image.BILINEAR, "bicubic": Image.BICUBIC,
             "lanczos": Image.LANCZOS}[self.alpha_mode]
        return np.array(Image.fromarray(a).resize(size, m))

    def upscale_image(self, img):
        has_alpha = img.mode in ("RGBA", "LA", "PA") or (img.mode == "P" and "transparency" in img.info)
        if has_alpha:
            rgba = np.array(img.convert("RGBA"))
            rgb = self.upscale_rgb(rgba[..., :3])
            h, w = rgb.shape[:2]
            alpha = self.upscale_alpha(rgba[..., 3], (w, h))
            return Image.fromarray(np.dstack([rgb, alpha]), "RGBA")
        return Image.fromarray(self.upscale_rgb(np.array(img.convert("RGB"))), "RGB")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input_dir")
    ap.add_argument("output_dir")
    ap.add_argument("--model", default=str(DEFAULT_MODEL))
    ap.add_argument("--device", default="auto", help="auto|cpu|cuda (cuda also means ROCm)")
    ap.add_argument("--alpha", dest="alpha_mode", default="model",
                    choices=["model", "model-mean", "nearest", "bilinear", "bicubic", "lanczos"],
                    help="model = alpha through the model, 3rd output channel (pack-exact, default)")
    ap.add_argument("--keep-opaque", action="store_true",
                    help="fully opaque source alpha stays 255 (the pack lets the model dim it to ~244)")
    ap.add_argument("--pad-mode", default="none", choices=["none", "reflect", "replicate", "wrap"],
                    help="edge padding before upscaling (cropped afterwards)")
    ap.add_argument("--pad", type=int, default=8, help="padding in source pixels (if --pad-mode != none)")
    ap.add_argument("--tile", type=int, default=512, help="tile size in source px (0 = no tiling)")
    ap.add_argument("--tile-overlap", type=int, default=32)
    ap.add_argument("--half", action="store_true", help="fp16 on GPU (faster, tiny differences)")
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    src, dst = Path(args.input_dir), Path(args.output_dir)
    files = sorted(p for p in src.rglob("*") if p.is_file() and p.suffix.lower() in EXTS)
    todo = []
    for p in files:
        out = dst / p.relative_to(src).with_suffix(".png")
        if out.exists() and not args.overwrite:
            continue
        todo.append((p, out))
    print(f"{len(files)} images, {len(files) - len(todo)} already done, {len(todo)} to do", flush=True)
    if not todo:
        return
    up = Upscaler(args.model, args.device, args.pad, args.pad_mode, args.tile, args.tile_overlap,
                  args.alpha_mode, args.half, args.keep_opaque)
    print(f"device={up.device} model={Path(args.model).name} alpha={args.alpha_mode} "
          f"pad={args.pad_mode}:{up.pad} tile={args.tile}", flush=True)
    t0 = time.time()
    for i, (p, out) in enumerate(todo, 1):
        try:
            img = Image.open(p)
            img.load()
            res = up.upscale_image(img)
            out.parent.mkdir(parents=True, exist_ok=True)
            tmp = out.with_suffix(".tmp.png")
            res.save(tmp, optimize=False)
            os.replace(tmp, out)
            print(f"[{i}/{len(todo)}] {p.relative_to(src)} {img.size} -> {res.size} ({time.time() - t0:.1f}s)",
                  flush=True)
        except Exception as e:  # keep going on bad files
            print(f"[{i}/{len(todo)}] ERROR {p}: {e}", file=sys.stderr, flush=True)


if __name__ == "__main__":
    main()
