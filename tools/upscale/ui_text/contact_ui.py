# SPDX-License-Identifier: GPL-3.0-or-later
"""Contact sheets of the uncovered UI textures for the manual text/no-text review -> work/_review/ (run from tools/upscale/).
Env: KEYS_OUT = out/ folder of tools/keys/run_all.sh; FONT = TTF font for labels."""
import glob,os
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
R=os.environ.get('KEYS_OUT', str(Path(__file__).resolve().parents[2] / 'keys' / 'work' / 'out')).rstrip('/')+'/uncovered_png/'
os.makedirs('work/_review', exist_ok=True)
cats=['ui_IF','ui_LKIF','odif_ui','other_BALLOON','events_EV','battle_abr']
files=[f for c in cats for f in sorted(glob.glob(R+c+'/*.png'))]
open('work/_review/list.txt','w').write('\n'.join(f'{i}\t{f}' for i,f in enumerate(files)))
try: F=ImageFont.truetype(os.environ.get('FONT','DejaVuSans-Bold.ttf'),14)
except OSError: F=ImageFont.load_default()
TW,TH=310,200; cols=5; per=25
def thumb(f):
    im=Image.open(f).convert('RGBA'); bg=Image.new('RGBA',im.size,(70,70,90,255)); im=Image.alpha_composite(bg,im).convert('RGB')
    k=min((TW-6)/im.width,(TH-22)/im.height)
    if k>=1: k=int(k); im=im.resize((im.width*k,im.height*k),Image.NEAREST)
    else: im=im.resize((max(1,int(im.width*k)),max(1,int(im.height*k))),Image.LANCZOS)
    return im
for s in range(0,len(files),per):
    sh=Image.new('RGB',(cols*TW,(per//cols)*TH),(25,25,25)); d=ImageDraw.Draw(sh)
    for j,f in enumerate(files[s:s+per]):
        x,y=(j%cols)*TW,(j//cols)*TH; sh.paste(thumb(f),(x+3,y+20))
        d.text((x+3,y+2),f'{s+j} {f.split("/")[-2]} {Image.open(f).size}',fill=(255,255,0),font=F)
    sh.save(f'work/_review/r{s//per:02d}.png')
print(len(files))
