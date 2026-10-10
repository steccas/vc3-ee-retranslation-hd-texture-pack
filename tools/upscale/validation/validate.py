# SPDX-License-Identifier: GPL-3.0-or-later
"""Compare upscaling variants against efonte's pack (ai_upscaled in the ZIP).

Reads the ZIP read-only. Picks a stratified sample of textures present in both
original/sorted and ai_upscaled, runs each (model, padding) variant once, derives alpha
variants from the same output, and reports PSNR/SSIM/exact-match for RGB and alpha.
"""
import os
os.environ.setdefault("MIOPEN_FIND_MODE", "FAST")
import io, json, random, sys, zipfile, collections, time, csv
from pathlib import Path
import numpy as np
import torch
from PIL import Image
from skimage.metrics import structural_similarity as ssim

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from upscale import Upscaler  # noqa

ZIP = os.environ.get('EFONTE_ZIP', 'ULJM05781_v20200807-001.zip')
M = HERE.parent / 'models'
MODELS = {
    'interp075 (0.25A+0.75P)': M / '4x_fatal_Anime_500000_G_4x_FatalPixels_340000_G_interp_075.pth',
    'interp025 (0.75A+0.25P)': M / '4x_fatal_Anime_500000_G_4x_FatalPixels_340000_G_interp_025.pth',
    'interp050': M / '4x_fatal_Anime_500000_G_4x_FatalPixels_340000_G_interp_050.pth',
    'Anime': M / '4x_fatal_Anime_500000_G.pth',
    'Pixels': M / '4x_FatalPixels_340000_G.pth',
}
N = int(sys.argv[1]) if len(sys.argv) > 1 else 120
QUICK_PADS = ['none', 'reflect', 'replicate']


def psnr(a, b):
    mse = np.mean((a.astype(np.float64) - b.astype(np.float64)) ** 2)
    return 99.0 if mse == 0 else 10 * np.log10(255 ** 2 / mse)


def pick_sample(rows, z, n):
    random.seed(42)
    by = collections.defaultdict(list)
    for r in rows:
        cat = '/'.join(r['up'].split('/')[2:-1][:2])
        by[cat].append(r)
    cats = sorted(by)
    out = []
    # round-robin across categories, which mixes sizes and alpha/no-alpha
    for c in cats:
        random.shuffle(by[c])
    i = 0
    while len(out) < n:
        progressed = False
        for c in cats:
            if i < len(by[c]) and len(out) < n:
                out.append(by[c][i]); progressed = True
        i += 1
        if not progressed:
            break
    return out


def main():
    z = zipfile.ZipFile(ZIP)
    rows = json.load(open(HERE / 'index.json'))
    sample = pick_sample(rows, z, N)
    data = []
    for r in sample:
        a = np.array(Image.open(io.BytesIO(z.read(r['orig']))).convert('RGBA'))
        b = np.array(Image.open(io.BytesIO(z.read(r['up']))).convert('RGBA'))
        data.append((r, a, b))
    print(f'sample: {len(data)} textures, {sum(d[1][...,3].min() < 255 for d in data)} with real alpha', flush=True)
    results = []  # (variant, idx, metrics)
    variants = [(m, p) for m in MODELS for p in (QUICK_PADS if m.startswith('interp075') else ['none'])]
    if len(sys.argv) > 2 and sys.argv[2] == 'short':  # best candidate + closest alternatives only
        variants = [(list(MODELS)[0], 'none'), (list(MODELS)[0], 'replicate'), (list(MODELS)[1], 'none')]
    for mname, pad in variants:
        up = Upscaler(MODELS[mname], pad_mode=pad, pad=8, tile=0)
        t0 = time.time()
        for i, (r, a, b) in enumerate(data):
            rgb = up.upscale_rgb(a[..., :3])
            al3 = up.upscale_rgb(np.repeat(a[..., 3:4], 3, axis=2)).astype(np.float64)
            H, W = rgb.shape[:2]
            alphas = {
                'model_ch2': al3[..., 2].round(),
                'model_mean': al3.mean(2).round(),
                'model_ch0': al3[..., 0].round(),
            }
            if pad == 'none' and mname.startswith('interp075'):
                for k, mm in [('nearest', Image.NEAREST), ('bicubic', Image.BICUBIC), ('lanczos', Image.LANCZOS)]:
                    alphas[k] = np.array(Image.fromarray(a[..., 3]).resize((W, H), mm)).astype(np.float64)
            tb = b[..., :3]
            m = dict(rgb_psnr=psnr(rgb, tb), rgb_ssim=ssim(rgb, tb, channel_axis=2, data_range=255),
                     rgb_exact=float((rgb == tb).all(2).mean()))
            # RGB only where pack alpha>0 (visible pixels)
            vis = b[..., 3] > 0
            m['rgb_psnr_vis'] = psnr(rgb[vis], tb[vis]) if vis.any() else float('nan')
            for k, al in alphas.items():
                m[f'a_{k}_psnr'] = psnr(al, b[..., 3])
                m[f'a_{k}_ssim'] = ssim(al.astype(np.uint8), b[..., 3], data_range=255)
                m[f'a_{k}_exact'] = float((al == b[..., 3]).mean())
            if i % 20 == 0:
                print(f'  {i}/{len(data)} {time.time() - t0:.1f}s', flush=True)
            results.append(dict(variant=f'{mname} | pad={pad}', fn=r['fn'], cat='/'.join(r['up'].split('/')[2:-1][:2]),
                                size=f"{r['osz'][0]}x{r['osz'][1]}", has_alpha=bool(a[..., 3].min() < 255), **m))
        print(f'{mname} pad={pad}: {time.time() - t0:.1f}s', flush=True)
        del up; torch.cuda.empty_cache() if torch.cuda.is_available() else None
    out = sys.argv[3] if len(sys.argv) > 3 else 'results'
    with open(HERE / f'{out}.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=sorted({k for r in results for k in r}, key=lambda k: (k not in ('variant', 'fn', 'cat', 'size', 'has_alpha'), k)))
        w.writeheader(); w.writerows(results)
    summarize(results)


def summarize(results):
    by = collections.defaultdict(list)
    for r in results:
        by[r['variant']].append(r)
    print('\n=== RGB (all textures): median/mean PSNR, mean SSIM, %pixel bit-exact, #textures bit-exact')
    for v, rs in by.items():
        p = np.array([r['rgb_psnr'] for r in rs]); s = np.array([r['rgb_ssim'] for r in rs]); e = np.array([r['rgb_exact'] for r in rs])
        print(f'{v:45s} med {np.median(p):6.2f} mean {np.mean(np.minimum(p, 60)):6.2f} ssim {s.mean():.4f} '
              f'exact {100 * e.mean():5.1f}% fullymatch {(e > 0.999).sum()}/{len(rs)}')
    print('\n=== Alpha (textures with real alpha only; opaque ones listed separately)')
    for v, rs in by.items():
        keys = sorted({k[2:-5] for k in rs[0] if k.startswith('a_') and k.endswith('_psnr')})
        for sub, name in [([r for r in rs if r['has_alpha']], 'alpha'), ([r for r in rs if not r['has_alpha']], 'opaque')]:
            if not sub:
                continue
            for k in keys:
                p = np.array([r[f'a_{k}_psnr'] for r in sub]); s = np.array([r[f'a_{k}_ssim'] for r in sub]); e = np.array([r[f'a_{k}_exact'] for r in sub])
                print(f'{v:45s} {name:6s} {k:11s} med {np.median(p):6.2f} ssim {s.mean():.4f} exact {100 * e.mean():5.1f}% fullymatch {(e > 0.999).sum()}/{len(sub)}')


if __name__ == '__main__':
    main()
