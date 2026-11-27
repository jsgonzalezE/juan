// Arma una lamina por idea (cuadros + notas) a partir de storyboards/frames.
// Uso: node src/sheets.mjs   -> storyboards/idea_a_galeria.jpg, idea_b_..., idea_c_...
import { createRequire } from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const { chromium } = createRequire(import.meta.url)('playwright');
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const FR = path.join(ROOT, 'storyboards', 'frames');
const frames = JSON.parse(fs.readFileSync(path.join(FR, 'frames.json'), 'utf8'));
for (const f of ['frames_d.json', 'frames_e.json', 'frames_f.json', 'frames_g.json']) { // ideas D y E: las generan pixel_mix.py y pixel_walk.py
  const extra = path.join(FR, f);
  if (fs.existsSync(extra)) frames.push(...JSON.parse(fs.readFileSync(extra, 'utf8')));
}
const url = (p) => pathToFileURL(p).href;
const font = (w, s) => url(path.join(ROOT, 'node_modules/@fontsource/montserrat/files', `montserrat-latin-${w}-${s}.woff2`));

const META = {
  a: {
    file: 'idea_a_galeria', n: 'Idea A', name: 'THE COLLECTION', sub: 'la galería',
    what: 'Los empaques nuevos se cuelgan como cuadros en una sala oscura, cada uno bajo su lámpara y con una ficha de museo que dice la variedad. Noah hace la visita guiada.',
    tone: 'Elegante y pausada. La más minimal de las tres.',
    noah: 'Seis de tus ilustraciones, sin redibujar. Noah es anfitrión: está quieto y cambia de pose en cada corte.',
  },
  b: {
    file: 'idea_b_dog_not_included', n: 'Idea B', name: 'DOG NOT INCLUDED', sub: 'Noah opina',
    what: 'Cada empaque empieza con un primerísimo plano de su dibujo (cerezas, fiesta, mula, perro) y se abre hasta mostrar la bolsa completa con su variedad. Noah comenta cada uno y se pone celoso del perro pintado.',
    tone: 'Con humor y ritmo rápido. Remata con la frase de la marca.',
    noah: 'Seis de tus ilustraciones, sin redibujar. Noah se queda fijo abajo a la derecha y cambia de pose con cada comentario.',
  },
  c: {
    file: 'idea_c_el_sueno', n: 'Idea C', name: "NOAH'S DREAM", sub: 'el sueño',
    what: 'Noah duerme y sueña con los cuatro empaques dentro de una burbuja. El perro pintado en el último lo despierta, y los empaques resultan ser de verdad.',
    tone: 'Tierna, un cuento corto con principio y final.',
    noah: 'Cinco de tus ilustraciones, sin redibujar. Como está dormido casi todo el video, no hace falta animarlo mucho.',
  },
};

META.d = {
  file: 'idea_d_mezcla_pixel', n: 'Idea D · la mezcla', name: 'LIGHTS ON', sub: 'la ficha de color, en pixel art, que Noah enciende',
  what: 'Junta tus dos referencias. La ficha con el color de cada variedad, pero dibujada toda en pixel art. Empieza apagada; Noah ladra, cada ladrido pone una letra del nombre y al completarlo todo se enciende con el color del empaque.',
  tone: 'Animación de personaje: Noah hace que pasen las cosas. Cuatro encendidos, un color distinto cada vez.',
  noah: 'En estos borradores van tus ilustraciones como marcador. Aquí es donde entran las animaciones nuevas: caminar, ladrar, celebrar, mirar de reojo, dormirse.',
};
META.e = {
  file: 'idea_e_recorrido', n: 'Idea E · el recorrido', name: 'FOLLOW NOAH', sub: 'Noah camina de empaque en empaque y termina en la tostadora',
  what: 'Un solo camino, de izquierda a derecha. Noah va caminando, se detiene en cada empaque y lo presenta; el color del fondo cambia con cada variedad. Al final llega a la tostadora.',
  tone: 'Un paseo. Los empaques son objetos de pixel art dentro del mundo de Noah, no la foto de la bolsa.',
  noah: 'Aquí Noah camina de verdad: la animación de caminar es la más importante. En el borrador van tus ilustraciones fijas y unas huellitas donde camina.',
  pano: 'idea_e_recorrido_panorama.png',
};
META.f = {
  file: 'idea_f_horizonte_de_cafe', n: 'Idea F · el horizonte de café', name: 'COFFEE HORIZON', sub: 'Noah camina sobre la curva de una taza de café',
  what: 'El horizonte curvo de tu referencia, pero es la superficie de una taza de café. Noah camina por encima y el mundo gira bajo él: los empaques van saliendo por el horizonte, el cielo cambia de color con cada variedad y flotan referencias a los sabores. Al final llega a la tostadora: los granos saltan, arman el logo en pixel art y el logo pasa a normal con "coming soon".',
  tone: 'Un paseo con atmósfera. Cada empaque trae su propio cielo y Noah reacciona con una expresión distinta.',
  noah: 'Noah camina en el sitio mientras el mundo gira; hace falta la animación de caminar y una expresión por empaque. En el borrador van tus ilustraciones fijas.',
};
META.g = {
  file: 'idea_g_viaje_por_los_mundos', n: 'Idea G · el viaje', name: 'FOUR WORLDS', sub: 'cada empaque es un mundo y Noah los recorre',
  what: 'No se muestran las bolsas: cada empaque se vuelve un mundo, hecho con su propio dibujo en pixel art y con su ambiente. Noah viaja de uno a otro y cada entrada es distinta: el capuchino, un portal de café, una marea de café, una puerta. Al final llega a la tostadora, suena el primer "crack" y avisa que ya casi está listo.',
  tone: 'Un viaje. Cuatro ambientes muy distintos entre sí y un final corto y limpio con el logo.',
  noah: 'Camina dentro de cada mundo y hace una expresión distinta en cada uno. En el borrador van tus ilustraciones fijas.',
};
const ONLY = process.argv[2];

const TW = 320; // ancho de cada cuadro en la lamina
const sheet = (id) => {
  const m = META[id];
  const fs_ = frames.filter((f) => f.idea === id);
  const cols = fs_.length > 8 ? Math.ceil(fs_.length / 2) : fs_.length;
  const cells = fs_.map((f) => `
    <figure>
      <img src="${url(path.join(FR, `${f.id}.png`))}">
      <figcaption>
        <div class="k"><b>${f.n}</b><span>${f.t}</span></div>
        <h3>${f.title}</h3>
        <p>${f.es}</p>
        <p class="tx"><i>En pantalla:</i> ${f.text}</p>
        <p class="sn"><i>Sonido:</i> ${f.snd}</p>
      </figcaption>
    </figure>`).join('');
  return `<!doctype html><meta charset="utf-8"><style>
@font-face{font-family:M;font-weight:300;src:url(${font(300, 'normal')})}
@font-face{font-family:M;font-weight:300;font-style:italic;src:url(${font(300, 'italic')})}
@font-face{font-family:M;font-weight:400;src:url(${font(400, 'normal')})}
@font-face{font-family:M;font-weight:400;font-style:italic;src:url(${font(400, 'italic')})}
@font-face{font-family:M;font-weight:500;src:url(${font(500, 'normal')})}
*{box-sizing:border-box}
html,body{margin:0;background:#171513}
#s{width:${cols * (TW + 24) + 56}px;padding:44px 40px 40px;font-family:M,sans-serif;color:#efe7da;background:#171513}
header{display:flex;gap:56px;align-items:flex-start;margin-bottom:34px}
.id{flex:0 0 auto}
.id small{display:block;font-size:15px;font-weight:500;letter-spacing:.4em;text-transform:uppercase;color:#e0903f;margin-bottom:12px}
.id h1{margin:0;font-size:44px;font-weight:300;letter-spacing:.16em;line-height:1.1;white-space:nowrap}
.id em{display:block;margin-top:10px;font-size:22px;font-weight:300;color:#cfc6b8}
.desc{display:grid;grid-template-columns:auto 1fr;gap:9px 18px;font-size:17px;line-height:1.5;max-width:1150px;padding-top:4px}
.desc dt{font-size:12px;font-weight:500;letter-spacing:.3em;text-transform:uppercase;color:#8d857a;padding-top:5px;white-space:nowrap}
.desc dd{margin:0;font-weight:400;color:#e4dccf}
.pano{margin:0 0 26px}.pano small{display:block;font-size:12px;font-weight:500;letter-spacing:.3em;text-transform:uppercase;color:#8d857a;margin-bottom:12px}.pano img{display:block;width:100%;border:1px solid #33302c;image-rendering:pixelated}
main{display:grid;grid-template-columns:repeat(${cols},${TW}px);gap:30px 24px}
figure{margin:0}
figure img{display:block;width:${TW}px;height:${Math.round(TW * 16 / 9)}px;border:1px solid #33302c}
.k{display:flex;justify-content:space-between;align-items:baseline;margin:12px 0 5px;font-size:13px;letter-spacing:.14em;color:#8d857a}
.k b{font-weight:500;color:#e0903f;font-size:14px}
h3{margin:0 0 6px;font-size:17px;font-weight:500;letter-spacing:.01em}
p{margin:0 0 6px;font-size:13.5px;line-height:1.45;font-weight:400;color:#cfc6b8}
p i{color:#8d857a}
</style><div id="s">
<header>
  <div class="id"><small>${m.n} · ${fs_.length} cuadros · 20 s</small><h1>${m.name}</h1><em>(${m.sub})</em></div>
  <dl class="desc"><dt>La idea</dt><dd>${m.what}</dd><dt>Tono</dt><dd>${m.tone}</dd><dt>Noah</dt><dd>${m.noah}</dd></dl>
</header>
${m.pano ? `<div class="pano"><small>El recorrido completo, de un vistazo</small><img src="${url(path.join(ROOT, 'storyboards', m.pano))}"></div><div class="pano"><small>Lo que ve el celular en cada parada</small></div>` : ''}
<main>${cells}</main></div>`;
};

const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 2600, height: 1400 }, deviceScaleFactor: 2 });
const pg = await ctx.newPage();
for (const id of Object.keys(META)) {
  if (ONLY && id !== ONLY) continue;
  if (!frames.some((f) => f.idea === id)) continue;
  const tmp = path.join(FR, `_sheet_${id}.html`);
  fs.writeFileSync(tmp, sheet(id));
  await pg.goto(url(tmp));
  await pg.evaluate(() => document.fonts.ready);
  const out = path.join(ROOT, 'storyboards', `${META[id].file}.jpg`);
  await pg.locator('#s').screenshot({ path: out, type: 'jpeg', quality: 90 });
  fs.unlinkSync(tmp);
  console.log(out);
}
await browser.close();
