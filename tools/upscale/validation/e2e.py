# SPDX-License-Identifier: GPL-3.0-or-later
"""End-to-end check of the CLI: extract a few originals, run upscale.py, compare to the pack."""
import io, json, os, random, subprocess, sys, zipfile
from pathlib import Path
import numpy as np
from PIL import Image
H = Path(__file__).resolve().parent
z = zipfile.ZipFile(os.environ.get('EFONTE_ZIP', 'ULJM05781_v20200807-001.zip'))
rows = json.load(open(H / 'index.json'))
random.seed(7)
pick = [r for r in rows if '/ui/' in r['up']][:0] + random.sample(rows, 10)
inp, out = H / 'e2e' / 'in', H / 'e2e' / 'out'
inp.mkdir(parents=True, exist_ok=True)
for r in pick:
    (inp / r['fn']).write_bytes(z.read(r['orig']))
dev = sys.argv[1] if len(sys.argv) > 1 else 'auto'
subprocess.run([sys.executable, str(H.parent / 'upscale.py'), str(inp), str(out), '--device', dev], check=True)
ok = 0
for r in pick:
    a = np.array(Image.open(out / r['fn'])); b = np.array(Image.open(io.BytesIO(z.read(r['up']))))
    ex = (a == b).mean(); ok += ex > 0.999
    print(f"{r['up'].split('/', 2)[2]:70s} {r['osz']} exact={ex:.5f} maxdiff={np.abs(a.astype(int) - b).max()}")
print(f'{ok}/{len(pick)} match')
