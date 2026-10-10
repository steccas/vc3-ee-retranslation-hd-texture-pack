# SPDX-License-Identifier: GPL-3.0-or-later
import zipfile, io, json, os, random, numpy as np
from PIL import Image
z=zipfile.ZipFile(os.environ.get('EFONTE_ZIP', 'ULJM05781_v20200807-001.zip'))
rows=json.load(open('validation/index.json'))
random.seed(1); random.shuffle(rows)
stats={'opaque_orig':0,'opaque_orig_up_not':0,'alpha':0}
shown=0
for r in rows[:400]:
    a=np.array(Image.open(io.BytesIO(z.read(r['orig']))).convert('RGBA')); b=np.array(Image.open(io.BytesIO(z.read(r['up']))).convert('RGBA'))
    oa=a[...,3]; ua=b[...,3]
    if oa.min()==255:
        stats['opaque_orig']+=1
        if ua.min()<255: stats['opaque_orig_up_not']+=1
        continue
    stats['alpha']+=1
    if shown<14:
        shown+=1
        o=Image.fromarray(oa); W,H=o.size
        res={}
        for name,m in [('nearest',Image.NEAREST),('bilinear',Image.BILINEAR),('bicubic',Image.BICUBIC),('lanczos',Image.LANCZOS)]:
            x=np.array(o.resize((4*W,4*H),m)).astype(float); res[name]=round(np.abs(x-ua).mean(),2)
        print(r['up'].split('/',2)[2], a.shape[:2], 'orig uniq',len(np.unique(oa)),'up uniq',len(np.unique(ua)), 'MAE',res,
              'transp px RGB up mean', b[ua==0][:,:3].mean(0).round(1) if (ua==0).any() else '-')
print(stats)
