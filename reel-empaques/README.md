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

### Estilo de la referencia con las 5 bolsas reales (dirección actual)

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
