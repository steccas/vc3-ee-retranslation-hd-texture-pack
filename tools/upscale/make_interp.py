#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Build IEU-style interpolated models: out = (1-alpha)*A + alpha*B
(same formula as IEU.Core Scripts/interpModels.py).

Usage: python make_interp.py [--a MODEL_A] [--b MODEL_B] [--out-dir DIR]
Defaults: models/4x_fatal_Anime_500000_G.pth and models/4x_FatalPixels_340000_G.pth (next to this script).
Check the results against models/SHA256SUMS.
"""
import argparse
from collections import OrderedDict
from pathlib import Path
import torch

HERE = Path(__file__).resolve().parent
ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument('--a', default=str(HERE / 'models' / '4x_fatal_Anime_500000_G.pth'))
ap.add_argument('--b', default=str(HERE / 'models' / '4x_FatalPixels_340000_G.pth'))
ap.add_argument('--out-dir', default=str(HERE / 'models'))
args = ap.parse_args()
a = torch.load(args.a, map_location='cpu', weights_only=True); b = torch.load(args.b, map_location='cpu', weights_only=True)
assert a.keys() == b.keys()
for alpha, tag in [(0.75, 'interp_075'), (0.25, 'interp_025'), (0.5, 'interp_050')]:
    out = OrderedDict((k, (1 - alpha) * a[k] + alpha * b[k]) for k in a)
    torch.save(out, str(Path(args.out_dir) / f'4x_fatal_Anime_500000_G_4x_FatalPixels_340000_G_{tag}.pth'))
    print(tag, '= %.2f*Anime + %.2f*Pixels' % (1 - alpha, alpha))
