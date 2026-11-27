# Teasers — Juanito Coffee · nuevos empaques / nueva cosecha

Tres versiones de teaser vertical (1080×1920, 24 fps) en inglés para escoger la
dirección. En todas los empaques aparecen **solo en pixel art** (nunca la
imagen limpia), se mencionan las variedades **Java, Castillo, Geisha y
Bourbon**, el origen **Huila, Colombia** y el cierre es **Green coffee · Coming
soon · @juanitocoffee** con el logo oficial. No se usan datos de los empaques
ni la foto de los dueños.

| Versión | Duración | Estilo |
|---|---|---|
| `v1_noir.py` | 18 s | Fondo oscuro, elegante. El empaque se arma con puntos que vuelan y gira en 3D; macro del empaque con HUILA; cada variedad en pantalla completa con su color; los dos empaques girando; logo. |
| `v2_pop.py` | 16 s | Fondo gris claro, tipografía gruesa vino. El empaque se construye con bloques que caen; lista de variedades con cuadritos de color; el empaque oscuro aparece en ola; logo vino. |
| `v3_grid.py` | 15 s | Fondo gris oscuro, cuadrícula de 3×4. Las piezas del empaque aparecen revueltas y se ordenan como rompecabezas; los cuadros giran al ritmo para mostrar variedades, origen y el empaque oscuro; cierre en vino con el logo. |

### "Noah's shift" — con el Noah en pixel art de la marca (dirección actual)

`t2_noah.py` (22 s) + `t2_audio.py`. Noah no se redibuja ni se calca: `pixref.py` recorta del fondo
blanco las ilustraciones en pixel art de la marca (`assets/noah_pix/*.png`: `sack`, `roaster`,
`cupping`, `barista`, `sugar`, `mug`, …), les pone un borde crema para que se lean sobre negro y
separa los acentos sueltos (chispas, rayitas) para que parpadeen.

Historia: Noah sale de un saco de café verde *(origin HUILA COLOMBIA)* → oye el primer crack
*(first crack? I heard it first.)* → control de calidad con las cuatro variedades
*JAVA · CASTILLO · GEISHA · BOURBON* → de barista presenta los cuatro empaques reales
*(a new look)* → en el cuarto ve al perro pintado *(...who's HE?) (dog included.)* → los cuatro
empaques, *New look? Noah approved.* → logo, *COMING SOON*, *green coffee · Huila, Colombia*,
@juanitocoffee. Noah rebota al ritmo; los empaques se materializan desde píxeles.

```
python3 t2_noah.py --cues && python3 t2_noah.py          # video sin sonido
/ruta/al/venv/de/earshot/bin/python t2_audio.py          # build/t2_noah.wav (efectos en build/sfx)
ffmpeg -i build/t2_noah_silent.mp4 -i build/t2_noah.wav -c:v libx264 -crf 20 -pix_fmt yuv420p \
  -c:a aac -b:a 192k -shortest build/t2_noah.mp4
```

### "The Sniff Test" — Noah dibujado a mano (descartado: no se parecía a Noah)

`t1_sniff_test.py` (23 s) + `t1_audio.py`. Noah ya no se genera calcando los dibujos: es un sprite
de pixel art hecho a mano (`assets/noah_px/final/front_sit.txt`, 56×64; se dibujaron cuatro
propuestas y un jurado eligió y corrigió la mejor contra los dibujos de la marca).

- `px.py`: formato de sprite en texto (un carácter por píxel), paleta pensada para fondo negro y
  herramientas (`render`, `check`, `strip`, `onion`, `anim`).
- `rig.py`: "esqueleto" de Noah sentado: ojos (abiertos, entrecerrados, cerrados, felices, mirando
  a los lados, sorprendidos, serios), boca (lengua, cerrada, seria, jadeo), nariz que olfatea,
  orejas que se levantan, copete que rebota, cabeza que se inclina, pata arriba y cola.
- `props.py`: saco de yute con café verde, patas sobre el borde y sello de huella.
- `stage.py`: empaques reales que se materializan desde píxeles, partículas y saltos.

Historia: un saco de café verde de Huila se mueve → Noah se asoma, olfatea y salta → el saco se
vuelve píxeles y se convierte en el primer empaque → Noah olfatea y sella con la pata
*(new look: approved)*, *(approved)*, *(muy approved)* → en el cuarto ve al perro pintado:
*(...who's HE?)*, primer plano serio, *(not jealous.)*, *(...approved.)* y *(dog included.)* →
los cuatro empaques con *(four new varieties) JAVA · CASTILLO · GEISHA · BOURBON* y
*New look? I sniffed it first.* → logo, *COMING SOON*, *green coffee · Huila, Colombia*,
@juanitocoffee.

Sonido: cama lo-fi por código (`audio.py`) y efectos generados con
[earshot](https://github.com/Leonxlnx/earshot) (`earshot make`), colocados en los tiempos de
`build/t1_sniff_test_cues.json` y revisados con `earshot timeline` (volumen −15,7 LUFS, sin cortes
sin sonido). Para regenerar:

```
python3 t1_sniff_test.py --cues && python3 t1_sniff_test.py      # video sin sonido
# efectos: ver la lista de `earshot make --sound ...` en t1_audio.py (carpeta build/sfx)
/ruta/al/venv/de/earshot/bin/python t1_audio.py                  # build/t1_sniff_test.wav
ffmpeg -i build/t1_sniff_test_silent.mp4 -i build/t1_sniff_test.wav -c:v libx264 -crf 20 \
  -pix_fmt yuv420p -c:a aac -b:a 192k -shortest build/t1_sniff_test.mp4
```

### Noah en pixel art (versiones anteriores)

Noah se convierte a pixel art a partir de los dibujos de la marca (`noah.py`: recorta cada pose,
la reduce a una cuadrícula pequeña, separa líneas y manchas negras y rellena el blanco). Los
empaques se muestran en color (`noah.pack_sprite`); se deja fuera la bolsa más verde (recolector).
Dibujos en `assets/noah/` (`vibes.png`, `roaster.jpg`, `mug.jpg`, `gift.jpg`, `cap.jpg`).

| Versión | Duración | Idea |
|---|---|---|
| `n1_noah_presents.py` | 20,5 s | Fondo oscuro con objetos en puntos grises. Noah entra saltando, sube a los sacos y arma letra por letra *NEW LOOK* en el letrero, que se enciende; luego cada empaque sube desde detrás de un pedestal y Noah se asoma a presentarlo (Look 01–04); en el letrero pasan las variedades mientras Noah está en su taza; final con los 4 empaques, Noah asomándose, *COMING SOON*, logo y @juanitocoffee. |
| `n3_noah_v2.py` | 21 s | **Versión refinada.** Mismo guion que n1, pero Noah usa `noah.sprite2` (más resolución, borde crema tipo sticker para que la silueta se lea sobre negro, orejas en gris cálido, lengua rosada, taza en vino) y los empaques son las fotos reales recortadas (`noah.pack_photo`) que se materializan desde píxeles grandes con un halo suave. Noah inclina la cabeza al presentar, parpadea al final y sale vapor de su taza. |
| `n2_horizons.py` | 17 s | Cada empaque es un planeta en pixel art con su horizonte curvo y un Noah diminuto caminando encima; una taza de café como horizonte con Noah asomándose; noche estrellada con las variedades; cierre con *Juanito Coffee* sobre el horizonte. |

### Estilo de la referencia con las 5 bolsas reales

`r2_pouches.py` (17 s): mismas reglas que `r1_reference.py` pero con las cinco bolsas reales
(cuatro acuarelas + la de colores) como objetos 3D en puntos naranjas. Necesita en `assets/`:
`pouch_cherries.png`, `pouch_picker.png`, `pouch_color.png`, `pouch_mule.png`, `pouch_dog.png`
(recortes de los mockups). Bolsa de cerezas con *(origin HUILA COLOMBIA)* → coordenadas →
follaje gris de la acuarela con *LOVE* → manchas → bolsa de la casa azul con las variedades →
las cinco bolsas en cortes rápidos con *A NEW LOOK* → las cinco en fila, logo y cinta.

### Estilo del video de referencia

`r1_reference.py` (15 s): puntos finos de un solo color con tramado Floyd–Steinberg (la textura
de rayitas de la referencia); los empaques son bolsas 3D iluminadas que giran como el grano de la
referencia (el de colores en naranja, el oscuro en gris). Estática → empaque girando con
*(origin HUILA COLOMBIA)* → coordenadas → *FROM OUR LAND* → follaje gris del diseño con
*(grown with) LOVE (& respect for the land)* → manchas naranjas → empaque oscuro con las
variedades alrededor → *A NEW LOOK (coming soon)* → cierre con los dos empaques, logo y cinta.
Helpers en `refstyle.py`.

### Presentación de los empaques

| Versión | Duración | Idea |
|---|---|---|
| `p1_turntable.py` | 16 s | Fondo oscuro. El empaque se “imprime” en píxeles desde una línea de piso y gira como producto en vitrina, con reflejo; pasan las variedades; luego los dos empaques juntos mirándose; logo. |
| `p2_lookbook.py` | 16 s | Fondo gris claro, estilo catálogo. Look 01 y Look 02 entran en pixel art grande con sombra; luego los dos juntos con las variedades y el origen; logo. |

### Versiones minimalistas (más cerca del video de referencia)

| Versión | Duración | Idea |
|---|---|---|
| `m1_still_life.py` | 15 s | Un solo objeto en puntos naranjas sobre negro que va cambiando: la flor y las cerezas recortadas de la acuarela, un grano girando mientras aparecen las variedades una por una, el empaque apenas insinuado girando *(and a new look)* y el logo. |
| `m3_combo.py` | 16 s | **Combinación (dirección elegida).** La franja de m2 es el hilo: muestra fragmentos del empaque, se cierra en una línea-horizonte donde florece la flor de m1, se abre con las montañas (Huila), el grano gira frente a una franja fina del empaque oscuro mientras pasan las variedades, *(almost)* y logo. |
| `m2_glimpse.py` | 15 s | Los empaques solo se ven por una franja delgada que se desplaza; en medio aparecen Huila y las variedades; casi al final la franja se abre un poco *(almost)* y se cierra antes del logo. |

Cada script genera su propia música (lo‑fi / chiptune, 120 BPM) con `audio.py`.

## Cómo regenerar

Las imágenes **no están en el repositorio** (es público). Van en `assets/`:
`pack_color_front.png`, `pack_dark_front.jpg`, `logo_white.png`,
`wc_cherries.jpg`, `wc_picker.jpg`, `wc_mule_dog.jpg`.

Fuentes (OFL) desde npm, copiadas a `fonts/`: `@fontsource/montserrat@5.0.19`
(`montserrat-latin-*-{normal,italic}.woff`) y `@fontsource/pixelify-sans`.

```
pip install numpy pillow scipy
python3 v1_noir.py --stills 2,5,9    # vistas previas en build/
python3 v1_noir.py                   # build/v1_noir.mp4 (con música)
python3 v2_pop.py
python3 v3_grid.py
```
