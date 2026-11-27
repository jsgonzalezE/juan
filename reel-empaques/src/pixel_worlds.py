"""Idea G (el viaje por los mundos): cada empaque es un mundo hecho con su propio dibujo.

Noah recorre los cuatro mundos; las transiciones cambian (capuchino, portal de cafe...).
Termina en la tostadora con el primer "crack" y despues el logo.
Uso: python3 src/pixel_worlds.py PAQUETE_DIR -> storyboards/frames/g_XX.png + frames_g.json
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pixelkit import *

PK = sys.argv[1]
LW, LH, P = 180, 320, 6
TOP = 96                                   # donde empieza el mundo; arriba queda negro para el texto
B = Board('g')

WORLDS = [
    dict(name='JAVA', n='01', line='(cherry season.)', src='03_acuarelas/acuarela_cerezas.jpg', box=(0, 190, 1135, 1600),
         noah='host', s=0.40, x=58, y=288, flip=False,
         es='El mundo de Java sale de la acuarela de las cerezas: los cafetales, las hojas y los racimos rojos en primer plano. Noah lo cruza caminando, contento. Las hojas se mecen y cae alguna cereza.'),
    dict(name='CASTILLO', n='02', line='(la fiesta.)', src='02_empaques/empaque_colores_CASTILLO.png', box=(28, 282, 460, 822),
         noah='listen', s=0.46, x=50, y=290, flip=False,
         es='El mundo de Castillo sale del empaque de colores: la fiesta, los bailarines, los músicos y las flores. Todo rebota al ritmo. Noah levanta la oreja: lo oye.'),
    dict(name='GEISHA', n='03', line='(up in the clouds.)', src='03_acuarelas/acuarela_mula_casa_azul.jpg', box=(0, 250, 1088, 1600),
         noah='mug', s=0.38, x=50, y=296, flip=False,
         es='El mundo de Geisha sale de la acuarela de la casa azul: montañas con neblina, el camino, el arriero y la mula. La neblina se mueve despacio. Noah, feliz con su taza.'),
    dict(name='BOURBON', n='04', line="(...who's that dog?)", src='03_acuarelas/acuarela_mula_perro_casa_roja.jpg', box=(0, 0, 1080, 1350),
         noah='sideeye', s=0.40, x=136, y=300, flip=True,
         es='El mundo de Bourbon sale de la acuarela de la casa roja: el balcón, el árbol, el camino... y el perro pintado. Noah lo ve y lo mira de reojo.'),
]
ENTRA = ['Entra por el capuchino: Noah salta del borde a la espuma.',
         'Entra por un portal de café: un remolino que se lo traga.',
         'Entra con una marea de café que sube, tapa todo y al bajar ya es otro mundo.',
         'Entra por la puerta azul de la casa del mundo anterior.']


def world_art(w):
    """El dibujo del empaque, en pixel art, como paisaje del mundo (180 x 224)."""
    im = Image.open(os.path.join(PK, w['src'])).convert('RGB').crop(w['box'])
    im = ImageEnhance.Color(im).enhance(1.25)
    im = ImageEnhance.Contrast(im).enhance(1.08)
    W, H = LW, LH - TOP
    s = im.resize((W * 3, H * 3), Image.LANCZOS).filter(ImageFilter.UnsharpMask(2, 90, 2)).resize((W, H), Image.BOX)
    return s.quantize(colors=44, method=Image.MEDIANCUT, dither=Image.NONE, kmeans=3).convert('RGB')


def world_scene(w):
    img = Image.new('RGBA', (LW, LH), BLACK + (255,))
    img.paste(world_art(w), (0, TOP))
    a = np.asarray(img).copy()
    yy, xx = np.mgrid[0:LH, 0:LW]
    fade = (yy >= TOP) & (B8[yy % 8, xx % 8] > (yy - TOP) / 40.0)       # el negro se deshace en puntos hacia el paisaje
    a[fade, :3] = BLACK
    return Image.fromarray(a, 'RGBA')


def ground_shadow(img, cx, y, w):
    d = ImageDraw.Draw(img)
    for dy in range(4):
        for x in range(cx - w // 2 + dy * 2, cx + w // 2 - dy * 2):
            if (x + y + dy) % 2 == 0:
                d.point((x, y + dy), fill=(28, 22, 18))


# ---------- 1 · abre: el capuchino visto desde arriba, Noah camina por el borde ----------
img = Image.new('RGBA', (LW, LH), BLACK + (255,))
text(img, (90, 58), 'FOUR NEW VARIETIES', F_M, CREAM, 'ma')
text(img, (90, 80), '(follow Noah.)', F_S, SOFT, 'ma')
d = ImageDraw.Draw(img)
cx, cy, rx, ry = 82, 196, 76, 52
d.ellipse([cx + rx - 8, cy - 14, cx + rx + 22, cy + 22], fill=(250, 242, 226))                # asa
d.ellipse([cx + rx - 2, cy - 7, cx + rx + 14, cy + 15], fill=BLACK)
d.ellipse([cx - rx, cy - ry + 10, cx + rx, cy + ry + 26], fill=(34, 26, 21))              # cuerpo oscuro de la taza
d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=(250, 242, 226))                      # borde claro
d.ellipse([cx - rx + 7, cy - ry + 6, cx + rx - 7, cy + ry - 5], fill=(196, 150, 100))      # crema
a = np.asarray(img).copy()
yy, xx = np.mgrid[0:LH, 0:LW]
ex, ey = (xx - cx) / (rx - 12.0), (yy - (cy + 1)) / (ry - 11.0)
rr = np.sqrt(ex ** 2 + ey ** 2)
th = np.arctan2(ey, ex)
foam = rr < 1
swirl = np.mod(th / (2 * np.pi) + 1.15 * rr, 1.0)                                           # remolino de latte art
light = (swirl < 0.55)
a[foam & light, :3] = (238, 220, 190)
a[foam & ~light, :3] = (168, 112, 66)
edge = foam & (np.abs(swirl - 0.55) < 0.06) & (B8[yy % 8, xx % 8] > 0.5)
a[edge, :3] = (206, 166, 122)
img = Image.fromarray(a, 'RGBA')
c = up(img, P)
noah(c, 'host', 0.25, 80 * P, (cy + ry - 2) * P)
B.save(c, '0 – 2 s', 'Abre: el capuchino', 'Fondo negro y un capuchino visto desde arriba. Noah camina por el borde de la taza, que aquí va al revés: como una sonrisa. La espuma gira despacio.',
       'FOUR NEW VARIETIES · (follow Noah.)', 'Cucharita contra la loza. Pasitos.')

# ---------- 2 · mundo Java ----------
def world_frame(i):
    w = WORLDS[i]
    img = world_scene(w)
    text(img, (13, 34), f"{w['n']} / 04", F_S, CREAM)
    text(img, (12, 44), w['name'], fit_title(w['name'], 156, 30), CREAM)
    text(img, (13, 80), w['line'], F_M if F_M.getlength(w['line']) <= 160 else F_S, CREAM)
    ground_shadow(img, w['x'], w['y'] - 1, 44)
    c = up(img, P)
    noah(c, w['noah'], w['s'], w['x'] * P, w['y'] * P + 6, flip=w['flip'])
    return c


times = ['2 – 5,5 s', '5,5 – 8,5 s', '8,5 – 11,5 s', '11,5 – 14,5 s']
B.save(world_frame(0), times[0], 'Mundo 1: Java', WORLDS[0]['es'] + ' ' + ENTRA[0], '01 / 04 · JAVA · (cherry season.)', 'Pájaros, hojas. Nota al llegar.')

# ---------- 3 · transicion: portal de cafe ----------
img = Image.new('RGBA', (LW, LH), BLACK + (255,))
a = np.asarray(img).copy()
px_, py_ = 90, 176
dx, dy = xx - px_, (yy - py_) * 0.92
r = np.sqrt(dx ** 2 + dy ** 2)
th = np.arctan2(dy, dx)
v = np.mod(th / (2 * np.pi) * 2 + 0.55 * np.log(r + 3), 1.0)
ring = r < 96
tone = np.where(v > B8[yy % 8, xx % 8] * 0.9 + 0.05, 1, 0)
a[ring & (tone == 1), :3] = (58, 32, 18)
a[ring & (tone == 0), :3] = (196, 150, 100)
a[ring & (np.abs(v - 0.5) < 0.05), :3] = (236, 214, 180)
rimfade = ring & (r > 80) & (B8[yy % 8, xx % 8] < (r - 80) / 16.0)
a[rimfade, :3] = BLACK
core = r < 30                                                                               # al fondo ya se ve el mundo que sigue
mag, ora = np.array((150, 30, 86)), np.array((234, 124, 30))
a[core, :3] = np.where((r[core] / 30.0 > B8[yy % 8, xx % 8][core])[:, None], mag, ora)
img = Image.fromarray(a, 'RGBA')
c = up(img, P)
nz = Image.open(os.path.join(A, 'sprites', 'noah_host.png')).convert('RGBA')
nz = nz.resize((round(nz.width * 0.16), round(nz.height * 0.16)), Image.LANCZOS).rotate(24, expand=True, resample=Image.BICUBIC)
c.alpha_composite(nz, (118 * P, 196 * P))
B.save(c, '5,5 s', 'Transición: portal de café', 'Para pasar al siguiente mundo se abre un remolino de café con crema. Al fondo ya se ve el color del mundo que viene. Noah cae girando hacia el centro.',
       '(sin texto)', 'Remolino, succión, "pop".')

B.save(world_frame(1), times[1], 'Mundo 2: Castillo', WORLDS[1]['es'] + ' ' + ENTRA[1], '02 / 04 · CASTILLO · (la fiesta.)', 'Guitarra y palmas. Nota al llegar.')
B.save(world_frame(2), times[2], 'Mundo 3: Geisha', WORLDS[2]['es'] + ' ' + ENTRA[2], '03 / 04 · GEISHA · (up in the clouds.)', 'Viento suave, cascos lejanos. Nota al llegar.')
B.save(world_frame(3), times[3], 'Mundo 4: Bourbon', WORLDS[3]['es'] + ' ' + ENTRA[3], "04 / 04 · BOURBON · (...who's that dog?)", 'Un ladrido chiquito. Nota al llegar.')

# ---------- 8 · final: la tostadora y el primer crack ----------
img = Image.new('RGBA', (LW, LH), BLACK + (255,))
t = yy / LH + 0.010 * np.sin(xx / LW * 2 * np.pi * 0.9 + 0.6)
c1, c2 = (104, 58, 22), (226, 160, 70)
ramp = [BLACK, mixc(BLACK, c1, .5), c1, mixc(c1, c2, .5), c2, mixc(c2, (246, 228, 196), .5)]
sk = dither_ramp(t, ramp, 0.42, 0.80)
a = np.asarray(img).copy(); a[..., :3] = sk
a[yy >= 258, :3] = (24, 16, 11)
img = Image.fromarray(a, 'RGBA')
ImageDraw.Draw(img).line([(0, 258), (LW, 258)], fill=(196, 150, 100))
text(img, (90, 62), '(first crack!)', F_M, CREAM, 'ma')
text(img, (90, 86), 'this one is almost ready.', F_S, CREAM, 'ma')
for (qx, qy, qr) in [(116, 168, 7), (126, 150, 5), (110, 152, 4), (132, 134, 3)]:
    dd = ImageDraw.Draw(img)
    for y in range(qy - qr, qy + qr + 1):
        for x in range(qx - qr, qx + qr + 1):
            q = ((x - qx) ** 2 + (y - qy) ** 2) / (qr * qr + 0.1)
            if q <= 1 and B8[y % 8, x % 8] > q * 0.8:
                dd.point((x, y), fill=(236, 222, 200))
for (mk, mw, mx, my) in [(53, 9, 130, 176), (56, 8, 100, 170), (25, 9, 140, 156)]:
    img.alpha_composite(motif(mk, mw), (mx, my))
c = up(img, P)
noah(c, 'roaster', 0.50, 86 * P, 258 * P + 8)
B.save(c, '14,5 – 17 s', 'Final: el primer crack', 'Noah llega a la tostadora y se sienta. Suena el primer "crack": levanta la oreja de golpe, saltan los granos y sale humo. Avisa que este café ya casi está listo.',
       '(first crack!) · this one is almost ready.', 'Tambor girando y un "crack" seco.')

# ---------- 9-10 · el logo: de pixel art a normal ----------
LOGO = Image.open(os.path.join(A, 'logo_blanco.png')).convert('RGBA')
h62 = round(LOGO.height * 62 / LOGO.width)
on = np.asarray(LOGO.split()[3].resize((62, h62), Image.BOX)) >= 92
lg = np.zeros((h62, 62, 4), np.uint8); lg[on] = CREAM + (255,)
img = Image.new('RGBA', (LW, LH), BLACK + (255,))
img.alpha_composite(Image.fromarray(lg, 'RGBA'), (90 - 31, 96))
B.save(up(img, P), '17 – 18,5 s', 'Solo el logo, en pixel art', 'Los granos suben, se vuelven pixeles y arman el logo de Juanito. Fondo negro, sin empaques y sin Noah.',
       '(logo en pixel art)', 'Último pixel que encaja: un "clic".')

c = Image.new('RGBA', (LW * P, LH * P), BLACK + (255,))
lw = 62 * P
logo = LOGO.resize((lw, round(LOGO.height * lw / LOGO.width)), Image.LANCZOS)
c.alpha_composite(logo, (540 - lw // 2, 96 * P))
f = font('montserrat', 'montserrat-latin-300-normal.woff', 40)
s_, track = 'COMING SOON', 20
ws = [f.getlength(ch) for ch in s_]
x = 540 - (sum(ws) + track * (len(s_) - 1)) / 2
dd = ImageDraw.Draw(c)
for ch, wch in zip(s_, ws):
    dd.text((x, 96 * P + logo.height + 70), ch, font=f, fill=CREAM); x += wch + track
B.save(c, '18,5 – 20 s', 'El logo pasa a normal', 'Los pixeles se afinan hasta volverse el logo normal. Debajo, "coming soon" en letra fina.',
       'COMING SOON', 'Nota limpia que se apaga.')
B.close()
