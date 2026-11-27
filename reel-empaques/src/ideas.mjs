// Textos de cada idea, compartidos por las laminas (sheets.mjs) y el PDF (pdf.mjs).
import fs from 'node:fs';
import path from 'node:path';

export const META = {
  a: {
    file: 'idea_a_galeria', n: 'Idea A', name: 'THE COLLECTION', sub: 'la galería',
    what: 'Los empaques nuevos se cuelgan como cuadros en una sala oscura, cada uno bajo su lámpara y con una ficha de museo que dice la variedad. Noah hace la visita guiada.',
    tone: 'Elegante y pausada. La más minimal de las tres.',
    noah: 'Seis de tus ilustraciones, sin redibujar. Noah es anfitrión: está quieto y cambia de pose en cada corte.',
    line: 'Galería oscura: los empaques cuelgan como cuadros y Noah hace la visita guiada.',
  },
  b: {
    file: 'idea_b_dog_not_included', n: 'Idea B', name: 'DOG NOT INCLUDED', sub: 'Noah opina',
    what: 'Cada empaque empieza con un primerísimo plano de su dibujo (cerezas, fiesta, mula, perro) y se abre hasta mostrar la bolsa completa con su variedad. Noah comenta cada uno y se pone celoso del perro pintado.',
    tone: 'Con humor y ritmo rápido. Remata con la frase de la marca.',
    noah: 'Seis de tus ilustraciones, sin redibujar. Noah se queda fijo abajo a la derecha y cambia de pose con cada comentario.',
    line: 'Primer plano del dibujo de cada empaque que se abre a la bolsa completa; Noah comenta.',
  },
  c: {
    file: 'idea_c_el_sueno', n: 'Idea C', name: "NOAH'S DREAM", sub: 'el sueño',
    what: 'Noah duerme y sueña con los cuatro empaques dentro de una burbuja. El perro pintado en el último lo despierta, y los empaques resultan ser de verdad.',
    tone: 'Tierna, un cuento corto con principio y final.',
    noah: 'Cinco de tus ilustraciones, sin redibujar. Como está dormido casi todo el video, no hace falta animarlo mucho.',
    line: 'Noah duerme y sueña con los cuatro empaques dentro de una burbuja.',
  },
  d: {
    file: 'idea_d_mezcla_pixel', n: 'Idea D · la mezcla', name: 'LIGHTS ON', sub: 'la ficha de color, en pixel art, que Noah enciende',
    what: 'Junta tus dos referencias. La ficha con el color de cada variedad, pero dibujada toda en pixel art. Empieza apagada; Noah ladra, cada ladrido pone una letra del nombre y al completarlo todo se enciende con el color del empaque.',
    tone: 'Animación de personaje: Noah hace que pasen las cosas. Cuatro encendidos, un color distinto cada vez.',
    noah: 'En estos borradores van tus ilustraciones como marcador. Aquí es donde entran las animaciones nuevas: caminar, ladrar, celebrar, mirar de reojo, dormirse.',
    line: 'La ficha de color de cada variedad, en pixel art, que Noah enciende con ladridos.',
  },
  e: {
    file: 'idea_e_recorrido', n: 'Idea E · el recorrido', name: 'FOLLOW NOAH', sub: 'Noah camina de empaque en empaque y termina en la tostadora',
    what: 'Un solo camino, de izquierda a derecha. Noah va caminando, se detiene en cada empaque y lo presenta; el color del fondo cambia con cada variedad. Al final llega a la tostadora.',
    tone: 'Un paseo. Los empaques son objetos de pixel art dentro del mundo de Noah, no la foto de la bolsa.',
    noah: 'Aquí Noah camina de verdad: la animación de caminar es la más importante. En el borrador van tus ilustraciones fijas y unas huellitas donde camina.',
    pano: 'idea_e_recorrido_panorama.png',
    line: 'Un camino plano: Noah va de empaque en empaque y termina en la tostadora.',
  },
  f: {
    file: 'idea_f_horizonte_de_cafe', n: 'Idea F · el horizonte de café', name: 'COFFEE HORIZON', sub: 'Noah camina sobre la curva de una taza de café',
    what: 'El horizonte curvo de tu referencia, pero es la superficie de una taza de café. Noah camina por encima y el mundo gira bajo él: los empaques van saliendo por el horizonte, el cielo cambia de color con cada variedad y flotan referencias a los sabores. Al final llega a la tostadora: los granos saltan, arman el logo en pixel art y el logo pasa a normal con "coming soon".',
    tone: 'Un paseo con atmósfera. Cada empaque trae su propio cielo y Noah reacciona con una expresión distinta.',
    noah: 'Noah camina en el sitio mientras el mundo gira; hace falta la animación de caminar y una expresión por empaque. En el borrador van tus ilustraciones fijas.',
    line: 'Noah camina sobre la curva de una taza de café; termina en la tostadora y el logo.',
  },
};

/** Cuadros de todas las ideas: frames.json (A-C) y frames_<idea>.json (D en adelante). */
export function loadFrames(FR) {
  const frames = JSON.parse(fs.readFileSync(path.join(FR, 'frames.json'), 'utf8'));
  for (const f of fs.readdirSync(FR).filter((n) => /^frames_[a-z]\.json$/.test(n)).sort()) {
    frames.push(...JSON.parse(fs.readFileSync(path.join(FR, f), 'utf8')));
  }
  return frames;
}
