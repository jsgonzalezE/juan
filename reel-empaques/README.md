# Teaser — Juanito Coffee · nueva cosecha / café verde

Teaser vertical (1080×1920, 24 fps, 24 s) en inglés, en pixel art. No muestra
los empaques reales (solo una bolsa “bloqueada” con píxeles revueltos) ni a
ninguna persona: las acuarelas se recortan para dejar solo paisaje, casa y
cerezas. Todo se genera por código: animación (`make_reel.py`, `sprites.py`,
`fx.py`) y banda sonora lo‑fi / chiptune (`make_audio.py`).

## Guion

Abajo corre una barra de “viaje” con íconos que se van encendiendo:
BLOOM → ORIGIN → CHERRY → VARIETIES → CUP → PACKAGING.

| Tiempo | Escena | Texto |
|---|---|---|
| 0–2 s | Una flor de café se abre en píxeles | SOMETHING IS BLOOMING *(in Huila, Colombia)* |
| 2–4 s | Campo de flores que brotan | NEW HARVEST · COMING SOON |
| 4–7 s | Tres franjas de acuarela en píxel (montañas, casa, cerezas) | ORIGIN · **HUILA** · COLOMBIA 02°32′N 75°31′W |
| 7–9,5 s | Rama con cerezas que maduran de verde a rojo | FROM FLOWER → TO CHERRY *(ripening in the mountains of Huila)* |
| 9,5–13,5 s | Cuatro tarjetas con granos verdes | NEW VARIETIES *(coming soon)* · **JAVA · CASTILLO · GEISHA · BOURBON** · ONE ORIGIN · HUILA |
| 13,5–16 s | Granos verdes cayendo en una taza con vapor | YOUR NEXT FAVORITE CUP *(every bean tells a story)* |
| 16–19,5 s | Bolsa bloqueada con candado + barra de carga al 87 % | NEW PACKAGING *(we can't show it yet...)* · ALMOST READY... |
| 19,5–24 s | Logo oficial armándose con puntos + flores | GREEN COFFEE · FROM HUILA, COLOMBIA · COMING SOON · @JUANITOCOFFEE |

Los cortes se tapan con un barrido de píxeles naranja/magenta/vino.

## Cómo regenerar

Las imágenes **no están en el repositorio** (es público). Van en `assets/`:

```
assets/wc_cherries.jpg      acuarela cerezas + montañas
assets/wc_picker.jpg        acuarela recolector (solo se usa la parte de montañas)
assets/wc_mule_dog.jpg      acuarela casa roja (solo se usa la casa)
assets/logo_white.png       logo oficial en blanco con transparencia
```

Fuentes (OFL) desde npm, copiadas a `fonts/`:

```
npm pack @fontsource/montserrat@5.0.19 @fontsource/pixelify-sans
# extraer y copiar montserrat-latin-*-{normal,italic}.woff y pixelify-sans-latin-*-normal.woff
```

Luego:

```
pip install numpy pillow scipy
python3 make_reel.py --stills 1,5,8   # vistas previas en build/
python3 make_reel.py                  # build/reel_silent.mp4
python3 make_audio.py                 # build/soundtrack.wav
ffmpeg -i build/reel_silent.mp4 -i build/soundtrack.wav -c:v libx264 -crf 20 -maxrate 10M \
  -bufsize 20M -pix_fmt yuv420p -c:a aac -b:a 192k -shortest build/juanito_teaser.mp4
```
