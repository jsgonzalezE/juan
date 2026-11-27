"""Idea F afinada (el horizonte de cafe): Noah camina sobre la curva de una taza de cafe.

Version afinada: Noah mas grande y al frente, el empaque sube por detras del horizonte como un sol,
mas cielo y menos loma, el cafe refleja el color de cada variedad, y el ambiente entra por los bordes.
Uso: python3 src/pixel_cup.py -> storyboards/frames/f_XX.png + frames_f.json
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pixelkit import *

LW, LH, P, R, H0 = 180, 320, 6, 300, 212
GLOW = (246, 228, 196)
yy, xx = np.mgrid[0:LH, 0:LW]
BAY = B8[yy % 8, xx % 8]
XC = (LW - 1) / 2
B = Board('f')


def ydome(x): return H0 + R - np.sqrt(R * R - (np.asarray(x, float) - XC) ** 2)


def sky(c1, c2, glow=GLOW, mist=True):
    t = yy / LH + 0.010 * np.sin(xx / LW * 2 * np.pi * 0.9 + 0.6)
    ramp = [BLACK, mixc(BLACK, c1, .5), c1, mixc(c1, c2, .5), c2, mixc(c2, glow, .6), glow]
    rgb = dither_ramp(t, ramp, 0.37, H0 / LH + 0.02)
    if mist:                                                # dos capas de neblina: dan profundidad
        for yc, amp, k in [(H0 - 22, 3.0, 0.55), (H0 - 46, 4.0, 0.35)]:
            edge = yc + amp * np.sin(xx / 13.0 + yc)
            band = (yy > edge) & (yy < edge + 9)
            dens = np.clip(1 - np.abs(yy - edge - 4.5) / 4.5, 0, 1) * k
            rgb[band & (dens > BAY)] = mixc(c2, glow, .72)
    return Image.fromarray(rgb, 'RGB').convert('RGBA')


def coffee(c1, c2, lit=True):
    """La superficie del cafe: curva oscura con borde de crema; refleja el color del cielo."""
    depth = yy - ydome(xx)
    base = mixc((46, 26, 15), c1, 0.14) if lit else (26, 20, 17)
    dark = (20, 11, 7) if lit else (14, 12, 11)
    out = np.zeros((LH, LW, 4), np.uint8)
    k = np.clip(depth / (LH - H0), 0, 1)
    out[..., :3] = np.where((k * 1.1 > BAY)[..., None], dark, base)
    streak = (depth >= 5) & (depth < 22) & (B8[yy % 8, (xx + yy // 3) % 8] < 0.09) & ((yy // 2) % 3 == 0)
    out[streak, :3] = (96, 58, 30) if lit else (44, 36, 30)
    if lit:
        sheen = (depth >= 3) & (depth < 18) & (yy % 2 == 0) & ((1 - (depth - 3) / 15.0) * 0.5 > BAY)
        out[sheen, :3] = mixc(c2, base, 0.62)
    out[(depth >= 0) & (depth < 3), :3] = (152, 100, 54) if lit else (58, 48, 40)
    out[(depth >= 0) & (depth < 1), :3] = (218, 174, 116) if lit else (84, 72, 60)
    out[..., 3] = (depth >= 0) * 255
    return Image.fromarray(out, 'RGBA')


def halo(img, c1, c2, cx, cy, r, glow=GLOW, power=1.0):
    """Brillo en puntos detras del empaque, como un sol que sale."""
    a = np.asarray(img).copy()
    d = np.sqrt((xx - cx) ** 2 + ((yy - cy) * 1.15) ** 2)
    f = np.clip(1 - d / r, 0, 1) * (yy >= 108) * power
    a[(f * 0.9 > BAY) & (d < r), :3] = mixc(c1, glow, .45)
    a[(f * 0.9 > BAY + 0.3) & (d < r), :3] = mixc(c2, glow, .8)
    a[(f > 0.72) & (d < r), :3] = glow
    img.paste(Image.fromarray(a, 'RGBA'))


def rising_bag(img, bag, c1, c2, sunk=26, x=110, glow=GLOW, power=1.0):
    b = bag_obj(bag, 62)
    top = int(ydome(x)) + sunk - b.height
    halo(img, c1, c2, x, top + 18, 74, glow, power)
    img.alpha_composite(b, (x - b.width // 2, top))


def header(img, n, name, line):
    text(img, (13, 40), f'{n} / 04', F_S, CREAM)
    text(img, (12, 50), name, fit_title(name, 156, 30), CREAM)
    text(img, (13, 92), line, F_M if F_M.getlength(line) <= 160 else F_S, CREAM)


VAR = [
    dict(name='JAVA', n='01', bag='cerezas', c=[(40, 84, 40), (132, 170, 60)], noah='host', s=0.46, x=36, line='(the new kid.)',
         amb=[(10, 64, -14, 102), (13, 34, 154, 98), (57, 8, 70, 124), (58, 7, 150, 150)],
         es='El mundo gira bajo Noah y el empaque sube por detrás del horizonte, como un sol, con su brillo. El cielo se pinta de verde, entran ramas con cerezas por los bordes y el café refleja el color. Noah, al frente, sonríe.'),
    dict(name='CASTILLO', n='02', bag='colores', c=[(150, 30, 86), (234, 124, 30)], noah='listen', s=0.54, x=36, line='(the loud one.)',
         amb=[(15, 40, -10, 104), (18, 30, 156, 100), (28, 12, 66, 122), (42, 10, 152, 150)],
         es='Noah sigue caminando; el sol anterior se oculta y sale el segundo empaque. El cielo pasa a magenta y naranja, entran flores grandes por los bordes. Noah levanta la oreja.'),
    dict(name='GEISHA', n='03', bag='casa_azul', c=[(26, 66, 122), (96, 154, 200)], noah='peek', s=0.50, x=40, line='(the fancy one.)',
         amb=[(5, 62, -16, 102), (19, 36, 152, 100), (42, 10, 72, 124), (12, 12, 156, 150)],
         es='El cielo pasa a azul con neblina, entran ramas con flores de café. Sale el tercer empaque. Noah se asoma por el horizonte, muy serio.'),
    dict(name='BOURBON', n='04', bag='casa_roja', c=[(124, 28, 24), (216, 90, 52)], noah='sideeye', s=0.50, x=38, line="(...who's that dog?)",
         amb=[(7, 38, -10, 104), (2, 44, 146, 104), (51, 9, 68, 124), (26, 16, 150, 148)],
         es='El cielo pasa a rojo. Sale el cuarto empaque, el que tiene un perro pintado: Noah lo descubre y lo mira de reojo.'),
]

# ---------- 1 · amanece ----------
dim = [(22, 20, 19), (40, 36, 32)]
img = sky(*dim, glow=(86, 76, 64), mist=False)
rising_bag(img, 'cerezas', (40, 84, 40), (132, 170, 60), sunk=84, glow=(150, 170, 110), power=0.55)
text(img, (90, 78), 'FOUR NEW VARIETIES', F_M, CREAM, 'ma')
text(img, (90, 100), '(follow Noah.)', F_S, SOFT, 'ma')
img.alpha_composite(coffee(*dim, lit=False))
c = up(img, P)
noah(c, 'host', 0.46, 44 * P, int(ydome(44)) * P + 8)
B.save(c, '0 – 2,5 s', 'Amanece sobre el café', 'Todo oscuro. El horizonte curvo es la superficie de una taza de café. Noah camina por encima, grande y al frente. Por la derecha ya se asoma el primer empaque, con un brillo verde, como un sol que va a salir.',
       'FOUR NEW VARIETIES · (follow Noah.)', 'Pasitos. Un zumbido grave, como café sirviéndose.')

# ---------- 2-5 · un empaque, un cielo, una expresion ----------
times = ['2,5 – 6 s', '6 – 9 s', '9 – 12 s', '12 – 15 s']
for k, v in enumerate(VAR):
    c1, c2 = v['c']
    img = sky(c1, c2)
    for (mk, mw, mx, my) in v['amb']:
        img.alpha_composite(motif(mk, mw), (mx, my))
    rising_bag(img, v['bag'], c1, c2)
    header(img, v['n'], v['name'], v['line'])
    if v['noah'] == 'peek':                                   # Noah asomado detras del horizonte
        c = up(img, P)
        noah(c, 'peek', v['s'], v['x'] * P, int(ydome(v['x'])) * P + 26)
        c.alpha_composite(up(coffee(c1, c2), P))
    else:
        img.alpha_composite(coffee(c1, c2))
        c = up(img, P)
        noah(c, v['noah'], v['s'], v['x'] * P, int(ydome(v['x'])) * P + 8)
    B.save(c, times[k], f"Empaque: {v['name'].capitalize()}", v['es'], f"{v['n']} / 04 · {v['name']} · {v['line']}", 'Nota al llegar. Cambia el ambiente de fondo.')

# ---------- final: la tostadora -> los granos arman el logo -> el logo pasa a normal ----------
warm = [(104, 58, 22), (226, 160, 70)]
LOGO = Image.open(os.path.join(A, 'logo_blanco.png')).convert('RGBA')
rng = np.random.default_rng(4)


def pixel_logo(w, drop=0.0):
    """El logo oficial llevado a pixel art (solo se reduce: no se redibuja)."""
    h = round(LOGO.height * w / LOGO.width)
    on = np.asarray(LOGO.split()[3].resize((w, h), Image.BOX)) >= 92
    if drop:
        on &= rng.random(on.shape) > drop
    out = np.zeros((h, w, 4), np.uint8); out[on] = CREAM + (255,)
    return Image.fromarray(out, 'RGBA')


def puff(img, cx, cy, r, col=(236, 222, 200)):
    d = ImageDraw.Draw(img)
    for y in range(cy - r, cy + r + 1):
        for x in range(cx - r, cx + r + 1):
            q = ((x - cx) ** 2 + (y - cy) ** 2) / (r * r + 0.1)
            if q <= 1 and B8[y % 8, x % 8] > q * 0.8:
                d.point((x, y), fill=col)


def spaced(canvas, s, f, cx, y, track, fill):
    d = ImageDraw.Draw(canvas)
    ws = [f.getlength(ch) for ch in s]
    x = cx - (sum(ws) + track * (len(s) - 1)) / 2
    for ch, wch in zip(s, ws):
        d.text((x, y), ch, font=f, fill=fill); x += wch + track


NX = 78                                                       # donde se sienta Noah con la tostadora
# 6 · llega a la tostadora
img = sky(*warm)
text(img, (90, 62), '(first crack!)', F_M, CREAM, 'ma')
text(img, (90, 86), 'this one is almost ready.', F_S, CREAM, 'ma')
for (qx, qy, qr) in [(118, 126, 7), (128, 108, 5), (112, 110, 4), (134, 94, 3)]:
    puff(img, qx, qy, qr)
for (mk, mw, mx, my) in [(53, 10, 134, 142), (56, 9, 100, 130), (25, 10, 146, 120)]:
    img.alpha_composite(motif(mk, mw), (mx, my))
img.alpha_composite(coffee(*warm))
c = up(img, P)
noah(c, 'roaster', 0.56, NX * P, int(ydome(NX)) * P + 8)
B.save(c, '15 – 16,5 s', 'Final: el primer crack', 'Ya no hay empaques. Noah llega a la tostadora y se sienta. Suena el primer "crack": levanta la oreja de golpe, sale humo, saltan los granos y avisa que este café ya casi está listo.',
       '(first crack!) · this one is almost ready.', 'Tambor girando. Un "crack" seco.')

# 7 · los granos suben y arman el logo
img = sky((40, 24, 12), (150, 92, 36), glow=(214, 150, 80), mist=False)
lg = pixel_logo(30, drop=0.42)
big = lg.resize((lg.width * 2, lg.height * 2), Image.NEAREST)
img.alpha_composite(big, (90 - big.width // 2, 34))
for i in range(52):                                           # chorro de pixeles que sube desde la tostadora
    tt = rng.random()
    x = int(112 + (90 - 112) * tt + rng.normal(0, 10 * (0.3 + tt)))
    y = int(160 - 104 * tt + rng.normal(0, 4))
    ImageDraw.Draw(img).rectangle([x, y, x + 1, y + 1], fill=CREAM if rng.random() > 0.3 else (226, 160, 70))
for (mk, mw, mx, my) in [(53, 10, 122, 140), (56, 9, 92, 124), (25, 9, 108, 108), (53, 8, 76, 100)]:
    img.alpha_composite(motif(mk, mw), (mx, my))
img.alpha_composite(coffee(*warm))
c = up(img, P)
noah(c, 'roaster', 0.56, NX * P, int(ydome(NX)) * P + 8)
B.save(c, '16,5 – 17,5 s', 'Los granos arman el logo', 'Con el "crack" los granos salen disparados hacia arriba, se vuelven pixeles y empiezan a formar el logo de Juanito en el cielo. Noah los sigue con la mirada.',
       '(sin texto)', 'Palomitas de "crack" cada vez más rápidas, subiendo de tono.')

# 8 · solo el logo, en pixel art
img = Image.new('RGBA', (LW, LH), BLACK + (255,))
lg = pixel_logo(62)
img.alpha_composite(lg, (90 - lg.width // 2, 96))
for (x, y) in [(52, 90), (130, 104), (60, 172), (126, 166), (90, 84)]:
    ImageDraw.Draw(img).point((x, y), fill=(226, 160, 70))
B.save(up(img, P), '17,5 – 18,5 s', 'Solo el logo, en pixel art', 'Todo se va a negro. Queda únicamente el logo de Juanito, armado en pixel art. Sin empaques y sin Noah.',
       '(logo en pixel art)', 'Último pixel que encaja: un "clic".')

# 9 · el logo pasa a normal + coming soon
c = Image.new('RGBA', (LW * P, LH * P), BLACK + (255,))
lw = 62 * P
logo = LOGO.resize((lw, round(LOGO.height * lw / LOGO.width)), Image.LANCZOS)
c.alpha_composite(logo, (540 - lw // 2, 96 * P))
spaced(c, 'COMING SOON', font('montserrat', 'montserrat-latin-300-normal.woff', 40), 540, 96 * P + logo.height + 70, 20, CREAM)
B.save(c, '18,5 – 20 s', 'El logo pasa a normal', 'Los pixeles se afinan en tres saltos hasta volverse el logo normal, nítido. Debajo aparece "coming soon" en letra fina. Fin.',
       'COMING SOON', 'Una nota limpia que se sostiene y se apaga.')
B.close()
