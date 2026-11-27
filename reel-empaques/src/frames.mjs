// Storyboards del reel de Juanito Coffee: un cuadro fijo (1080x1920) por escena.
// Uso: node src/frames.mjs            -> storyboards/frames/<idea>_<n>.png + frames.json
import { createRequire } from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const { chromium } = createRequire(import.meta.url)('playwright'); // Playwright ya viene instalado en el entorno
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const SPR = path.join(ROOT, 'assets', 'sprites');
const BAGS = path.join(ROOT, 'assets', 'bags');
const OUT = path.join(ROOT, 'storyboards', 'frames');
fs.mkdirSync(OUT, { recursive: true });
const sizes = JSON.parse(fs.readFileSync(path.join(SPR, 'sizes.json'), 'utf8'));
const url = (p) => pathToFileURL(p).href;
const font = (w, s) => url(path.join(ROOT, 'node_modules/@fontsource/montserrat/files', `montserrat-latin-${w}-${s}.woff2`));

const C = { bg: '#0b0a09', cream: '#efe7da', soft: '#cfc6b8', dim: '#7d766c', line: '#262220', orange: '#e0903f' };
const W = 1080, H = 1920;

// ---------- piezas ----------
const px = (src, x, y, w, h, z = 1) =>
  `<img src="${url(src)}" style="left:${x}px;top:${y}px;width:${w}px;height:${h}px;image-rendering:pixelated;z-index:${z}">`;

/** Empaque en pixel art. p = pixeles de pantalla por pixel de arte (72 x 122 de arte). */
const bag = (name, cx, top, p, z = 2) => px(path.join(BAGS, `${name}.png`), Math.round(cx - 36 * p), top, 72 * p, 122 * p, z);

const ui = (key, x, y, p, w0, h0, z = 1, op = 1) =>
  `<img src="${url(path.join(SPR, `ui_${key}.png`))}" style="left:${x}px;top:${y}px;width:${w0 * p}px;height:${h0 * p}px;image-rendering:pixelated;z-index:${z};opacity:${op}">`;

/** Noah (ilustracion del cliente, solo recortada). Se ancla por los pies (bottom) y por el centro o un lado. */
const noah = (key, { cx, left, right, bottom, s, z = 3, pool = false }) => {
  const [w0, h0] = sizes[key];
  const w = Math.round(w0 * s), h = Math.round(h0 * s);
  const x = left !== undefined ? left : right !== undefined ? right - w : Math.round(cx - w / 2);
  const p = pool ? ui('pool', Math.round(x + w / 2 - 220), bottom - 34, 4, 110, 14) : '';
  return `${p}<img src="${url(path.join(SPR, `noah_${key}.png`))}" style="left:${x}px;top:${bottom - h}px;width:${w}px;height:${h}px;z-index:${z}">`;
};

const det = (key, cx, top, p, z = 2) => px(path.join(SPR, `det_${key}.png`), Math.round(cx - 36 * p), top, 72 * p, 54 * p, z);

const T = (str, { x, y, size, weight = 300, italic = false, track = 0, color = C.cream, align = 'left', upper = false, z = 5 }) => {
  const tx = align === 'center' ? '-50%' : align === 'right' ? '-100%' : '0';
  const pad = align === 'center' ? `padding-left:${track}em;` : align === 'right' ? `margin-right:-${track}em;` : '';
  return `<div class="t" style="left:${x}px;top:${y}px;font-size:${size}px;font-weight:${weight};font-style:${italic ? 'italic' : 'normal'};letter-spacing:${track}em;color:${color};transform:translateX(${tx});${pad}${upper ? 'text-transform:uppercase;' : ''}z-index:${z}">${str}</div>`;
};
const name = (s, x, y, align = 'left', size = 56) => T(s, { x, y, size, track: 0.28, align, upper: true });
const count = (s, x, y, align = 'left') => T(s, { x, y, size: 22, weight: 500, track: 0.34, color: C.orange, align });
const paren = (s, x, y, align = 'left', size = 30, color = C.soft) => T(s, { x, y, size, italic: true, track: 0.01, color, align });
const meta = (s, x, y, align = 'center') => T(s, { x, y, size: 20, weight: 500, track: 0.44, color: C.dim, align, upper: true });
const big = (s, x, y, align = 'center', size = 50) => T(s, { x, y, size, weight: 300, track: 0.02, align });
const hline = (y, x1 = 0, x2 = W, color = C.line, h = 2) =>
  `<div style="left:${x1}px;top:${y}px;width:${x2 - x1}px;height:${h}px;background:${color};z-index:1"></div>`;
const logo = (cx, top, w) => `<img src="${url(path.join(ROOT, 'assets', 'logo_blanco.png'))}" style="left:${Math.round(cx - w / 2)}px;top:${top}px;width:${w}px;z-index:4">`;

// ============ IDEA 1 · THE COLLECTION (la galeria) ============
const FLOOR = 1560;
const piece = (bagName, variety, n, medium, noahKey, s, line) => [
  ui('halo', 120, 196, 4, 210, 240),
  ui('lamp', 540 - 119, 172, 7, 34, 7, 2),
  bag(bagName, 540, 250, 7),
  name(variety, 288, 1140),
  paren(medium, 288, 1222, 'left', 27),
  count(`${n} / 04`, 288, 1282),
  hline(FLOOR),
  noah(noahKey, { right: 1010, bottom: FLOOR + 6, s, pool: true }),
  paren(line, 610, 1440, 'right', 30, C.cream),
];

const idea1 = [
  {
    t: '0 – 2,5 s', title: 'Se enciende la luz',
    es: 'Sala oscura. Una lámpara de cuadro se enciende y aparece Noah, de anfitrión, con el café en la mano.',
    text: 'JUANITO COFFEE · THE NEW COLLECTION · (guided tour by Noah)',
    snd: 'Clic de interruptor, zumbido suave de lámpara.',
    html: [
      ui('halo', 120, 322, 4, 210, 240),
      ui('lamp', 540 - 119, 300, 7, 34, 7, 2),
      meta('Juanito Coffee', 540, 452),
      T('THE NEW COLLECTION', { x: 540, y: 500, size: 52, track: 0.2, align: 'center' }),
      paren('(guided tour by Noah)', 540, 590, 'center', 30),
      hline(FLOOR),
      noah('host', { cx: 540, bottom: FLOOR + 8, s: 0.6, pool: true }),
    ],
  },
  {
    t: '2,5 – 6 s', title: 'Primera pieza: Java',
    es: 'El empaque de las cerezas cuelga como un cuadro bajo su lámpara. La ficha de museo dice la variedad. Noah lo presenta.',
    text: 'JAVA · (watercolor on coffee bag) · 01 / 04 — Noah: (my favorite.)',
    snd: 'Clic de lámpara + una nota suave.',
    html: piece('cerezas', 'Java', '01', '(watercolor on coffee bag)', 'host', 0.4, '(my favorite.)'),
  },
  {
    t: '6 – 9 s', title: 'Segunda pieza: Castillo',
    es: 'Corte a la siguiente pieza: el empaque de colores. Noah levanta la oreja, emocionado.',
    text: 'CASTILLO · (illustration on coffee bag) · 02 / 04 — Noah: (also my favorite.)',
    snd: 'Clic + nota un tono más arriba.',
    html: piece('colores', 'Castillo', '02', '(illustration on coffee bag)', 'listen', 0.46, '(also my favorite.)'),
  },
  {
    t: '9 – 12 s', title: 'Tercera pieza: Geisha',
    es: 'El empaque de la casa azul. Noah se asoma muy serio, como crítico de arte.',
    text: 'GEISHA · (watercolor on coffee bag) · 03 / 04 — Noah: (okay. this one.)',
    snd: 'Clic + nota.',
    html: piece('casa_azul', 'Geisha', '03', '(watercolor on coffee bag)', 'peek', 0.4, '(okay. this one.)'),
  },
  {
    t: '12 – 15 s', title: 'Cuarta pieza: Bourbon',
    es: 'El empaque de la casa roja. Noah mira de reojo: no logra escoger.',
    text: "BOURBON · (watercolor on coffee bag) · 04 / 04 — Noah: (I can't pick.)",
    snd: 'Clic + nota final del acorde.',
    html: piece('casa_roja', 'Bourbon', '04', '(watercolor on coffee bag)', 'sideeye', 0.42, "(I can't pick.)"),
  },
  {
    t: '15 – 17,5 s', title: 'La pared completa',
    es: 'La cámara se aleja: las cuatro piezas en la pared, cada una con su nombre. Noah abraza su taza.',
    text: 'New look. Noah approved. · (all four.)',
    snd: 'Las cuatro notas juntas (acorde).',
    html: [
      meta('The new collection', 540, 330),
      ...['cerezas', 'colores', 'casa_azul', 'casa_roja'].flatMap((b, i) => {
        const cx = 63 + 108 + i * 246;
        return [
          ui('lamp', cx - 51, 426, 3, 34, 7, 2),
          bag(b, cx, 462, 3),
          T(['Java', 'Castillo', 'Geisha', 'Bourbon'][i], { x: cx, y: 852, size: 19, weight: 400, track: 0.3, align: 'center', upper: true }),
        ];
      }),
      big('New look. Noah approved.', 540, 990, 'center', 46),
      paren('(all four.)', 540, 1062, 'center', 30),
      hline(FLOOR),
      noah('mug', { cx: 540, bottom: FLOOR + 6, s: 0.42, pool: true }),
    ],
  },
  {
    t: '17,5 – 20 s', title: 'Cierre',
    es: 'Última pieza de la pared: el logo. Noah ya se durmió en el piso de la sala.',
    text: 'COMING SOON · (green coffee · Huila, Colombia) · @juanitocoffee',
    snd: 'Lámpara que se apaga despacio, silencio.',
    html: [
      ui('halo', 120, 290, 4, 210, 240),
      ui('lamp', 540 - 119, 268, 7, 34, 7, 2),
      logo(540, 370, 400),
      T('COMING SOON', { x: 540, y: 900, size: 38, weight: 300, track: 0.5, align: 'center' }),
      paren('(green coffee · Huila, Colombia)', 540, 972, 'center', 28),
      T('@juanitocoffee', { x: 540, y: 1036, size: 24, weight: 400, track: 0.08, color: C.orange, align: 'center' }),
      hline(FLOOR),
      noah('sleep', { cx: 540, bottom: FLOOR + 6, s: 0.42, pool: true }),
    ],
  },
];

// ============ IDEA 2 · DOG NOT INCLUDED (Noah opina) ============
const NB = 1570; // pies de Noah
const close = (d, line, noahKey, s) => [
  det(d, 540, 280, 13),
  paren(line, 72, 1160, 'left', 38, C.cream),
  noah(noahKey, { right: 1010, bottom: NB, s }),
];
const full = (b, variety, n, noahKey, s, extra = []) => [
  bag(b, 540, 215, 7),
  count(`${n} / 04`, 72, 1118),
  name(variety, 72, 1156, 'left', 60),
  noah(noahKey, { right: 1010, bottom: NB, s }),
  ...extra,
];

const idea2 = [
  {
    t: '0 – 2 s', title: 'Noah tiene opiniones',
    es: 'Noah en primer plano, mirando de reojo. Entra el texto.',
    text: 'New bags. · (Noah has notes.)',
    snd: 'Un golpe seco de bombo. Silencio.',
    html: [
      big('New bags.', 540, 330, 'center', 72),
      paren('(Noah has notes.)', 540, 440, 'center', 36),
      noah('sideeye', { cx: 540, bottom: 1440, s: 0.9 }),
    ],
  },
  {
    t: '2 – 3,2 s', title: 'Detalle: las cerezas',
    es: 'Primerísimo plano del dibujo del empaque, en pixeles grandes. Noah lo comenta.',
    text: '(this one has cherries.)',
    snd: 'Golpe 1.',
    html: close('cerezas', '(this one has cherries.)', 'host', 0.42),
  },
  {
    t: '3,2 – 5 s', title: 'Se abre: Java',
    es: 'La imagen se aleja en tres saltos de pixel hasta mostrar el empaque completo, con su variedad.',
    text: '01 / 04 · JAVA',
    snd: 'Tres clics descendentes + nota.',
    html: full('cerezas', 'Java', '01', 'host', 0.42),
  },
  {
    t: '5 – 6,2 s', title: 'Detalle: la fiesta',
    es: 'Los bailarines del empaque de colores. Noah levanta la oreja: lo oye.',
    text: '(this one has a party.)',
    snd: 'Golpe 2 + un compás de guitarra.',
    html: close('fiesta', '(this one has a party.)', 'listen', 0.48),
  },
  {
    t: '6,2 – 8 s', title: 'Se abre: Castillo',
    es: 'Saltos de pixel hacia atrás: el empaque de colores completo.',
    text: '02 / 04 · CASTILLO',
    snd: 'Tres clics + nota.',
    html: full('colores', 'Castillo', '02', 'listen', 0.48),
  },
  {
    t: '8 – 9,2 s', title: 'Detalle: la mula',
    es: 'El arriero y la mula cargada de la acuarela de la casa azul. Noah, muy serio.',
    text: '(this one has a mule.)',
    snd: 'Golpe 3 + cascos lejanos.',
    html: close('mula', '(this one has a mule.)', 'peek', 0.4),
  },
  {
    t: '9,2 – 11 s', title: 'Se abre: Geisha',
    es: 'El empaque de la casa azul completo.',
    text: '03 / 04 · GEISHA',
    snd: 'Tres clics + nota.',
    html: full('casa_azul', 'Geisha', '03', 'peek', 0.4),
  },
  {
    t: '11 – 12,6 s', title: 'Detalle: ¿un perro?',
    es: 'El perrito pintado en la acuarela de la casa roja. Noah lo descubre y mira de reojo.',
    text: '(this one has… a dog?)',
    snd: 'La música se corta. Un ladrido chiquito.',
    html: close('perro', '(this one has… a dog?)', 'sideeye', 0.44),
  },
  {
    t: '12,6 – 14,5 s', title: 'Se abre: Bourbon',
    es: 'El empaque de la casa roja completo. Noah sigue ofendido.',
    text: '04 / 04 · BOURBON — Noah: (not me.)',
    snd: 'Tres clics + nota. Vuelve la música.',
    html: full('casa_roja', 'Bourbon', '04', 'sideeye', 0.44, [paren('(not me.)', 72, 1262, 'left', 34, C.cream)]),
  },
  {
    t: '14,5 – 17 s', title: 'Los cuatro juntos',
    es: 'Los cuatro empaques en fila con sus nombres. Noah, feliz dentro de la caja de regalo.',
    text: 'Four new bags. · Dog not included.',
    snd: 'Acorde completo.',
    html: [
      big('Four new bags.', 540, 300, 'center', 58),
      ...['cerezas', 'colores', 'casa_azul', 'casa_roja'].flatMap((b, i) => {
        const cx = 63 + 108 + i * 246;
        return [bag(b, cx, 440, 3), T(['Java', 'Castillo', 'Geisha', 'Bourbon'][i], { x: cx, y: 830, size: 19, weight: 400, track: 0.3, align: 'center', upper: true })];
      }),
      big('Dog not included.', 540, 930, 'center', 58),
      noah('gift', { cx: 540, bottom: NB, s: 0.46 }),
    ],
  },
  {
    t: '17 – 20 s', title: 'Cierre',
    es: 'Logo y datos. Noah abrazado a su taza.',
    text: 'COMING SOON · (green coffee · Huila, Colombia) · @juanitocoffee',
    snd: 'Nota final que se apaga.',
    html: [
      logo(540, 300, 380),
      T('COMING SOON', { x: 540, y: 800, size: 38, weight: 300, track: 0.5, align: 'center' }),
      paren('(green coffee · Huila, Colombia)', 540, 872, 'center', 28),
      T('@juanitocoffee', { x: 540, y: 936, size: 24, weight: 400, track: 0.08, color: C.orange, align: 'center' }),
      noah('mug', { cx: 540, bottom: NB, s: 0.5 }),
    ],
  },
];

// ============ IDEA 3 · NOAH'S DREAM (el sueno) ============
const BX = 42, BY = 116, BP = 6; // burbuja: 166 x 176 px de arte
const bubble = () => [
  ui('bubble', BX, BY, BP, 166, 176, 1),
  ui('dot_l', 640, 1200, BP, 14, 14, 1),
  ui('dot_m', 644, 1300, BP, 9, 9, 1),
];
const sleeper = (key = 'sleepbody', s = 0.4) => [noah(key, { cx: 520, bottom: 1590, s, pool: true })];
const dream = (b, variety, n) => [
  ...bubble(),
  bag(b, 540, 256, 6),
  name(variety, 540, 1012, 'center', 50),
  count(`${n} / 04`, 540, 1086, 'center'),
];

const idea3 = [
  {
    t: '0 – 2,5 s', title: 'Shhh',
    es: 'Todo negro. Noah duerme abajo. De su cabeza sube un rizo de humo.',
    text: 'shhh. · (Noah is dreaming.)',
    snd: 'Ronquido suave, grillos lejanos.',
    html: [
      big('shhh.', 540, 660, 'center', 64),
      paren('(Noah is dreaming.)', 540, 760, 'center', 32),
      noah('sleep', { cx: 520, bottom: 1590, s: 0.4, pool: true }),
    ],
  },
  {
    t: '2,5 – 4,5 s', title: 'Se abre el sueño',
    es: 'El humo se vuelve una burbuja de sueño que crece hasta llenar la pantalla.',
    text: '(four new varieties) · from Huila, Colombia',
    snd: 'Burbujas que suben, arpa corta.',
    html: [
      ...bubble(),
      paren('(four new varieties)', 540, 570, 'center', 40, C.cream),
      T('FROM HUILA, COLOMBIA', { x: 540, y: 660, size: 22, weight: 500, track: 0.4, color: C.dim, align: 'center' }),
      ...sleeper(),
    ],
  },
  {
    t: '4,5 – 7 s', title: 'Sueña con Java',
    es: 'Dentro de la burbuja aparece el empaque de las cerezas, con su variedad.',
    text: 'JAVA · 01 / 04',
    snd: 'Nota de caja de música.',
    html: [...dream('cerezas', 'Java', '01'), ...sleeper()],
  },
  {
    t: '7 – 9,5 s', title: 'Sueña con Castillo',
    es: 'El empaque de colores reemplaza al anterior con un "pop". Noah sigue dormido.',
    text: 'CASTILLO · 02 / 04',
    snd: 'Pop + nota.',
    html: [...dream('colores', 'Castillo', '02'), ...sleeper()],
  },
  {
    t: '9,5 – 12 s', title: 'Sueña con Geisha',
    es: 'El empaque de la casa azul.',
    text: 'GEISHA · 03 / 04',
    snd: 'Pop + nota.',
    html: [...dream('casa_azul', 'Geisha', '03'), ...sleeper()],
  },
  {
    t: '12 – 14,5 s', title: 'Bourbon… y un perro',
    es: 'El empaque de la casa roja, que tiene un perro pintado. Noah abre un ojo: se despertó.',
    text: 'BOURBON · 04 / 04 — Noah: (…another dog?)',
    snd: 'Pop + nota. Se corta el ronquido.',
    html: [...dream('casa_roja', 'Bourbon', '04'), noah('sideeye', { cx: 500, bottom: 1590, s: 0.36, pool: true }), paren('(…another dog?)', 700, 1450, 'left', 30, C.cream)],
  },
  {
    t: '14,5 – 17 s', title: 'No era un sueño',
    es: 'La burbuja revienta. Los cuatro empaques quedan ahí, de verdad, en fila. Noah ya está de pie sirviendo café.',
    text: 'Not a dream. · (almost.)',
    snd: 'Burbuja que revienta, acorde completo.',
    html: [
      big('Not a dream.', 540, 300, 'center', 60),
      paren('(almost.)', 540, 392, 'center', 34),
      ...['cerezas', 'colores', 'casa_azul', 'casa_roja'].flatMap((b, i) => {
        const cx = 63 + 108 + i * 246;
        return [bag(b, cx, 520, 3), T(['Java', 'Castillo', 'Geisha', 'Bourbon'][i], { x: cx, y: 912, size: 19, weight: 400, track: 0.3, align: 'center', upper: true })];
      }),
      noah('host', { cx: 540, bottom: 1590, s: 0.46, pool: true }),
    ],
  },
  {
    t: '17 – 20 s', title: 'Cierre',
    es: 'Logo y datos. Noah vuelve a dormirse, ahora junto a la moka y un saco de café verde.',
    text: 'COMING SOON · (green coffee · Huila, Colombia) · @juanitocoffee',
    snd: 'Vuelve el ronquido. Fin.',
    html: [
      logo(540, 300, 380),
      T('COMING SOON', { x: 540, y: 800, size: 38, weight: 300, track: 0.5, align: 'center' }),
      paren('(green coffee · Huila, Colombia)', 540, 872, 'center', 28),
      T('@juanitocoffee', { x: 540, y: 936, size: 24, weight: 400, track: 0.08, color: C.orange, align: 'center' }),
      noah('moka', { cx: 540, bottom: 1590, s: 0.44, pool: true }),
    ],
  },
];

export const IDEAS = [
  { id: 'a', frames: idea1 },
  { id: 'b', frames: idea2 },
  { id: 'c', frames: idea3 },
];

const page = (parts) => `<!doctype html><meta charset="utf-8"><style>
@font-face{font-family:M;font-weight:300;font-style:normal;src:url(${font(300, 'normal')})}
@font-face{font-family:M;font-weight:300;font-style:italic;src:url(${font(300, 'italic')})}
@font-face{font-family:M;font-weight:400;font-style:normal;src:url(${font(400, 'normal')})}
@font-face{font-family:M;font-weight:500;font-style:normal;src:url(${font(500, 'normal')})}
html,body{margin:0;background:${C.bg}}
#f{position:relative;width:${W}px;height:${H}px;overflow:hidden;background:${C.bg};font-family:M,sans-serif}
#f>*{position:absolute}
.t{white-space:nowrap;line-height:1}
</style><div id="f">${parts.join('\n')}</div>`;

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const only = process.argv[2];
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
  const pg = await ctx.newPage();
  const index = [];
  for (const idea of IDEAS) {
    for (const [i, f] of idea.frames.entries()) {
      const id = `${idea.id}_${String(i + 1).padStart(2, '0')}`;
      index.push({ id, idea: idea.id, n: i + 1, t: f.t, title: f.title, es: f.es, text: f.text, snd: f.snd });
      if (only && !id.startsWith(only)) continue;
      const tmp = path.join(OUT, `_${id}.html`);
      fs.writeFileSync(tmp, page(f.html.flat()));
      await pg.goto(url(tmp));
      await pg.evaluate(() => document.fonts.ready);
      await pg.locator('#f').screenshot({ path: path.join(OUT, `${id}.png`) });
      fs.unlinkSync(tmp);
    }
  }
  fs.writeFileSync(path.join(OUT, 'frames.json'), JSON.stringify(index, null, 1));
  await browser.close();
  console.log('ok', index.length, 'cuadros');
}
