# SPDX-License-Identifier: GPL-3.0-or-later
"""Model comparison for text/UI textures: runs every candidate model on a test set,
builds labeled crop sheets (sheet_XX.png), an index.html and metrics.csv.

Usage: ./venv/bin/python compare/build.py [--only-sheets]
Outputs of each model are cached in compare/out/<model>/<name>.png (full RGBA, 4x).
Inputs are read only.
"""
import csv, io, json, os, sys, time, zipfile, html
from pathlib import Path
os.environ.setdefault("MIOPEN_FIND_MODE", "FAST")
import numpy as np
import torch
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
from upscale import Upscaler  # noqa

# KEYS_OUT: out/ folder written by tools/keys/run_all.sh (en_changed_png/, uncovered_png/)
# EFONTE_ZIP: efonte's original pack zip (read only)
R = os.environ.get('KEYS_OUT', str(ROOT.parent / 'keys' / 'work' / 'out')).rstrip('/') + '/'
ZIP = os.environ.get('EFONTE_ZIP', 'ULJM05781_v20200807-001.zip')
C = ROOT / 'models' / 'candidates'
MODELS = [  # (label, path)
    ('interp_075 (attuale)', ROOT / 'models' / '4x_fatal_Anime_500000_G_4x_FatalPixels_340000_G_interp_075.pth'),
    ('AnimeSharp', C / '4x-AnimeSharp.pth'),
    ('UltraSharp', C / '4x-UltraSharp.pth'),
    ('UltraSharpV2 (DAT2)', C / '4x-UltraSharpV2.safetensors'),
    ('UltraSharpV2 Lite', C / '4x-UltraSharpV2_Lite.safetensors'),
    ('AnimeSharpV4 2x×2', C / '2x-AnimeSharpV4_RCAN.safetensors'),
    ('FatePlus-lite (PSP)', C / '4x-FatePlus-lite.pth'),
    ('NMKD Siax', C / '4x_NMKD-Siax_200k.pth'),
    ('Remacri', C / '4x_foolhardy_Remacri.pth'),
    ('blend 50% interp_075 + 50% AnimeSharp', C / 'blend50_interp075_AnimeSharp.pth'),
    ('blend 50% interp_075 + 50% Remacri', C / 'blend50_interp075_foolhardy_Remacri.pth'),
]
# text test set: indices into compare/_contact/list.txt (en_changed_png + ui_IF/ui_LKIF), picked by eye
TEXT_IDX = [0, 2, 3, 4, 5, 8, 15, 17, 31, 32, 36, 40, 54, 58, 63, 66, 69, 76, 89, 92, 97, 102, 113, 123,
            125, 126, 146, 150]
NONTEXT_ZIP = [
    'ULJM05781/original/sorted/portraits/characters/men/0000000044ad697485384acf.png',
    'ULJM05781/original/sorted/maps/spanish/00000000a7bef2e6e33206b2.png',
    'ULJM05781/original/sorted/models/128_128/00000000909b550c88082d62.png',
    'ULJM05781/original/sorted/portraits/battle/spanish/0000000023aa28401d04517e.png',
    'ULJM05781/original/sorted/backgrounds/maps/00000000b06ead6d907ce36b.png',
    'ULJM05781/original/sorted/ui/medals/00000000d128f276c039bcbe.png',
]
# manual crops (source px x, y, w, h) on text areas; others use the auto edge-density pick
CROPS = {0: (76, 64, 64, 32), 4: (340, 140, 64, 32), 54: (110, 6, 64, 32), 125: (50, 328, 64, 32),
         66: (194, 0, 64, 32), 126: (0, 96, 64, 32), 146: (36, 0, 64, 32)}
BG = (34, 38, 48, 255)   # dark background for compositing (white text on alpha stays visible)
CROP_SRC = (64, 32)       # crop size in source pixels (-> 256x128 at 4x, shown at 2x = 512x256)
ZOOM = 2


def load_inputs():
    lst = dict(l.split('\t') for l in open(HERE / '_contact' / 'list.txt').read().splitlines())
    items = []
    for i in TEXT_IDX:
        p = lst[str(i)]
        items.append(dict(name=Path(p).stem, src=p, kind='testo', idx=i, img=Image.open(p).convert('RGBA')))
    z = zipfile.ZipFile(ZIP)
    for n in NONTEXT_ZIP:
        im = Image.open(io.BytesIO(z.read(n))).convert('RGBA')
        items.append(dict(name=Path(n).stem, src=n, kind='non-testo', img=im))
    return items


def composite(a):
    """RGBA uint8 array -> RGB over dark bg"""
    im = Image.fromarray(a, 'RGBA')
    bg = Image.new('RGBA', im.size, BG)
    return np.array(Image.alpha_composite(bg, im).convert('RGB'))


def pick_crop(src):
    """crop window (source coords) with the most edge energy: a proxy for text"""
    g = np.array(Image.fromarray(composite(src)).convert('L')).astype(np.float32)
    H, W = g.shape
    cw, ch = min(CROP_SRC[0], W), min(CROP_SRC[1], H)
    e = np.abs(np.diff(g, axis=0, prepend=g[:1])) + np.abs(np.diff(g, axis=1, prepend=g[:, :1]))
    ii = e.cumsum(0).cumsum(1)
    ii = np.pad(ii, ((1, 0), (1, 0)))
    best, bx, by = -1, 0, 0
    for y in range(0, H - ch + 1, 2):
        for x in range(0, W - cw + 1, 2):
            s = ii[y + ch, x + cw] - ii[y, x + cw] - ii[y + ch, x] + ii[y, x]
            if s > best:
                best, bx, by = s, x, y
    return bx, by, cw, ch


def metrics(src, out):
    """objective hints, on the composited image and on alpha.
    sharp: mean gradient of output / mean gradient of bicubic 4x (higher = sharper)
    halo: mean overshoot (0-255) of output beyond the 3x3 min/max of the source around each pixel
    fid: PSNR of the 4x box-downscaled output vs the source (low = the model changed content)
    """
    res = {}
    H, W = src.shape[:2]
    for ch, s, o in [('rgb', composite(src), composite(out)), ('a', src[..., 3], out[..., 3])]:
        s = s.astype(np.float32); o = o.astype(np.float32)
        if s.ndim == 2:
            s = s[..., None]; o = o[..., None]
        bic = np.stack([np.array(Image.fromarray(s[..., c].astype(np.uint8)).resize((W * 4, H * 4), Image.BICUBIC))
                        for c in range(s.shape[2])], -1).astype(np.float32)
        def grad(x):
            return (np.abs(np.diff(x, axis=0)).mean() + np.abs(np.diff(x, axis=1)).mean()) / 2
        res[f'{ch}_sharp'] = grad(o) / max(grad(bic), 1e-6)
        mx = np.stack([np.array(Image.fromarray(s[..., c].astype(np.uint8)).filter(ImageFilter.MaxFilter(3)))
                       for c in range(s.shape[2])], -1).astype(np.float32)
        mn = np.stack([np.array(Image.fromarray(s[..., c].astype(np.uint8)).filter(ImageFilter.MinFilter(3)))
                       for c in range(s.shape[2])], -1).astype(np.float32)
        mx4 = mx.repeat(4, 0).repeat(4, 1); mn4 = mn.repeat(4, 0).repeat(4, 1)
        res[f'{ch}_halo'] = float((np.maximum(o - mx4, 0) + np.maximum(mn4 - o, 0)).mean())
        down = o.reshape(H, 4, W, 4, -1).mean((1, 3))
        mse = ((down - s) ** 2).mean()
        res[f'{ch}_fid'] = 99.0 if mse == 0 else float(10 * np.log10(255 ** 2 / mse))
    return res


def run_models(items):
    times = {}
    for label, path in MODELS:
        d = HERE / 'out' / path.stem
        d.mkdir(parents=True, exist_ok=True)
        todo = [it for it in items if not (d / f"{it['name']}.png").exists()]
        if not todo:
            continue
        up = Upscaler(path, tile=512)
        t0 = time.time(); npx = 0
        for it in todo:
            up.upscale_image(it['img']).save(d / f"{it['name']}.png")
            npx += it['img'].width * it['img'].height
        if torch.cuda.is_available():
            torch.cuda.synchronize()
        times[label] = (time.time() - t0, npx)
        print(f'{label}: {len(todo)} img {time.time() - t0:.1f}s', flush=True)
        del up
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    return times


def font(sz):
    for f in ['/usr/share/fonts/TTF/DejaVuSans-Bold.ttf', '/usr/share/fonts/noto/NotoSans-Bold.ttf',
              '/usr/share/fonts/TTF/DejaVuSans.ttf']:
        if os.path.exists(f):
            return ImageFont.truetype(f, sz)
    return ImageFont.load_default()


def build_sheets(items):
    F, Fs = font(18), font(14)
    rows = []
    entries = []
    for k, it in enumerate(items):
        src = np.array(it['img'])
        x, y, cw, ch = CROPS[it['idx']] if it.get('idx') in CROPS else pick_crop(src)
        it['crop'] = (x, y, cw, ch)
        panels = []
        # source thumbnail with crop rectangle
        th = Image.fromarray(composite(src))
        sc = max(1, min(512 // th.width, 256 // th.height))
        th = th.resize((th.width * sc, th.height * sc), Image.NEAREST)
        if th.width > 512 or th.height > 256:
            f = min(512 / th.width, 256 / th.height); th = th.resize((max(1, int(th.width * f)), max(1, int(th.height * f))), Image.NEAREST)
            sc = f
        dr = ImageDraw.Draw(th); dr.rectangle([x * sc, y * sc, (x + cw) * sc - 1, (y + ch) * sc - 1], outline=(255, 0, 0), width=2)
        panels.append((f'originale {it["img"].width}x{it["img"].height} (riquadro = crop)', th))
        crop4 = (x * 4, y * 4, (x + cw) * 4, (y + ch) * 4)
        nn = Image.fromarray(composite(src)).resize((src.shape[1] * 4, src.shape[0] * 4), Image.NEAREST).crop(crop4)
        panels.append(('nearest 4x', nn))
        for label, path in MODELS:
            out = np.array(Image.open(HERE / 'out' / path.stem / f"{it['name']}.png").convert('RGBA'))
            m = metrics(src, out)
            rows.append(dict(texture=it['name'], kind=it['kind'], model=label, **{kk: round(v, 3) for kk, v in m.items()}))
            panels.append((f"{label}  sh {m['rgb_sharp']:.2f} halo {m['rgb_halo']:.1f} fid {m['rgb_fid']:.1f}",
                           Image.fromarray(composite(out)).crop(crop4)))
        # layout: 4 columns of crop panels at 2x zoom
        PW, PH = cw * 4 * ZOOM, ch * 4 * ZOOM
        PW = max(PW, 256); cols = max(1, min(4, 2048 // (PW + 8)))
        nrows = (len(panels) + cols - 1) // cols
        cellw, cellh = max(PW, 512 if cols < 4 else PW) + 8, max(PH, 256) + 30
        sheet = Image.new('RGB', (cols * cellw, nrows * cellh + 34), (20, 20, 20))
        d = ImageDraw.Draw(sheet)
        d.text((6, 6), f"{k + 1:02d} [{it['kind']}] {it['name']}  —  {it['src'].split('/out/')[-1]}", fill=(255, 255, 255), font=F)
        for j, (lab, im) in enumerate(panels):
            cx, cy = (j % cols) * cellw + 4, (j // cols) * cellh + 34
            if j >= 1:
                im = im.resize((im.width * ZOOM, im.height * ZOOM), Image.NEAREST)
            sheet.paste(im, (cx, cy + 22))
            d.text((cx, cy + 2), lab, fill=(255, 220, 90) if j >= 2 else (180, 220, 255), font=Fs)
        fn = f'sheet_{k + 1:02d}.png'
        sheet.save(HERE / fn)
        entries.append((fn, it))
        print(fn, flush=True)
    with open(HERE / 'metrics.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    return rows, entries


def summary(rows):
    out = []
    for kind in ['testo', 'non-testo']:
        for label, _ in MODELS:
            rs = [r for r in rows if r['model'] == label and r['kind'] == kind]
            out.append(dict(kind=kind, model=label, **{k: round(float(np.median([r[k] for r in rs])), 2)
                                                         for k in ['rgb_sharp', 'rgb_halo', 'rgb_fid', 'a_sharp', 'a_halo', 'a_fid']}))
    return out


def write_html(entries, summ, times):
    h = ['<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
         '<title>Confronto modelli VC3</title><style>body{background:#111;color:#ddd;font:14px sans-serif;margin:16px}'
         'img{max-width:100%;image-rendering:pixelated;border:1px solid #333}table{border-collapse:collapse;margin:8px 0}'
         'td,th{border:1px solid #444;padding:3px 8px;text-align:right}th{background:#222}td:first-child,td:nth-child(2){text-align:left}'
         'a{color:#8cf}.nav{position:sticky;top:0;background:#111;padding:6px 0;border-bottom:1px solid #333}</style></head><body>',
         '<h1>Confronto modelli 4x su texture di testo/UI (VC3)</h1>',
         '<p style="background:#223;padding:8px;border-left:4px solid #8cf"><b>Esito (visivo):</b> per testo/UI <b>Remacri</b> '
         '(con <code>--pad-mode replicate</code>) è il più fedele su font bitmap/cifre/menu; AnimeSharp secondo (meglio sul blackletter minuscolo). '
         'interp_075 inventa tratti nelle cifre piccole e vela i bianchi; DAT2/UltraSharp alterano glifi; AnimeSharpV4 è rotto (testo bianco diventa scuro). '
         'Per ritratti/mappe/modelli resta interp_075 (= stile del pack). Vedi anche <a href="alpha_check.png">alpha_check.png</a>.</p>',
         '<p>Ogni sheet: originale (riquadro rosso = zona del crop), nearest 4x, poi ogni modello. I crop sono a zoom 2× del risultato 4x, '
         'composti su fondo scuro. Alpha gestito per tutti con il trucco del 3° canale (alpha passato nel modello).</p>',
         '<p>Indicatori (mediane): <b>sharp</b> = gradiente medio rispetto a bicubic 4x (più alto = più nitido); '
         '<b>halo</b> = overshoot medio oltre min/max locale della sorgente (più alto = più ringing/aloni); '
         '<b>fid</b> = PSNR del risultato riportato a 1x contro l\'originale (basso = il modello ha cambiato il contenuto). '
         'Sono solo indizi: la scelta è visiva.</p><table><tr><th>tipo</th><th>modello</th><th>RGB sharp</th><th>RGB halo</th><th>RGB fid</th>'
         '<th>α sharp</th><th>α halo</th><th>α fid</th><th>s/Mpx sorgente</th></tr>']
    for s in summ:
        t = times.get(s['model'])
        tt = f'{t[0] / (t[1] / 1e6):.1f}' if t else ''
        h.append(f"<tr><td>{s['kind']}</td><td>{html.escape(s['model'])}</td><td>{s['rgb_sharp']}</td><td>{s['rgb_halo']}</td><td>{s['rgb_fid']}</td>"
                 f"<td>{s['a_sharp']}</td><td>{s['a_halo']}</td><td>{s['a_fid']}</td><td>{tt}</td></tr>")
    h.append('</table><div class="nav">' + ' '.join(f'<a href="#{fn}">{fn[6:8]}</a>' for fn, _ in entries) + '</div>')
    for fn, it in entries:
        h.append(f'<h3 id="{fn}">{fn} — [{it["kind"]}] {html.escape(it["name"])} ({it["img"].width}x{it["img"].height})</h3>'
                 f'<a href="{fn}"><img src="{fn}" loading="lazy" alt="{fn}"></a>')
    h.append('</body></html>')
    (HERE / 'index.html').write_text('\n'.join(h))


if __name__ == '__main__':
    items = load_inputs()
    times = {}
    tf = HERE / 'times.json'
    if '--only-sheets' not in sys.argv:
        times = run_models(items)
        if times:
            old = json.loads(tf.read_text()) if tf.exists() else {}
            old.update(times)
            tf.write_text(json.dumps(old))
    if tf.exists():
        times = json.loads(tf.read_text())
    rows, entries = build_sheets(items)
    summ = summary(rows)
    for s in summ:
        print(s)
    write_html(entries, summ, times)
