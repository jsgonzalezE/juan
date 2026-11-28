// Prueba de estilo: ficha por variedad con degradado y grano (referencia nueva del cliente).
// Uso: node src/style_cards.mjs  -> storyboards/estilo/ficha_<variedad>.png + prueba_fichas.jpg
import { createRequire } from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const { chromium } = createRequire(import.meta.url)('playwright');
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const OUT = path.join(ROOT, 'storyboards', 'estilo');
fs.mkdirSync(OUT, { recursive: true });
const url = (p) => pathToFileURL(p).href;
const font = (w, s) => url(path.join(ROOT, 'node_modules/@fontsource/montserrat/files', `montserrat-latin-${w}-${s}.woff2`));
const sizes = JSON.parse(fs.readFileSync(path.join(ROOT, 'assets/sprites/sizes.json'), 'utf8'));

const CARDS = [
  { id: 'java', name: 'JAVA', n: '01', bag: 'cerezas', noah: 'host', s: 0.36 },
  { id: 'castillo', name: 'CASTILLO', n: '02', bag: 'colores', noah: 'listen', s: 0.42 },
  { id: 'geisha', name: 'GEISHA', n: '03', bag: 'casa_azul', noah: 'peek', s: 0.36 },
  { id: 'bourbon', name: 'BOURBON', n: '04', bag: 'casa_roja', noah: 'sideeye', s: 0.38 },
];
const CREAM = '#f3ead9', INK = '#1b1613';

const card = (c) => {
  const [w0, h0] = sizes[c.noah];
  const nw = Math.round(w0 * c.s), nh = Math.round(h0 * c.s);
  const scatter = [
    ['New variety', 700, 905, 0.9], ['from', 860, 962, 0.55], ['Huila,', 690, 1006, 0.7],
    ['Colombia', 800, 1052, 0.5], ['new bag', 690, 1104, 0.38], ['coming soon', 840, 1146, 0.3],
  ];
  return `<!doctype html><meta charset="utf-8"><style>
@font-face{font-family:M;font-weight:300;src:url(${font(300, 'normal')})}
@font-face{font-family:M;font-weight:300;font-style:italic;src:url(${font(300, 'italic')})}
@font-face{font-family:M;font-weight:400;src:url(${font(400, 'normal')})}
@font-face{font-family:M;font-weight:700;src:url(${font(700, 'normal')})}
@font-face{font-family:M;font-weight:900;src:url(${font(900, 'normal')})}
html,body{margin:0}
#f{position:relative;width:1080px;height:1920px;overflow:hidden;font-family:M,sans-serif;background:url(${url(path.join(ROOT, 'assets/style', `bg_${c.id}.jpg`))})}
#f>*{position:absolute}
.t{white-space:nowrap;line-height:1}
.h{font-size:19px;font-weight:700;letter-spacing:.16em;color:${INK}}
.b{font-size:19px;font-weight:400;line-height:1.5;color:${INK};white-space:normal}
.dot{width:9px;height:9px;border-radius:50%;background:${INK}}
</style><div id="f">
<img src="${url(path.join(ROOT, 'assets/bags', `${c.bag}.png`))}" style="left:${540 - 216}px;top:150px;width:432px;height:732px;image-rendering:pixelated">
<div class="t" style="left:70px;top:948px;font-size:${c.name.length > 6 ? 104 : 128}px;font-weight:900;letter-spacing:-.01em;color:${CREAM}">${c.name}</div>
<div class="t" style="left:74px;top:1082px;font-size:26px;font-weight:700;letter-spacing:.3em;color:${CREAM}">${c.n} / 04</div>
${scatter.map(([s, x, y, o]) => `<div class="t" style="left:${x}px;top:${y}px;font-size:31px;font-weight:300;color:${CREAM};opacity:${o}">${s}</div>`).join('')}
<div class="dot" style="left:830px;top:880px"></div><div class="dot" style="left:1002px;top:1210px"></div>
<div class="t h" style="left:70px;top:1300px">TASTING NOTES</div>
<div class="b" style="left:70px;top:1332px;width:400px"><i>(aquí van tus notas de cata reales)</i></div>
<div class="t h" style="left:70px;top:1436px">PROCESS</div>
<div class="b" style="left:70px;top:1468px;width:400px"><i>(aquí va el proceso real)</i></div>
<img src="${url(path.join(ROOT, 'assets/sprites', `noah_${c.noah}.png`))}" style="left:${1010 - nw}px;top:${1640 - nh}px;width:${nw}px;height:${nh}px">
<div class="t h" style="left:70px;top:1690px">ORIGIN</div>
<div class="t h" style="left:1010px;top:1690px;transform:translateX(-100%)">HUILA, COLOMBIA</div>
</div>`;
};

const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
const pg = await ctx.newPage();
for (const c of CARDS) {
  const tmp = path.join(OUT, `_${c.id}.html`);
  fs.writeFileSync(tmp, card(c));
  await pg.goto(url(tmp));
  await pg.evaluate(() => document.fonts.ready);
  await pg.locator('#f').screenshot({ path: path.join(OUT, `ficha_${c.id}.png`) });
  fs.unlinkSync(tmp);
}
// lamina con las cuatro
const sheet = `<!doctype html><meta charset="utf-8"><style>html,body{margin:0;background:#171513}
#s{display:flex;gap:20px;padding:28px;width:${4 * 540 + 3 * 20}px}img{width:540px;height:960px;display:block}</style>
<div id="s">${CARDS.map((c) => `<img src="${url(path.join(OUT, `ficha_${c.id}.png`))}">`).join('')}</div>`;
const tmp = path.join(OUT, '_sheet.html');
fs.writeFileSync(tmp, sheet);
const pg2 = await (await browser.newContext({ viewport: { width: 2400, height: 1100 }, deviceScaleFactor: 1 })).newPage();
await pg2.goto(url(tmp));
await pg2.locator('#s').screenshot({ path: path.join(OUT, 'prueba_fichas.jpg'), type: 'jpeg', quality: 90 });
fs.unlinkSync(tmp);
await browser.close();
console.log('ok');
