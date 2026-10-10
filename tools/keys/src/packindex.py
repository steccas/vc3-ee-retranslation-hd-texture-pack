# SPDX-License-Identifier: GPL-3.0-or-later
"""Index every PNG under pack/original by a hash of its RGBA pixels (+ size)."""
import os, sys, pickle, hashlib, numpy as np
from PIL import Image
from concurrent.futures import ProcessPoolExecutor
def one(p):
    try:
        im = np.asarray(Image.open(p).convert('RGBA'))
        return p, im.shape[1], im.shape[0], hashlib.md5(im.tobytes()).hexdigest(), hashlib.md5(im[:, :, :3].tobytes()).hexdigest()
    except Exception as e:
        return p, 0, 0, None, None
if __name__ == '__main__':
    root = sys.argv[1]
    paths = [os.path.join(d, f) for d, _, fs in os.walk(os.path.join(root, 'original')) for f in fs if f.endswith('.png')]
    with ProcessPoolExecutor() as ex:
        res = list(ex.map(one, paths, chunksize=64))
    pickle.dump(res, open(sys.argv[2], 'wb')); print(len(res))
