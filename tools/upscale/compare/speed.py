# SPDX-License-Identifier: GPL-3.0-or-later
import sys,time,glob,numpy as np,torch
import os; sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # run from tools/upscale/
from upscale import Upscaler
import upscale
ms=['models/4x_fatal_Anime_500000_G_4x_FatalPixels_340000_G_interp_075.pth']+sorted(glob.glob('models/candidates/*.safetensors'))
for m in ms:
    try:
        u=Upscaler(m,tile=512)
        arch=type(u.model).__name__
        r=[]
        for s in [(64,64),(256,256),(256,512),(256,512),(512,512)]:
            torch.cuda.synchronize(); t0=time.time(); o=u.upscale_rgb(np.random.randint(0,255,s+(3,),np.uint8)); torch.cuda.synchronize(); r.append(round(time.time()-t0,2))
        print(f'{m.split("/")[-1]:45s} {arch:10s} scale {u.scale} passes {u.passes} out {o.shape} times {r} maxmem {torch.cuda.max_memory_allocated()/2**30:.1f}GB',flush=True)
        del u; torch.cuda.empty_cache(); torch.cuda.reset_peak_memory_stats()
    except Exception as e: print(m,'ERROR',repr(e)[:300],flush=True)
