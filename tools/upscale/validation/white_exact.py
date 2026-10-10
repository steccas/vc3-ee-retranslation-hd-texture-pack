# SPDX-License-Identifier: GPL-3.0-or-later
import sys, os, io, json, zipfile, numpy as np, torch
sys.path.insert(0,'.')
from PIL import Image
from upscale import Upscaler
z=zipfile.ZipFile(os.environ.get('EFONTE_ZIP', 'ULJM05781_v20200807-001.zip'))
rows=json.load(open('validation/index.json'))
r=[r for r in rows if r['osz']==[64,128] and 'models/64_128' in r['up']][0]
a=np.array(Image.open(io.BytesIO(z.read(r['orig'])))); b=np.array(Image.open(io.BytesIO(z.read(r['up']))))
assert a[...,3].min()==255
ua=b[...,3].astype(int)
print(r['up'], 'pack alpha mode', np.bincount(ua.ravel()).argmax())
M='models/4x_fatal_Anime_500000_G_4x_FatalPixels_340000_G_interp_075.pth'
u=Upscaler(M)
t=torch.from_numpy(np.ones((3,128,64),np.float32))[None].to(u.device)
o=u._run(t)[0].cpu().numpy()*255
for name,x in [('R',o[0]),('G',o[1]),('B',o[2]),('mean',o.mean(0)),('lum',0.299*o[0]+0.587*o[1]+0.114*o[2])]:
    for rnd in ['round','floor']:
        y=np.round(x) if rnd=='round' else np.floor(x)
        print(name,rnd,'MAE',np.abs(y-ua).mean().round(3),'exact%',(y==ua).mean().round(3), 'mode',np.bincount(y.astype(int).ravel()).argmax())
print('pack row0[:20]',ua[0,:20]); print('mine G row0',np.round(o[1][0,:20]).astype(int))
print('pack center',ua[200:204,100:104]); print('mine', np.round(o[:, 200:204,100:104]).astype(int))
