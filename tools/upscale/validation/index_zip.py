# SPDX-License-Identifier: GPL-3.0-or-later
import zipfile, io, json, collections, sys, os
from PIL import Image
Z=os.environ.get('EFONTE_ZIP', 'ULJM05781_v20200807-001.zip')
z=zipfile.ZipFile(Z)
orig={}; up={}
for n in z.namelist():
    if not n.endswith('.png'): continue
    p=n.split('/')
    fn=p[-1]
    if n.startswith('ULJM05781/original/sorted/'): orig.setdefault(fn,n)
    elif n.startswith('ULJM05781/ai_upscaled/'): up.setdefault(fn,n)
both=sorted(set(orig)&set(up))
print('orig',len(orig),'up',len(up),'both',len(both))
rows=[]
for fn in both:
    a=Image.open(io.BytesIO(z.read(orig[fn]))); b=Image.open(io.BytesIO(z.read(up[fn])))
    rows.append(dict(fn=fn,orig=orig[fn],up=up[fn],osz=a.size,usz=b.size,omode=a.mode,umode=b.mode))
json.dump(rows,open('validation/index.json','w'))
c=collections.Counter((r['usz'][0]==4*r['osz'][0] and r['usz'][1]==4*r['osz'][1], r['omode'], r['umode']) for r in rows)
for k,v in c.most_common(): print(k,v)
c=collections.Counter('/'.join(r['up'].split('/')[2:4]) for r in rows)
print(c.most_common(40))
