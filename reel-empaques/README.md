# Reel — Juanito Coffee · nuevos empaques / café verde

Reel vertical (1080×1920, 24 fps, 23,5 s) en inglés, estilo píxel / dot‑matrix
inspirado en el reel de referencia. Todo se genera por código: animación
(`make_reel.py`) y banda sonora lo‑fi / chiptune (`make_audio.py`).

## Guion (en inglés, como sale en el video)

| Tiempo | Escena | Texto |
|---|---|---|
| 0,0–1,0 s | Estática de TV + logo | — |
| 1,0–4,0 s | Acuarela (cerezas y montañas) en píxel | (origin **HUILA** COLOMBIA) |
| 4,0–5,5 s | Coordenadas | HUILA, · 02°32′ N · 75°31′ W |
| 5,5–9,0 s | Acuarela (recolector) en píxel | **GROWN** (with love & respect for the land) · EVERY BEAN THAT REACHES YOUR CUP TELLS OUR STORY |
| 9,0–13,5 s | Grano de café girando en píxeles | (coming soon) NEW VARIETIES · **JAVA · CASTILLO · GEISHA · BOURBON** · FOUR VARIETIES · ONE ORIGIN |
| 13,5–17,5 s | Empaques nuevos (se “despixelan”) | **NEW PACKAGING** (a new look for a new harvest) |
| 17,5–19,5 s | Acuarelas con mula | FROM OUR **MOUNTAINS** → TO YOUR **ROASTERY** |
| 19,5–23,5 s | Logo + cierre | NEW LOOK · NEW HARVEST · **GREEN COFFEE** (samples & pricing via DM) · @JUANITOCOFFEE |

No se usa ningún dato técnico de los empaques (altura, región, variedad,
receta, etc.); solo se muestran los frentes, sin texto de ficha técnica.
Las coordenadas son las del departamento del Huila; se pueden cambiar por
las de la finca en `fx.py`/`make_reel.py` (`build_hud`, `scene_coords`).

## Cómo regenerar

Las imágenes (acuarelas, empaques, logo) **no están en el repositorio**
porque es público. Hay que ponerlas en `assets/` con estos nombres:

```
assets/wc_cherries.jpg      acuarela cerezas + montañas
assets/wc_picker.jpg        acuarela recolector
assets/wc_mule_dog.jpg      acuarela mula + perro + casa roja
assets/wc_mule_blue.jpg     acuarela mula + ventana azul
assets/pack_color_front.png frente del empaque de colores
assets/pack_dark_front.jpg  frente del empaque oscuro
assets/logo_white.png       logo oficial en blanco con transparencia
```

Fuente Montserrat (OFL) desde npm:

```
npm pack @fontsource/montserrat@5.0.19 && tar xzf fontsource-montserrat-*.tgz
mkdir -p fonts && cp package/files/montserrat-latin-*-{normal,italic}.woff fonts/
```

Luego:

```
pip install numpy pillow scipy
python3 make_reel.py --stills 3,7,12   # vistas previas en build/
python3 make_reel.py                   # build/reel_silent.mp4
python3 make_audio.py                  # build/soundtrack.wav
ffmpeg -i build/reel_silent.mp4 -i build/soundtrack.wav -c:v copy -c:a aac -b:a 192k -shortest build/juanito_reel.mp4
```
