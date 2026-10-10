# SPDX-License-Identifier: GPL-3.0-or-later
"""Contact sheets of the text/UI candidates -> compare/_contact/ (run from tools/upscale/)."""
import glob,os
from pathlib import Path
from PIL import Image,ImageDraw
R=os.environ.get('KEYS_OUT', str(Path(__file__).resolve().parents[2] / 'keys' / 'work' / 'out')).rstrip('/')+'/'
os.makedirs('compare/_contact', exist_ok=True)
files=sorted(glob.glob(R+'en_changed_png/*.png'))+sorted(glob.glob(R+'uncovered_png/ui_IF/*.png'))+sorted(glob.glob(R+'uncovered_png/ui_LKIF/*.png'))
open('compare/_contact/list.txt','w').write('\n'.join(f'{i}\t{f}' for i,f in enumerate(files)))
TW,TH=256,140; per=40; cols=5
for s in range(0,len(files),per):
    sheet=Image.new('RGB',(cols*TW,(per//cols)*TH),(60,60,60)); d=ImageDraw.Draw(sheet)
    for j,f in enumerate(files[s:s+per]):
        im=Image.open(f).convert('RGBA'); bg=Image.new('RGBA',im.size,(110,110,110,255)); im=Image.alpha_composite(bg,im)
        im.thumbnail((TW-4,TH-16),Image.NEAREST if im.width<TW else Image.LANCZOS)
        if im.width<TW/2 and im.height<(TH-16)/2:
            k=min((TW-4)//im.width,(TH-16)//im.height); im=im.resize((im.width*k,im.height*k),Image.NEAREST)
        x,y=(j%cols)*TW,(j//cols)*TH
        sheet.paste(im.convert('RGB'),(x+2,y+14)); d.text((x+2,y+1),f'{s+j} {os.path.basename(os.path.dirname(f))[:10]} {Image.open(f).size}',fill=(255,255,0))
    sheet.save(f'compare/_contact/c{s//per:02d}.png')
print(len(files))
