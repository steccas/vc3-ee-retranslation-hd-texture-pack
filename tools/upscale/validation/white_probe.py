# SPDX-License-Identifier: GPL-3.0-or-later
import sys, numpy as np, torch
sys.path.insert(0,'.')
from upscale import Upscaler
M='models/'
models={'anime':M+'4x_fatal_Anime_500000_G.pth','pixels':M+'4x_FatalPixels_340000_G.pth',
 'i075(.25A+.75P)':M+'4x_fatal_Anime_500000_G_4x_FatalPixels_340000_G_interp_075.pth',
 'i025(.75A+.25P)':M+'4x_fatal_Anime_500000_G_4x_FatalPixels_340000_G_interp_025.pth',
 'i050':M+'4x_fatal_Anime_500000_G_4x_FatalPixels_340000_G_interp_050.pth'}
w=np.full((64,64),255,np.uint8)
print('pack target (64x128 opaque): min 233 mean ~243.84 mode 244, border mean 239.7')
for k,p in models.items():
    for pm in ['none','reflect','replicate']:
        u=Upscaler(p,pad_mode=pm,pad=8)
        a=u.upscale_alpha(w,(256,256))
        h=np.bincount(a.ravel(),minlength=256)
        print(f'{k:18s} {pm:9s} min {a.min()} mean {a.mean():.2f} mode {h.argmax()} border {np.r_[a[0],a[-1],a[:,0],a[:,-1]].mean():.1f}')
