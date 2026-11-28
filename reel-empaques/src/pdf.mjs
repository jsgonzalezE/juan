// Junta todas las ideas en un PDF (A4 vertical) para verlas en el celular.
// Uso: python3 src/pdf_images.py && node src/pdf.mjs  -> storyboards/Juanito_Coffee_ideas_reel.pdf
import { createRequire } from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { META, loadFrames } from './ideas.mjs';

const { chromium } = createRequire(import.meta.url)('playwright');
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const SB = path.join(ROOT, 'storyboards');
const IMG = path.join(SB, 'pdf', 'img');
const MODE = process.argv[2];   // 'f' = PDF solo de la idea F afinada; sin argumento = todas las ideas
const OUT = path.join(SB, MODE === 'f' ? 'Juanito_Coffee_idea_F_afinada.pdf' : 'Juanito_Coffee_ideas_reel.pdf');
const url = (p) => pathToFileURL(p).href;
const img = (name) => url(path.join(IMG, name));
const font = (w, s) => url(path.join(ROOT, 'node_modules/@fontsource/montserrat/files', `montserrat-latin-${w}-${s}.woff2`));
const frames = loadFrames(path.join(SB, 'frames'));
const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

const STATUS = { now: 'En curso', pick: 'Falta escoger', old: 'Anterior' };

// orden del PDF: primero lo que esta en curso y lo que falta escoger
const SECTIONS = [
  { kind: 'idea', id: 'f', status: 'now' },
  { kind: 'options', id: 'h', status: 'pick' },
  { kind: 'idea', id: 'e', status: 'old' },
  { kind: 'idea', id: 'd', status: 'old' },
  { kind: 'style', id: 'estilo', status: 'old' },
  { kind: 'idea', id: 'a', status: 'old' },
  { kind: 'idea', id: 'b', status: 'old' },
  { kind: 'idea', id: 'c', status: 'old' },
];
const OPTIONS = {
  label: 'Opciones de taza · para la idea F', name: '¿CÓMO SE VE LA TAZA?', sub: 'la misma escena armada de cinco maneras',
  what: 'Todas muestran la misma parada (Java). Solo cambia cómo se ve la taza sobre la que camina Noah.',
  ask: 'Que escojas un número. También se pueden mezclar: una para abrir el video y otra para las paradas.',
  line: 'Cinco formas de armar la escena de la taza. Escoge un número.',
};
const STYLE = {
  label: 'Prueba de estilo · de tu referencia', name: 'FICHAS DE COLOR', sub: 'degradado con grano: de negro a color a crema',
  what: 'Una ficha por variedad con el color sacado del dibujo de cada empaque, título grueso y palabras sueltas, como la referencia de Instagram que mandaste.',
  after: 'Se mezcló con el pixel art en la idea D, y el cielo de color quedó en las ideas E y F.',
  line: 'Fichas de color con degradado y grano, sacadas de tu referencia.',
  cards: [['java', 'Java', '01'], ['castillo', 'Castillo', '02'], ['geisha', 'Geisha', '03'], ['bourbon', 'Bourbon', '04']],
};

const head = (sid, label, name, sub, status, rows) => `
  <div class="block start sec" id="sec-${sid}">
    <div class="lab"><span>${esc(label)}</span><b class="st st-${status}">${STATUS[status]}</b></div>
    <h1>${esc(name)}</h1><em>(${esc(sub)})</em>
    <dl>${rows.map(([k, v]) => `<dt>${k}</dt><dd>${esc(v)}</dd>`).join('')}</dl>
  </div>`;

const rowsOf = (items, cols, cell, cls = '') => {
  const out = [];
  for (let i = 0; i < items.length; i += cols) {
    out.push(`<div class="block grid ${cls}" style="grid-template-columns:repeat(${cols},1fr)">${items.slice(i, i + cols).map(cell).join('')}</div>`);
  }
  return out.join('');
};

const frameCell = (f) => `
  <figure><img src="${img(`${f.id}.png`)}">
    <figcaption>
      <div class="k"><b>${f.n}</b><span>${esc(f.t)}</span></div>
      <h3>${esc(f.title)}</h3>
      <p>${esc(f.es)}</p>
      <p><i>En pantalla:</i> ${esc(f.text)}</p>
      <p><i>Sonido:</i> ${esc(f.snd)}</p>
    </figcaption></figure>`;

const section = (s) => {
  if (s.kind === 'idea') {
    const m = META[s.id];
    const fs_ = frames.filter((f) => f.idea === s.id);
    return head(s.id, `${m.n} · ${fs_.length} cuadros · 20 s`, m.name, m.sub, s.status, [['La idea', m.what], ['Tono', m.tone], ['Noah', m.noah]])
      + (m.pano ? `<div class="block pano"><small>El recorrido completo, de un vistazo</small><img src="${img('panorama_e.png')}"></div>` : '')
      + rowsOf(fs_, 4, frameCell);
  }
  if (s.kind === 'options') {
    const o = frames.filter((f) => f.idea === 'h');
    return head('h', OPTIONS.label, OPTIONS.name, OPTIONS.sub, s.status, [['La idea', OPTIONS.what], ['Falta', OPTIONS.ask]])
      + rowsOf(o, 3, (f) => `<figure class="opt"><img src="${img(`${f.id}.png`)}"><figcaption><div class="num">${f.n}</div><h3>${esc(f.title)}</h3><p>${esc(f.es)}</p></figcaption></figure>`);
  }
  return head('estilo', STYLE.label, STYLE.name, STYLE.sub, s.status, [['La idea', STYLE.what], ['Qué pasó', STYLE.after]])
    + rowsOf(STYLE.cards, 4, ([id, nm, n]) => `<figure><img src="${img(`ficha_${id}.jpg`)}"><figcaption><div class="k"><b>${n}</b></div><h3>${nm}</h3></figcaption></figure>`);
};

const lineOf = (s) => (s.kind === 'idea' ? META[s.id].line : s.kind === 'options' ? OPTIONS.line : STYLE.line);
const nameOf = (s) => (s.kind === 'idea' ? `${META[s.id].n.split(' · ')[0]} · ${META[s.id].name}` : s.kind === 'options' ? 'Opciones de taza' : 'Prueba de estilo');
const indexRows = (st) => SECTIONS.filter((s) => (st === 'old' ? s.status === 'old' : s.status !== 'old')).map((s) => `
  <tr><td class="nm">${esc(nameOf(s))}</td><td>${esc(lineOf(s))}</td><td class="pg" data-goto="sec-${s.id}"></td></tr>`).join('');

const cover = `
  <div class="block start cover">
    <div class="lab"><span>Juanito Coffee · reel de los nuevos empaques</span></div>
    <h1 class="big">IDEAS PARA EL REEL</h1>
    <em>(para escoger)</em>
    <div class="thumbs">${['f_02', 'f_06', 'h_02', 'e_02', 'd_03', 'a_02'].map((id) => `<img src="${img(`${id}.png`)}">`).join('')}</div>
    <h2>En curso</h2>
    <table>${indexRows('now')}</table>
    <h2>Ideas anteriores</h2>
    <table>${indexRows('old')}</table>
    <p class="note">En todos los cuadros Noah aparece con tus ilustraciones fijas: son un marcador hasta que lleguen las animaciones. Los empaques están pasados a pixel art a partir de las fotos de los mockups.</p>
  </div>`;

const closing = `
  <div class="block start sec">
    <div class="lab"><span>Para seguir</span></div>
    <h1>LO QUE FALTA DECIDIR</h1>
    <ol class="todo">
      <li><b>La taza.</b> El número de la opción que más te guste (1 a 5), o cuál usar para abrir y cuál para las paradas.</li>
      <li><b>Empaque y variedad.</b> Hoy va Java con las cerezas, Castillo con el de colores, Geisha con la casa azul y Bourbon con la casa roja. Falta confirmarlo.</li>
      <li><b>Notas de sabor.</b> Dos o tres palabras reales por variedad, para escoger lo que flota en el cielo de cada una.</li>
      <li><b>Animaciones de Noah.</b> El encargo para quien las hace está en el archivo ENCARGO_ANIMACIONES_NOAH.md.</li>
    </ol>
  </div>`;

const fF = frames.filter((f) => f.idea === 'f');
const coverF = `
  <div class="block start cover">
    <div class="lab"><span>Juanito Coffee · reel de los nuevos empaques</span><b class="st st-now">Versión afinada</b></div>
    <h1 class="big">COFFEE HORIZON</h1>
    <em>(Noah camina sobre la curva de una taza de café)</em>
    <div class="ba">
      <figure><img src="${img('prev_f_02.png')}"><figcaption><h3>Antes</h3></figcaption></figure>
      <figure><img src="${img('f_02.png')}"><figcaption><h3>Ahora</h3></figcaption></figure>
      <div class="chg">
        <h2>Qué cambió en esta vuelta</h2>
        <ol>
          <li><b>El horizonte curvo es solo para caminar.</b> Mientras Noah va de un empaque al siguiente, el mundo gira bajo él.</li>
          <li><b>Al llegar, el piso se aplana.</b> En cada empaque y en la tostadora el horizonte queda recto.</li>
          <li><b>Todo más grande en las llegadas.</b> La cámara se acerca: Noah y el empaque ocupan casi toda la pantalla, y el empaque se ve completo.</li>
        </ol>
        <h2 style="margin-top:4mm">Se mantiene</h2>
        <ol>
          <li>El brillo detrás del empaque y el café que refleja el color de cada variedad.</li>
          <li>Ramas y flores grandes entrando por los bordes, con neblina.</li>
          <li>El final: primer "crack", el logo en pixel art que pasa a normal y coming soon.</li>
        </ol>
      </div>
    </div>
    <h2>El video completo, de un vistazo</h2>
    <div class="thumbs nine">${fF.map((f) => `<img src="${img(`${f.id}.png`)}">`).join('')}</div>
    <p class="note">En las páginas siguientes va cada cuadro en grande, con lo que pasa, el texto en pantalla y el sonido. Noah aparece con tus ilustraciones fijas: son un marcador hasta que lleguen las animaciones.</p>
  </div>`;
const closingF = `
  <div class="block start sec">
    <div class="lab"><span>Para seguir</span></div>
    <h1>LO QUE SIGUE</h1>
    <ol class="todo">
      <li><b>Tu visto bueno a esta versión,</b> o lo que quieras cambiar: puedes rayar encima de cualquier cuadro.</li>
      <li><b>Empaque y variedad.</b> Hoy va Java con las cerezas, Castillo con el de colores, Geisha con la casa azul y Bourbon con la casa roja. Falta confirmarlo.</li>
      <li><b>Notas de sabor.</b> Dos o tres palabras reales por variedad, para escoger qué entra por los bordes de cada cielo.</li>
      <li><b>Animaciones de Noah.</b> Caminar en el sitio, una expresión por empaque y el sobresalto del "crack". El encargo está en ENCARGO_ANIMACIONES_NOAH.md.</li>
      <li><b>Después:</b> una prueba de movimiento de una sola escena, antes de hacer el video completo.</li>
    </ol>
  </div>`;
const CONTENT = MODE === 'f'
  ? coverF + rowsOf(fF, 2, frameCell, 'bigcap') + closingF
  : cover + SECTIONS.map(section).join('') + closing;

const html = `<!doctype html><meta charset="utf-8"><style>
@font-face{font-family:M;font-weight:300;src:url(${font(300, 'normal')})}
@font-face{font-family:M;font-weight:300;font-style:italic;src:url(${font(300, 'italic')})}
@font-face{font-family:M;font-weight:400;src:url(${font(400, 'normal')})}
@font-face{font-family:M;font-weight:400;font-style:italic;src:url(${font(400, 'italic')})}
@font-face{font-family:M;font-weight:500;src:url(${font(500, 'normal')})}
@page{size:A4;margin:0}
*{box-sizing:border-box;-webkit-print-color-adjust:exact;print-color-adjust:exact}
html,body{margin:0;background:#141210;font-family:M,sans-serif;color:#efe7da}
#src{display:none}
.page{width:210mm;height:297mm;padding:13mm 12mm 0;background:#141210;display:flex;flex-direction:column;break-after:page;overflow:hidden}
.page:last-child{break-after:auto}
.body{flex:1;overflow:hidden;display:flex;flex-direction:column;gap:6mm}
.page>footer{height:11mm;display:flex;justify-content:space-between;align-items:center;font-size:6.5pt;letter-spacing:.2em;text-transform:uppercase;color:#6f685f;border-top:.2mm solid #2c2825}
.lab{display:flex;justify-content:space-between;align-items:center;font-size:7pt;font-weight:500;letter-spacing:.3em;text-transform:uppercase;color:#e0903f;margin-bottom:3mm}
.st{font-weight:500;letter-spacing:.18em;padding:1.2mm 2.4mm;border-radius:10mm;font-size:6pt}
.st-now{background:#e0903f;color:#141210}.st-pick{border:.3mm solid #e0903f;color:#e0903f}.st-old{border:.3mm solid #4a443e;color:#8d857a}
h1{margin:0;font-size:22pt;font-weight:300;letter-spacing:.14em;line-height:1.1}
h1.big{font-size:30pt;margin-top:8mm}
em{display:block;margin-top:1.5mm;font-size:10.5pt;font-weight:300;color:#cfc6b8}
dl{display:grid;grid-template-columns:auto 1fr;gap:2.2mm 5mm;margin:5mm 0 0;font-size:8.6pt;line-height:1.5}
dt{font-size:6pt;font-weight:500;letter-spacing:.3em;text-transform:uppercase;color:#8d857a;padding-top:.9mm;white-space:nowrap}
dd{margin:0;color:#e4dccf}
.grid{display:grid;gap:5mm}
figure{margin:0}
figure img{display:block;width:100%;aspect-ratio:9/16;border:.2mm solid #34302c}
figcaption{padding-top:2mm}
.k{display:flex;justify-content:space-between;align-items:baseline;font-size:6pt;letter-spacing:.14em;color:#8d857a;margin-bottom:1mm}
.k b{font-weight:500;color:#e0903f;font-size:7pt}
h3{margin:0 0 1.2mm;font-size:8pt;font-weight:500}
p{margin:0 0 1.1mm;font-size:6.6pt;line-height:1.42;color:#cfc6b8}
p i{color:#8d857a}
.opt .num{font-size:20pt;font-weight:300;color:#e0903f;line-height:1;margin-bottom:1mm}
.opt h3{font-size:9pt;letter-spacing:.06em}
.opt p{font-size:7.6pt}
.pano small{display:block;font-size:6pt;font-weight:500;letter-spacing:.3em;text-transform:uppercase;color:#8d857a;margin-bottom:2mm}
.pano img{display:block;width:100%;aspect-ratio:2700/708;border:.2mm solid #34302c}
.cover em{font-size:13pt}
.thumbs{display:grid;grid-template-columns:repeat(6,1fr);gap:3mm;margin:9mm 0 8mm}
.thumbs img{width:100%;aspect-ratio:9/16;display:block;border:.2mm solid #34302c}
.cover h2{margin:6mm 0 2mm;font-size:7pt;font-weight:500;letter-spacing:.3em;text-transform:uppercase;color:#e0903f}
table{width:100%;border-collapse:collapse;font-size:8.4pt}
td{padding:2.2mm 0;border-top:.2mm solid #2c2825;vertical-align:top;color:#cfc6b8;line-height:1.4}
td.nm{width:52mm;color:#efe7da;font-weight:500;padding-right:4mm}
td.pg{width:12mm;text-align:right;color:#e0903f}
.note{margin-top:8mm;font-size:7.6pt;color:#8d857a;max-width:150mm}
.ba{display:grid;grid-template-columns:38mm 38mm 1fr;gap:5mm;margin:8mm 0 2mm;align-items:start}
.ba h3{font-size:7pt;letter-spacing:.2em;text-transform:uppercase;color:#8d857a}
.chg h2{margin:0 0 2mm}
.chg ol{margin:0;padding-left:4.5mm;font-size:8pt;line-height:1.45;color:#cfc6b8}
.chg li{margin-bottom:1.8mm}.chg b{color:#efe7da;font-weight:500}
.thumbs.nine{grid-template-columns:repeat(10,1fr);gap:2mm;margin:2mm 0 0}
.bigcap{gap:8mm;padding:0 3mm}
.bigcap h3{font-size:11pt;margin-bottom:1.6mm}
.bigcap p{font-size:8.4pt;line-height:1.45}
.bigcap .k{font-size:7.5pt}.bigcap .k b{font-size:10pt}
.todo{margin:7mm 0 0;padding-left:6mm;font-size:9.6pt;line-height:1.6;color:#cfc6b8}
.todo li{margin-bottom:4mm}.todo b{color:#efe7da;font-weight:500}
</style>
<div id="book"></div>
<div id="src">${CONTENT}</div>
<script>
window.paginate = () => {
  const book = document.getElementById('book');
  const blocks = [...document.getElementById('src').children];
  let body = null;
  const newPage = () => {
    const page = document.createElement('section'); page.className = 'page';
    body = document.createElement('div'); body.className = 'body';
    page.appendChild(body); page.appendChild(document.createElement('footer'));
    book.appendChild(page);
  };
  for (const b of blocks) {
    if (!body || b.classList.contains('start')) newPage();
    body.appendChild(b);
    if (body.scrollHeight > body.clientHeight + 1 && body.children.length > 1) { body.removeChild(b); newPage(); body.appendChild(b); }
  }
  const pages = [...document.querySelectorAll('.page')];
  pages.forEach((p, i) => { p.querySelector('footer').innerHTML = i ? '<span>Juanito Coffee · ' + (document.querySelector('.bigcap') ? 'idea F afinada' : 'ideas para el reel') + '</span><span>' + (i + 1) + ' / ' + pages.length + '</span>' : ''; });
  document.querySelectorAll('[data-goto]').forEach((td) => { td.textContent = 'p. ' + (pages.indexOf(document.getElementById(td.dataset.goto).closest('.page')) + 1); });
  const over = pages.map((p, i) => [i + 1, p.querySelector('.body')]).filter(([, b]) => b.scrollHeight > b.clientHeight + 1).map(([i]) => i);
  return { pages: pages.length, over };
};
</script>`;

const tmp = path.join(SB, 'pdf', '_book.html');
fs.writeFileSync(tmp, html);
const browser = await chromium.launch();
const pg = await browser.newPage();
await pg.goto(url(tmp), { waitUntil: 'load' });
await pg.evaluate(() => document.fonts.ready);
const info = await pg.evaluate(() => window.paginate());
await pg.pdf({ path: OUT, preferCSSPageSize: true, printBackground: true });
await browser.close();
fs.unlinkSync(tmp);
console.log(OUT, info);
