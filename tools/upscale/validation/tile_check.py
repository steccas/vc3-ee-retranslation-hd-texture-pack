# SPDX-License-Identifier: GPL-3.0-or-later
import sys,os,io,json,zipfile,numpy as np
sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PIL import Image
from upscale import Upscaler
z=zipfile.ZipFile(os.environ.get('EFONTE_ZIP', 'ULJM05781_v20200807-001.zip'))
r=[r for r in json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'index.json'))) if r['osz']==[512,512] and '/portraits/' in r['up']][0]
a=np.array(Image.open(io.BytesIO(z.read(r['orig']))).convert('RGBA')); b=np.array(Image.open(io.BytesIO(z.read(r['up']))))
def psnr(x,y): m=((x.astype(float)-y)**2).mean(); return 99 if m==0 else 10*np.log10(255**2/m)
for tile,ov in [(0,0),(512,32),(256,32),(256,16),(128,16)]:
    u=Upscaler(tile=tile,tile_overlap=ov); o=np.array(u.upscale_image(Image.fromarray(a)))
    print(r['up'].split('/',2)[2],'tile',tile,'ov',ov,'PSNR vs pack RGB %.2f A %.2f'%(psnr(o[...,:3],b[...,:3]),psnr(o[...,3],b[...,3])))
