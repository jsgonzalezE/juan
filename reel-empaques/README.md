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
