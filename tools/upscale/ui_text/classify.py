# SPDX-License-Identifier: GPL-3.0-or-later
"""Manual classification of UI textures into "has text" (upscaled with Remacri) or not.

The YES / NOTE_NO dicts are the record of a visual review of the contact sheets work/_review/rNN.png
produced by contact_ui.py (indices refer to work/_review/list.txt). Notes are in Italian.
Output: work/ui_text_select.csv + work/ui_text_yes.png / ui_text_no.png. Run from tools/upscale/.
Env: FONT = path to a TTF font for labels (default: DejaVuSans-Bold if found, else PIL default font).
"""
import os
import csv
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
W = Path('work')
L = [l.split('\t') for l in (W / '_review/list.txt').read_text().splitlines()]
YES = {1: 'JP: istruzione', 3: 'EXP/DC + SELECT', 4: 'JP: istruzione', 7: 'LEVEL UP CLASS', 10: 'cifre 1-5 + icone',
       21: 'JP rosso', 22: 'data + STORY + JP', 23: 'pezzi UI con etichette piccole', 40: 'data + JP', 48: 'capitolo + EXP/DCT piccoli',
       54: 'JP: istruzione', 55: 'EXP/DCT/New/VS/Story/Free/Key', 56: 'UI con Lv/Record/Grade/JP', 57: 'JP classi + HP',
       58: 'LEVEL UP CLASS', 61: 'Hp/SP/Lv.DCT + icone', 63: 'JP classi + cifre + Next Lv.', 65: 'FAILED', 69: 'SUCCESS',
       72: 'JP: paragrafo', 82: 'STORY + JP + Rank', 83: 'mesi EN + JP', 86: 'Congratulations!', 91: 'Level up!!',
       96: 'JP + SELECT piccoli', 97: 'cifre 1-12 + Max/Lv. + icone', 102: 'List of Troop Training (pergamena)',
       104: 'INFOMATION', 112: 'DETAIL / Status Value Change (piccolo)', 122: 'ORDER + paragrafo + firma',
       140: 'ORDER + paragrafo + firma', 143: 'ORDER + paragrafo + firma', 158: 'misto: capelli + lettere RIA',
       164: 'LEVEL UP pezzi', 165: 'ORDER + paragrafo + firma', 187: 'ORDER + paragrafo + firma', 211: 'OPEN FIRE',
       229: 'pergamena con Rank/MISSION piccoli', 240: 'ORDER + paragrafo + firma', 241: 'JP 通信中',
       243: 'misto: schizzo + VALKYRIA', 253: 'ORDER + paragrafo + firma', 265: 'VALKYRIA', 266: 'misto: logo titolo JP + Press START',
       292: 'VALKYRIA', 307: 'misto: tratti + VLKY', 320: 'misto: capelli + VALKYRIA', 346: 'onomatopea katakana',
       348: 'onomatopea katakana'}
NOTE_NO = {2: 'foto (scritta PHOTO minima)', 11: 'mappa con nomi minuscoli', 46: 'mappa con nomi minuscoli',
           26: 'documento illeggibile', 33: "icone (solo 'Lv.' piccolo)", 149: 'cornice, intestazione NAMELESS minuscola',
           286: 'pergamena, intestazione NAMELESS minuscola', 297: 'pergamena, intestazione NAMELESS minuscola',
           173: 'ritratto con targhetta numero piccola', 193: 'busta con timbro illeggibile', 336: 'screenshot evento (UI piccola)',
           340: 'screenshot evento (onomatopea piccola)', 126: 'piante edifici', 127: 'piante edifici', 141: 'piante edifici',
           200: 'piante edifici', 220: 'piante edifici', 62: 'barre/stelle'}
for i in (35, 38, 44, 47, 66, 67, 88, 89, 95, 101, 106, 113):
    NOTE_NO[i] = 'misto: ritratto con numero grande in angolo (lasciato allo stile ritratti)'
rows = []
for i, p in L:
    i = int(i); p = Path(p)
    yes = i in YES
    rows.append(dict(key=p.stem, category=p.parent.name, png=str(p), decision='testo' if yes else 'no',
                     note=YES.get(i) if yes else NOTE_NO.get(i, ''), idx=i))
with open(W / 'ui_text_select.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['key', 'category', 'png', 'decision', 'note']); w.writeheader()
    w.writerows({k: r[k] for k in ['key', 'category', 'png', 'decision', 'note']} for r in rows)
def _font(size):
    try:
        return ImageFont.truetype(os.environ.get('FONT', 'DejaVuSans-Bold.ttf'), size)
    except OSError:
        return ImageFont.load_default()
F = _font(12)
TW, TH, cols = 260, 170, 8
def sheet(sel, out):
    n = (len(sel) + cols - 1) // cols
    sh = Image.new('RGB', (cols * TW, n * TH), (25, 25, 25)); d = ImageDraw.Draw(sh)
    for j, r in enumerate(sel):
        im = Image.open(r['png']).convert('RGBA'); bg = Image.new('RGBA', im.size, (70, 70, 90, 255))
        im = Image.alpha_composite(bg, im).convert('RGB')
        k = min((TW - 6) / im.width, (TH - 36) / im.height)
        im = im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.NEAREST if k >= 1 else Image.LANCZOS)
        x, y = (j % cols) * TW, (j // cols) * TH
        sh.paste(im, (x + 3, y + 32))
        d.text((x + 3, y + 2), f"{r['category']} {r['key'][-12:]}", fill=(255, 255, 0), font=F)
        d.text((x + 3, y + 16), (r['note'] or '')[:36], fill=(150, 220, 255), font=F)
    sh.save(out)
sheet([r for r in rows if r['decision'] == 'testo'], W / 'ui_text_yes.png')
sheet([r for r in rows if r['decision'] == 'no'], W / 'ui_text_no.png')
print('testo', sum(r['decision'] == 'testo' for r in rows), 'no', sum(r['decision'] == 'no' for r in rows))
