# Informe Coffee Business — semana 27 de julio al 02 de agosto de 2026

Reconstrucción del informe semanal del mercado del café a partir del video del canal
[Lavaive](https://www.youtube.com/@Lavaive) (contenido exclusivo para miembros).

- **Video:** <https://youtu.be/Mylvecoa7qA>
- **Documento original:** *"26 de julio de 2026 — Análisis del mercado del café"*, de Coffee Business
  (autor: Juan Felipe Jaimes V).
- **Duración del video:** 21 min (1.262 s), 1920×1080, audio original en español.

## Qué se extrajo

| Entregable | Descripción |
|---|---|
| `Informe_Coffee_Business_27jul-02ago.pdf` | El informe completo, 83 páginas. |
| `audio.mp3` | La narración completa (21 min, 192 kbps). |
| `Informe_ES.md` | Transcripción del texto del informe, en español. |
| `Report_EN.md` | El mismo informe traducido al inglés. |
| `Informe_Completo_ES.md` | El informe con la narración del video integrada, en español. |
| `Full_Report_EN.md` | Lo mismo en inglés. |
| `Narracion_audio_bruta_ES.txt` | Transcripción bruta del audio, con marcas de tiempo. |

> Los archivos PDF y MP3 no se versionan en el repositorio por su tamaño (42 MB y 30 MB).

## Informe combinado

`Informe_Completo_ES.md` y `Full_Report_EN.md` reorganizan el informe en 7 secciones y le añaden
21 bloques con lo que el autor **explica hablando** en el video, cada uno con su marca de tiempo,
separados del texto del documento escrito.

La narración se transcribió con Whisper large-v3, fusionando dos pasadas independientes que
cubren mutuamente sus vacíos. Todas las cifras habladas se contrastaron contra el documento; donde
ambas fuentes discrepan, prevalece el documento y la diferencia queda anotada en el punto
correspondiente.

## Cómo se garantizó que no falta contenido

El documento del video no pasa de página en página: **se desplaza (scroll)** de forma continua,
con retrocesos ocasionales. El método fue:

1. Muestreo del video a 2 fps y detección de los **110 tramos estables** (momentos en que el
   documento se queda quieto ≥ 1 s), extrayendo un fotograma nítido a 1920×1080 de cada uno.
2. Registro del desplazamiento vertical entre fotogramas consecutivos mediante correlación de
   descriptores por fila (32 bloques de columnas), usando solo las filas con texto real.
3. **Descarte únicamente de duplicados**: se elimina un fotograma solo si otro ya conservado
   muestra el mismo contenido en la misma posición (correlación > 0,93 y desfase < 120 px).
   Quedaron 83 de 110.
4. **Verificación de huecos**: se comprobó que entre tramos estables consecutivos el
   desplazamiento nunca alcanza una pantalla completa (1080 px). Resultado: **0 saltos**, es
   decir, la cobertura del documento es continua y no se perdió ningún fragmento.

Se descartó el cosido pixel a pixel en un lienzo único: no superó la verificación independiente
(76 % de los pares solapados no concordaban, por las amplias zonas en blanco del documento que
hacen inestable la correlación). Se prefirió un PDF con algo de solapamiento entre páginas antes
que un documento aparentemente limpio pero corrupto.

## `herramientas/`

`extraer_informe.py` es una herramienta general para repetir este proceso con otros videos.
Ver [`herramientas/LEEME.md`](herramientas/LEEME.md) para el modo de uso.

```bash
python3 herramientas/extraer_informe.py video.mp4 --salida informe_extraido
```
