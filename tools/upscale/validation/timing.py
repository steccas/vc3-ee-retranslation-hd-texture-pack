# SPDX-License-Identifier: GPL-3.0-or-later
import sys,time,numpy as np,torch
import os; sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from upscale import Upscaler
u=Upscaler()
for s in [(64,64),(64,64),(128,64),(128,64),(256,256),(256,256),(512,512)]:
    t0=time.time(); u.upscale_rgb(np.zeros(s+(3,),np.uint8)); torch.cuda.synchronize(); print(s,round(time.time()-t0,2),flush=True)
