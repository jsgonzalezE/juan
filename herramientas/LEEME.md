# Extractor de Informe — guía de uso

Esta herramienta toma un **vídeo** en el que se ve un documento o una presentación
(por ejemplo el *Informe Coffee Business*) y te devuelve:

| Archivo | Qué es |
|---|---|
| `informe.pdf` | **El documento reconstruido.** Todas las páginas, en orden. Esto es lo que normalmente querrás abrir. |
| `pagina_001.jpg`, `pagina_002.jpg`, … | Cada página por separado, en la calidad original del vídeo. |
| `audio.mp3` | La narración completa, sin imagen. |
| `resumen.txt` | Una lista legible: qué página aparece en qué minuto del vídeo. |
| `manifest.json` | Los mismos datos, en formato para programas. |

> Si una página **se ve varias veces** en el vídeo (por ejemplo una diapositiva de
> resumen que se repite), el PDF la incluye **una sola vez** —es un documento, no
> una grabación—, pero `resumen.txt` y `manifest.json` anotan **todos** los
> momentos en que aparece, bajo *"vuelve a verse en: …"*.

---

## 1. Antes de empezar

Necesitas dos cosas instaladas: **Python 3** y **ffmpeg**.

Para comprobar si ya los tienes, abre la Terminal y escribe:

```bash
python3 --version
ffmpeg -version
```

Si alguno responde *"command not found"*, instálalo:

```bash
# macOS (con Homebrew)
brew install python ffmpeg

# Linux (Ubuntu / Debian)
sudo apt install python3 python3-pip ffmpeg
```

Y luego, una sola vez, instala los complementos que usa la herramienta:

```bash
pip3 install numpy pillow imagehash img2pdf
```

---

## 2. Uso normal (lo que necesitas el 95% de las veces)

Copia esta línea, cambiando `informe.mp4` por el nombre de tu vídeo:

```bash
python3 extraer_informe.py informe.mp4
```

Todo aparecerá en una carpeta nueva llamada **`informe_extraido`**, junto al sitio
desde donde ejecutaste el comando.

> **Truco:** si no quieres escribir la ruta del vídeo a mano, escribe
> `python3 extraer_informe.py ` (con el espacio final) y luego **arrastra el archivo
> de vídeo** a la ventana de la Terminal. La ruta se escribe sola.

Mientras trabaja te irá contando lo que hace, en español:

```
[1/7] Revisando el video...
      Duracion: 00:42:18   Resolucion: 1920x1080   Codec: h264
      Pista de audio: si
[2/7] Buscando bandas negras y bordes que sobran...
      Se recortara a 1664x1040 (quitando 256 px de ancho y 40 de alto).
[3/7] Analizando el video a 4 imagenes/s (una sola pasada)...
[4/7] Localizando webcam, cursor, reloj y otras zonas que se mueven...
[5/7] Detectando los cambios de pagina...
[6/7] Extrayendo cada pagina en calidad original...
[7/7] Armando el PDF, el audio y el resumen...

  LISTO en 00:01:24  (30.3 veces mas rapido que el video)
```

Un vídeo de una hora tarda unos **2–4 minutos**.

---

## 3. Guardar el resultado en otro sitio

```bash
python3 extraer_informe.py informe.mp4 --salida ~/Escritorio/informe_semana_12
```

---

## 4. Si el resultado no es el que esperabas

Solo hay un mando que tocar: **`--sensibilidad`**, un número del **1 al 10**
(por defecto **5**).

### Faltan páginas

Sube la sensibilidad. Saldrán más páginas; algunas estarán repetidas, pero
podrás borrar las que sobren con dos clics.

```bash
python3 extraer_informe.py informe.mp4 --sensibilidad 8
```

### Salen demasiadas páginas repetidas

Lo más seguro es **borrarlas a mano**: son archivos `pagina_XXX.jpg` sueltos, y
el PDF se puede rehacer con los que queden. Si prefieres que la herramienta
agrupe más, baja la sensibilidad **como mucho a 4**:

```bash
python3 extraer_informe.py informe.mp4 --sensibilidad 4
```

> ⚠️ **Bajar la sensibilidad tiene un coste.** Cuanto más la bajes, más se
> agrupan las imágenes parecidas, y dos páginas que compartan cabecera y pie
> pueden acabar contadas como una sola. El valor de fábrica (**5**) es el que
> está comprobado. La herramienta te avisa por pantalla si pides menos de 4.
>
> Compara siempre el número de páginas de `informe.pdf` con las que esperabas
> del informe original antes de dar el trabajo por bueno.

### Alguna página aparece muy poco tiempo en pantalla

Analiza más imágenes por segundo (por defecto son 4). Tarda más, pero no se
escapa nada:

```bash
python3 extraer_informe.py informe.mp4 --fps 8
```

### Solo quieres el audio, o solo las páginas

```bash
# no extraer el MP3 (más rápido)
python3 extraer_informe.py informe.mp4 --sin-audio
```

> **Regla práctica:** es mucho mejor que sobre una página repetida a que falte
> una. La herramienta está ajustada así a propósito. Si dudas, usa
> `--sensibilidad 8` y borra a mano las repetidas.

---

## 5. Todas las opciones

```
python3 extraer_informe.py <video> [--salida DIR] [--sensibilidad N]
                                   [--sin-audio] [--fps N] [--debug]
```

| Opción | Para qué sirve | Por defecto |
|---|---|---|
| `--salida DIR` | Carpeta donde dejar los resultados | `./informe_extraido` |
| `--sensibilidad N` | 1 a 10. Más alto = más capturas (y más repetidas); más bajo = menos repeticiones, pero con riesgo de agrupar dos páginas parecidas | `5` |
| `--sin-audio` | No generar `audio.mp3` | desactivado |
| `--fps N` | Imágenes por segundo que se analizan | `4` |
| `--debug` | Mensajes técnicos y conserva los archivos temporales | desactivado |

---

## 6. Qué hace por dentro (resumen sencillo)

- **Quita las bandas negras** de los lados y de arriba/abajo automáticamente.
- **Ignora la webcam, el cursor del ratón, el reloj y la barra de progreso**: los
  detecta solo, viendo qué zonas se mueven *mientras la página está quieta*, y
  deja de mirarlas. Así una cara que habla en una esquina no se confunde con un
  cambio de página.
- **Evita los fotogramas borrosos de las transiciones.** Durante un fundido o un
  barrido la imagen es una mezcla de dos páginas; la herramienta detecta ese
  momento y guarda la página ya asentada, no la mezcla.
- **Detecta cambios pequeños**, como una sola barra de un gráfico que cambia de
  altura, que un método basado solo en "cuánto cambió la imagen entera" no vería.
- **Cubre el scroll**: si en vez de cambiar de página se hace scroll por un
  documento largo, va guardando capturas para no perder contenido.
- **Guarda las páginas en la calidad original**, no en la reducida que usa para
  analizar, así que el PDF sale nítido.

---

## 7. Problemas frecuentes

**"no se encuentra 'ffmpeg' en el sistema"**
No está instalado. Mira el paso 1.

**"no existe el archivo: ..."**
La ruta está mal escrita. Usa el truco de arrastrar el archivo a la Terminal.

**"el archivo esta vacio (0 bytes)" / "no se pudo leer el video"**
El vídeo se descargó a medias o está dañado. Vuelve a descargarlo.

**"este video NO tiene pista de audio; se omite audio.mp3"**
No es un error: el vídeo no lleva sonido. Las páginas y el PDF sí se generan.

**El PDF tiene páginas repetidas**
Normal y buscado (mejor que sobren a que falten). Bórralas desde cualquier
visor de PDF, o borra los `pagina_XXX.jpg` que sobren. Bajar la sensibilidad
también funciona, pero lee el aviso del punto 4 antes de hacerlo.

**Falta una página que sé que estaba**
Prueba `--sensibilidad 8`, y si sigue faltando, `--sensibilidad 10 --fps 8`.

---

## 8. Límites conocidos (con honestidad)

- Si el presentador **hace zoom** sobre una página y se detiene, esa vista
  ampliada se guarda como una página más. Es a propósito: preferimos que sobre.
- Si una zona del documento está **siempre tapada por la webcam**, un cambio que
  ocurra justo ahí no se puede detectar.
- Con un **scroll continuo que no se detiene nunca**, se toman capturas cada
  pocos segundos. Se cubre el contenido, pero pueden salir vistas solapadas.
- Dos páginas **idénticas salvo un dato muy pequeño** (una cifra en una tabla)
  pueden fundirse en una sola si el vídeo está muy comprimido. Sube la
  sensibilidad si sospechas que pasa.
- El recorte de bandas negras es **conservador**: si la webcam o un reloj tocan
  el borde de la imagen, prefiere no recortar antes que cortar contenido.
  Puede dejar **1 píxel** de banda negra cuando el contenido empieza en una
  coordenada impar (el formato de vídeo obliga a recortar en múltiplos de 2 y
  siempre se redondea hacia fuera, nunca hacia dentro).
- Si **bajas mucho `--fps`** (por ejemplo `--fps 1`), un scroll largo se muestrea
  demasiado poco y puede perderse el final del documento. Con el valor de
  fábrica (4) esto no ocurre; si tocas `--fps`, hazlo hacia arriba.
- Una página que **reaparece** más tarde no se vuelve a guardar como imagen: sale
  una sola vez en el PDF y sus otras apariciones quedan listadas en
  `resumen.txt`. Si lo que quieres es una transcripción visual del vídeo (con
  repeticiones) en vez del documento, tendrás que usar esos tiempos a mano.
