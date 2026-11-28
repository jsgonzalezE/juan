"""Tira de vista previa de una idea: python3 strip.py a|b|c OUT.png [ancho]"""
import sys, glob
from PIL import Image
idea, out = sys.argv[1], sys.argv[2]
w = int(sys.argv[3]) if len(sys.argv) > 3 else 360
h = w * 16 // 9
fs = sorted(glob.glob(f'storyboards/frames/{idea}_*.png'))
sheet = Image.new('RGB', (len(fs) * (w + 8) - 8, h), (70, 70, 70))
for i, f in enumerate(fs):
    sheet.paste(Image.open(f).convert('RGB').resize((w, h), Image.LANCZOS), (i * (w + 8), 0))
sheet.save(out)
