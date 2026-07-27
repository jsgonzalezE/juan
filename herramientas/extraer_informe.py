#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extraer_informe.py
==================

Reconstruye un documento (PDF + imagenes + audio) a partir de un video en el que
se muestra una presentacion o un documento de varias paginas mientras alguien narra.

Uso:
    python3 extraer_informe.py <video> [--salida DIR] [--sensibilidad N]
                               [--sin-audio] [--fps N] [--debug]

ARQUITECTURA (sintesis de tres estrategias independientes)
----------------------------------------------------------
1. SONDEO           ffprobe: duracion, resolucion, pista de audio. Fallos claros.
2. RECORTE          cropdetect de ffmpeg  UNIDO a  un bounding-box de contenido
                    calculado sobre el MAXIMO TEMPORAL de 12 sondas A RESOLUCION
                    NATIVA. Nunca corta contenido: el maximo temporal solo puede
                    ampliar el recorte. Medir a resolucion nativa (en vez de
                    sobre una miniatura de 480x270 con un margen del 0.4%) es lo
                    que evita dejar una franja negra residual de 8 px en todas
                    las paginas y en el PDF; ahora el residuo es 0 px, o 1 px si
                    el contenido esta en una coordenada impar (yuv420p obliga a
                    alinear el recorte a pares, siempre hacia fuera).
3. UNA DECODIFICACION en streaming (crop -> fps -> scale 256x144 gris). Por muestra
                    se retienen ~10.9 KB: firma 128x72 + 2 perfiles de bordes por
                    fila + 1 escalar de movimiento. Jamas se guarda un fotograma.
4. SENSOR BARATO    serie de movimiento (MAD global a resolucion de decodificacion)
                    -> pares "quietos" -> se aprende la MASCARA de zonas cronicamente
                    animadas (webcam, reloj, cursor, barra de progreso). El limite
                    de "par quieto" es adaptativo y los umbrales de actividad son
                    propios: con umbrales fijos, una webcam grande impedia aprender
                    su propia mascara y el video estallaba en 119 paginas falsas.
5. CONFIRMACION ROBUSTA  doble metrica sobre la MISMA firma, ambas enmascaradas:
                    (a) VOTO POR BALDOSAS con 1-NCC en rejilla gruesa 8x6 -> invariante
                        a brillo/contraste, inmune al reencodeo con perdida. Detecta
                        cambios GLOBALES de pagina.
                    (b) TEST DE FRACCION DE PIXELES en rejilla fina 16x9 -> un cambio
                        cuenta si >25% de los pixeles de la celda difieren >18 niveles.
                        Detecta cambios SUTILES (una barra de un grafico) que el voto
                        global diluye, y rechaza el cursor (satura la media de una
                        celda pero toca muy pocos pixeles).
                    Pagina nueva = (a) OR (b). Esto corrige el punto ciego que las
                    tres estrategias tenian por separado.
6. SEGMENTACION     tramos QUIETOS / EN MOVIMIENTO decididos por DOS sensores que
                    deben coincidir: el voto por baldosas (1-NCC) y el MAD. Hacen
                    falta los dos porque 1-NCC, al ser invariante al contraste, es
                    estructuralmente CIEGO a las mezclas de un fundido (medido:
                    0.0000 durante fundidos completos) mientras que el MAD si las
                    ve (asentado 0.05-0.15, fundido 0.36-1.86). Dentro de un tramo
                    quieto se compara siempre contra el ANCLA del tramo, que es lo
                    unico que ve un fundido cruzado lento.
7. MOVIMIENTO       en tramos en movimiento se fuerzan capturas POR TIEMPO. Esto es
                    lo que cubre el scroll continuo SIN paradas, donde la
                    segmentacion quieto/ocupado por si sola no emitiria nada. NO se
                    usa la magnitud del desplazamiento: sobre texto es aliasing puro
                    (correlacion 1.000 con saltos de -44 a +43 filas) y multiplicaba
                    por 5 el numero de paginas. Cada captura forzada se exige a
                    MEDIO INTERVALO como minimo de la anterior: si no, al arrancar
                    un scroll desde una posicion mantenida la primera captura caia
                    a 1 s de la pagina estable ya guardada, con solo un 5% de
                    desplazamiento, y salia una imagen redundante.
8. FOTOGRAMA LIMPIO representante = maximo CONTRASTE RMS entre las muestras asentadas
                    del tramo. Una mezcla de fundido superpone dos textos y baja el
                    contraste de forma medible; el medoide y la nitidez de bordes NO
                    distinguen mezclas. En tramos en movimiento se descarta ademas la
                    muestra de frontera (todavia muestra la pagina anterior).
9. ACEPTACION       cronologica + deduplicado global con el MISMO criterio dual
                    (para no borrar justamente las paginas de cambio sutil) pero
                    con umbrales FIJOS, ajenos a --sensibilidad: el deduplicado es
                    el unico punto donde una pagina real puede desaparecer, asi
                    que no puede depender de un mando que el usuario baja para
                    "quitar repetidos". Una pagina que REAPARECE no se duplica en
                    el PDF (es un documento) pero su instante queda anotado como
                    "reaparicion" en el manifiesto y en el resumen, para que la
                    linea de tiempo siga reflejando el video.
10. SEGUNDA OPINION phash 256 bits sobre las imagenes ya extraidas a RESOLUCION
                    COMPLETA; elimina solo repeticiones CONSECUTIVAS (<=20/256 bits).
11. SALIDAS         paginas JPEG, informe.pdf (img2pdf, sin reencodear), audio.mp3,
                    manifest.json y resumen.txt.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

import numpy as np

# ---------------------------------------------------------------------------
# Constantes de analisis
# ---------------------------------------------------------------------------

DEC_W, DEC_H = 256, 144          # resolucion de decodificacion (gris)
SIG_W, SIG_H = 128, 72           # firma retenida por muestra (9216 B)

# Rejilla GRUESA: voto por baldosas con 1-NCC (cambios globales de pagina)
GXC, GYC = 8, 6
TWC, THC = SIG_W // GXC, SIG_H // GYC      # 16 x 12 = 192 px por baldosa
NTC, TPXC = GXC * GYC, TWC * THC           # 48 baldosas

# Rejilla FINA: test de fraccion de pixeles (cambios sutiles, rechazo del cursor)
GXF, GYF = 16, 9
TWF, THF = SIG_W // GXF, SIG_H // GYF      # 8 x 8 = 64 px por celda
NTF, TPXF = GXF * GYF, TWF * THF           # 144 celdas

D_TILE = 0.10          # distancia 1-NCC a partir de la cual una baldosa "cambio"
FLAT_STD = 3.0         # baldosa considerada plana (NCC no es fiable)
LUMA_NORM = 24.0       # normalizacion de la diferencia de brillo en baldosas planas

ACT_CHRONIC = 0.30     # celda cronicamente animada si cambia en >30% de pares quietos
# El detector de actividad usa umbrales PROPIOS, mas sensibles que los de
# deteccion de pagina y ademas independientes de --sensibilidad (asi la mascara
# no cambia al mover la sensibilidad). Medido en este entorno sobre pares quietos:
#   webcam del 25% del area -> actividad maxima 0.631
#   video limpio sin overlay -> actividad maxima 0.013  (cero celdas enmascaradas)
# Con los umbrales de deteccion (18, 0.25) la webcam se quedaba en 0.284, justo
# por debajo de 0.30, la mascara no se aprendia y salian 119 paginas falsas.
ACT_PIX = 8.0          # diferencia de nivel para considerar "se movio"
ACT_FRAC = 0.15        # fraccion de pixeles de la celda que deben moverse
ACT_MAXFRAC = 0.45     # si la mascara supera esto, se descarta entera (deck animado)
MASK_QUIET_PAIR = 0.15 # un par es "quieto" si cambia <15% de las celdas

QUIET_FLOOR = 0.06     # suelo del umbral de quietud (fraccion de baldosas)
MAD_FLOOR = 0.30       # suelo del umbral de quietud del sensor MAD (niveles de luma)
MIN_QUIET_S = 0.35     # duracion minima de un tramo quieto para ser candidato
MIN_BUSY_S = 1.20      # tramos en movimiento mas cortos que esto = corte seco

SCROLL_CORR = 0.82     # correlacion minima para declarar traslacion vertical
SCROLL_GAP = 0.15      # ventaja minima sobre el desplazamiento cero
SCROLL_K = 60          # busqueda de +-60 filas

PHASH_DUP = 20         # duplicado consecutivo si distancia phash <= 20/256 bits

# --- criterio de DEDUPLICADO, deliberadamente INDEPENDIENTE de --sensibilidad ---
# Dos candidatos se funden en uno solo si AMBAS metricas dicen "es la misma
# vista". Estos umbrales NO se mueven con la sensibilidad: el deduplicado es el
# unico punto del programa donde una pagina real puede desaparecer, asi que no
# puede quedar en manos de un mando que el usuario baja para "quitar repetidos".
#
# Medido sobre un informe real de 12 paginas con cabecera y pie comunes:
#   frac (1-NCC por baldosas) entre DOS PAGINAS DISTINTAS: minimo 0.1136
#     (sobre TODOS los pares, no solo los consecutivos; los consecutivos dan 0.25)
#   frac entre dos muestras de la MISMA pagina asentada: 0.000
# 0.08 queda por encima del ruido de compresion y por debajo de ese 0.1136.
# Y con DEDUP_CELDAS = 1 basta UNA celda distinta para declarar paginas
# diferentes, que es la salvaguarda que de verdad sostiene el criterio.
DEDUP_FRAC = 0.08
DEDUP_CELDAS = 1
DEDUP_PIX_DELTA = 18.0
DEDUP_PIX_FRAC = 0.25

MAX_SAMPLES = 20000    # tope duro de muestras (~200 MB de firmas)

EXIT_ARGS = 2          # archivo o argumento invalido
EXIT_TOOLS = 3         # falta ffmpeg / ffprobe
EXIT_VIDEO = 4         # video corrupto o sin pista de video
EXIT_PROC = 5          # fallo durante el proceso


# ---------------------------------------------------------------------------
# Mapa de sensibilidad 1..10 -> umbrales internos
# ---------------------------------------------------------------------------

FRAC_NEW_TECHO = 0.215   # ver perfil_sensibilidad(): tope duro de frac_new


def perfil_sensibilidad(s):
    """1 = conservador (menos repeticiones), 10 = agresivo (mas capturas).

    REGLA DE DISENO (corrige una perdida silenciosa de paginas medida en esta
    misma herramienta): `frac_new` es el unico parametro capaz de FUNDIR DOS
    PAGINAS DISTINTAS en una sola, asi que NO se usa como mando de sensibilidad
    mas alla de un techo seguro.

    Medicion sobre un informe real de 12 paginas con cabecera y pie comunes: la
    distancia por baldosas (1-NCC) entre paginas CONSECUTIVAS Y DISTINTAS vale
    entre 0.250 y 0.432, con minimo 0.250. Con la tabla anterior los niveles
    1..3 pedian frac_new = 0.320 / 0.290 / 0.260, es decir POR ENCIMA de esa
    separacion minima: paginas realmente distintas quedaban por debajo del
    umbral y desaparecian sin aviso (nivel 3 -> 8 imagenes de 12 paginas;
    nivel 1 -> 6 de 12). Un usuario que siguiera el consejo impreso de bajar la
    sensibilidad se quedaba con medio informe.

    Ahora frac_new nunca pasa de FRAC_NEW_TECHO = 0.215 (un 14% de margen por
    debajo de la separacion minima medida). Bajar la sensibilidad solo endurece
    los parametros que producen REPETICIONES:
      - min_celdas / pix_delta / pix_frac : cuanto cambio "sutil" hace falta
      - sep_debil / fuerte                : encadenado de casi-duplicados
      - max_mov_s                         : cada cuanto se captura en un scroll
    Es decir: menos sensibilidad = menos imagenes repetidas, NO menos paginas.
    """
    s = int(max(1, min(10, s)))
    tabla = {
        #     frac_new  min_celdas  pix_delta  pix_frac  fuerte  sep_debil  max_mov_s
        1:  (0.215,  6, 26.0, 0.40, 16, 4.0, 8.0),
        2:  (0.213,  5, 24.0, 0.36, 14, 3.5, 7.0),
        3:  (0.211,  4, 22.0, 0.32, 12, 3.0, 6.0),
        4:  (0.210,  2, 20.0, 0.28, 10, 2.4, 4.5),
        5:  (0.210,  1, 18.0, 0.25,  8, 2.0, 3.0),
        6:  (0.185,  1, 16.0, 0.22,  7, 1.8, 2.5),
        7:  (0.160,  1, 15.0, 0.20,  6, 1.5, 2.5),
        8:  (0.135,  1, 14.0, 0.18,  5, 1.2, 2.0),
        9:  (0.110,  1, 12.0, 0.16,  4, 1.0, 2.0),
        10: (0.085,  1, 11.0, 0.15,  3, 0.8, 1.5),
    }
    f, mc, pd, pf, fu, sd, mm = tabla[s]
    return dict(frac_new=min(f, FRAC_NEW_TECHO), min_celdas=mc, pix_delta=pd,
                pix_frac=pf, fuerte=fu, sep_debil=sd, max_mov_s=mm, nivel=s)


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

_T0 = time.time()


def log(msg):
    print(msg, flush=True)


def vlog(activo, msg):
    if activo:
        print("      . %s" % msg, flush=True)


def morir(codigo, msg):
    print("\nERROR: %s" % msg, file=sys.stderr, flush=True)
    sys.exit(codigo)


def hms(t):
    t = max(0.0, float(t))
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = int(t % 60)
    return "%02d:%02d:%02d" % (h, m, s)


def buscar_herramientas():
    ff = shutil.which("ffmpeg") or "/usr/local/bin/ffmpeg"
    fp = shutil.which("ffprobe") or "/usr/local/bin/ffprobe"
    if not (os.path.isfile(ff) and os.access(ff, os.X_OK)):
        morir(EXIT_TOOLS, "no se encuentra 'ffmpeg' en el sistema.\n"
                          "Instalalo con:  brew install ffmpeg   (macOS)\n"
                          "                sudo apt install ffmpeg   (Linux)")
    if not (os.path.isfile(fp) and os.access(fp, os.X_OK)):
        morir(EXIT_TOOLS, "no se encuentra 'ffprobe' (viene junto con ffmpeg).")
    return ff, fp


def correr(cmd, timeout=None):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          timeout=timeout)


# ---------------------------------------------------------------------------
# 1. Sondeo del archivo
# ---------------------------------------------------------------------------

def sondear(video, fp):
    if not os.path.exists(video):
        morir(EXIT_ARGS, "no existe el archivo: %s" % video)
    if os.path.isdir(video):
        morir(EXIT_ARGS, "'%s' es una carpeta, no un archivo de video." % video)
    if os.path.getsize(video) == 0:
        morir(EXIT_ARGS, "el archivo esta vacio (0 bytes): %s" % video)

    r = correr([fp, "-v", "error", "-print_format", "json",
                "-show_format", "-show_streams", video], timeout=120)
    if r.returncode != 0:
        det = r.stderr.decode("utf8", "replace").strip().splitlines()
        det = det[-1] if det else "formato no reconocido"
        morir(EXIT_VIDEO, "no se pudo leer el video (archivo corrupto o formato no "
                          "soportado).\nDetalle de ffprobe: %s" % det)
    try:
        info = json.loads(r.stdout.decode("utf8", "replace"))
    except Exception:
        morir(EXIT_VIDEO, "ffprobe devolvio una respuesta ilegible; el archivo "
                          "parece corrupto.")

    vs = [s for s in info.get("streams", []) if s.get("codec_type") == "video"]
    aud = [s for s in info.get("streams", []) if s.get("codec_type") == "audio"]
    if not vs:
        morir(EXIT_VIDEO, "el archivo no contiene ninguna pista de video.")
    v = vs[0]

    dur = 0.0
    for cand in (info.get("format", {}).get("duration"), v.get("duration")):
        try:
            dur = float(cand)
            if dur > 0:
                break
        except (TypeError, ValueError):
            continue
    if dur <= 0:
        # ultimo recurso: contar con ffprobe
        r2 = correr([fp, "-v", "error", "-select_streams", "v:0", "-count_packets",
                     "-show_entries", "stream=nb_read_packets,avg_frame_rate",
                     "-of", "csv=p=0", video], timeout=600)
        try:
            npk, rate = r2.stdout.decode().strip().split(",")[:2]
            num, den = rate.split("/")
            dur = int(npk) / (float(num) / float(den))
        except Exception:
            dur = 0.0
    if dur <= 0:
        morir(EXIT_VIDEO, "el video tiene duracion cero o no se pudo determinar; "
                          "probablemente esta corrupto.")

    w, h = int(v.get("width") or 0), int(v.get("height") or 0)
    if w < 16 or h < 16:
        morir(EXIT_VIDEO, "la resolucion del video es invalida (%dx%d)." % (w, h))

    return dict(dur=dur, w=w, h=h, audio=bool(aud),
                codec=v.get("codec_name", "?"))


# ---------------------------------------------------------------------------
# 2. Recorte de bandas negras
# ---------------------------------------------------------------------------

BORDE_NEGRO = 24       # nivel de luma por debajo del cual un pixel es "banda negra"
BORDE_FRAC = 0.015     # fraccion de pixeles de la fila/columna que deben superarlo
SONDA_MAX_PX = 9.0e6   # presupuesto por sonda; por encima se submuestrea


def _sonda_gris(video, ff, t, w, h):
    """Decodifica UN fotograma en gris a w x h. Devuelve None si falla."""
    r = correr([ff, "-nostdin", "-v", "error", "-ss", "%.3f" % t, "-i", video,
                "-frames:v", "1", "-vf",
                "scale=%d:%d:flags=area,format=gray" % (w, h),
                "-f", "rawvideo", "-"], timeout=120)
    if r.returncode != 0 or len(r.stdout) < w * h:
        return None
    return np.frombuffer(r.stdout[:w * h], np.uint8).reshape(h, w)


def bbox_contenido(video, ff, dur, w, h, n=12):
    """Bounding-box del contenido en PIXELES, sobre el maximo temporal de n sondas.

    El maximo temporal evita que una diapositiva oscura haga creer que hay
    bandas donde no las hay.

    PRECISION: se sondea a RESOLUCION NATIVA (o al mayor divisor entero que
    quepa en SONDA_MAX_PX). Antes se median las bandas sobre una miniatura de
    480x270 y ademas se anadia un margen del 0.4% "por seguridad": en un video
    de 1920x1080 eso son +-4 px por lado, que se colaban en TODAS las paginas y
    en el PDF como una franja negra residual, visible al imprimir. A resolucion
    nativa el borde se localiza exacto y el margen sobra.

    Devuelve (x0, y0, x1, y1) en pixeles del video original, o None.
    """
    fac = 1
    while (w // fac) * (h // fac) > SONDA_MAX_PX:
        fac += 1
    pw, ph = max(2, w // fac), max(2, h // fac)

    vmax = None
    for i in range(n):
        t = dur * (0.03 + 0.94 * (i / max(1, n - 1.0)))
        g = _sonda_gris(video, ff, min(t, max(0.0, dur - 0.05)), pw, ph)
        if g is None:
            continue
        vmax = g.copy() if vmax is None else np.maximum(vmax, g)
    if vmax is None:
        return None

    fila_ok = (vmax > BORDE_NEGRO).mean(axis=1) > BORDE_FRAC
    col_ok = (vmax > BORDE_NEGRO).mean(axis=0) > BORDE_FRAC
    if not fila_ok.any() or not col_ok.any():
        return None
    ys = np.nonzero(fila_ok)[0]
    xs = np.nonzero(col_ok)[0]
    # al volver a pixeles del original se amplia por el factor de submuestreo,
    # que es la unica direccion segura (nunca corta contenido).
    y0, y1 = int(ys[0]) * fac, min(h, (int(ys[-1]) + 1) * fac)
    x0, x1 = int(xs[0]) * fac, min(w, (int(xs[-1]) + 1) * fac)
    return (x0, y0, x1, y1)


def cropdetect(video, ff, dur, w, h):
    """Union de varias pasadas de cropdetect. Devuelve (x0,y0,x1,y1) en PIXELES."""
    pos = [0.15, 0.35, 0.55, 0.75]
    xs0, ys0, xs1, ys1 = [], [], [], []
    pat = re.compile(r"crop=(\d+):(\d+):(-?\d+):(-?\d+)")
    for p in pos:
        t = max(0.0, min(dur * p, dur - 6.0))
        r = correr([ff, "-nostdin", "-v", "info", "-ss", "%.3f" % t, "-t", "6",
                    "-i", video, "-an", "-vf",
                    "cropdetect=limit=%d:round=2:reset=0" % BORDE_NEGRO,
                    "-f", "null", "-"], timeout=300)
        m = pat.findall(r.stderr.decode("utf8", "replace"))
        if not m:
            continue
        cw, ch, cx, cy = (int(v) for v in m[-1])
        if cw <= 0 or ch <= 0 or cx < 0 or cy < 0:
            continue
        xs0.append(cx)
        ys0.append(cy)
        xs1.append(min(w, cx + cw))
        ys1.append(min(h, cy + ch))
    if not xs0:
        return None
    return (min(xs0), min(ys0), max(xs1), max(ys1))


def detectar_recorte(video, ff, dur, w, h, debug=False):
    """Combina cropdetect con el bbox de contenido. Todo en PIXELES.

    Regla de seguridad: el resultado SIEMPRE contiene el bbox de contenido
    (que por construccion nunca corta nada que alguna vez tuvo contenido).
    cropdetect solo puede AMPLIAR ese recorte, nunca reducirlo: cubre 4
    ventanas continuas de 6 s y por tanto ve instantes que las 12 sondas
    puntuales no visitan.
    """
    bb = bbox_contenido(video, ff, dur, w, h)
    cd = cropdetect(video, ff, dur, w, h)
    vlog(debug, "cropdetect=%s  bbox_contenido=%s  (px)" % (cd, bb))

    if bb is None and cd is None:
        return None
    if bb is None:
        fin = cd
    elif cd is None:
        fin = bb
    else:
        area_cd = ((cd[2] - cd[0]) * (cd[3] - cd[1])) / float(w * h)
        if area_cd < 0.97:
            # cropdetect encontro bandas reales -> union con el bbox de contenido
            fin = (min(cd[0], bb[0]), min(cd[1], bb[1]),
                   max(cd[2], bb[2]), max(cd[3], bb[3]))
        else:
            fin = bb

    # Alineacion par (obligatoria en yuv420p) SIEMPRE hacia fuera: el origen
    # baja al par anterior y el final sube al par siguiente. Eso anade como
    # mucho 1 px por lado, frente a los 4 px del margen fraccionario anterior.
    x0 = max(0, int(fin[0])) & ~1
    y0 = max(0, int(fin[1])) & ~1
    x1 = min(w, (int(fin[2]) + 1) & ~1)
    y1 = min(h, (int(fin[3]) + 1) & ~1)
    cw, ch = max(2, x1 - x0), max(2, y1 - y0)
    cw = min(cw, max(2, (w - x0) & ~1))
    ch = min(ch, max(2, (h - y0) & ~1))

    area = (cw * ch) / float(w * h)
    if area < 0.35 or area > 0.985:
        return None
    return "crop=%d:%d:%d:%d" % (cw, ch, x0, y0)


# ---------------------------------------------------------------------------
# 3. Pasada unica de analisis (streaming)
# ---------------------------------------------------------------------------

def analizar(video, ff, crop, fps, dur, debug=False):
    """UNA sola decodificacion. Retiene ~10.9 KB por muestra, nunca un fotograma.

    Devuelve:
      S     (N, SIG_H, SIG_W) uint8   firmas
      pf    (N, DEC_H) float32        perfil de bordes por fila, ancho completo
      pc    (N, DEC_H) float32        perfil de bordes por fila, 20%-80% central
      mov   (N,) float32              MAD global a resolucion de decodificacion
    """
    vf = []
    if crop:
        vf.append(crop)
    vf += ["fps=%g" % fps,
           "scale=%d:%d:flags=area" % (DEC_W, DEC_H),
           "format=gray"]
    cmd = [ff, "-nostdin", "-v", "error", "-threads", "0", "-i", video,
           "-an", "-sn", "-dn", "-vf", ",".join(vf),
           "-f", "rawvideo", "-pix_fmt", "gray", "-"]
    vlog(debug, "ffmpeg -vf %s" % ",".join(vf))

    cap = min(MAX_SAMPLES, int(dur * fps) + 64)
    S = np.empty((cap, SIG_H, SIG_W), np.uint8)
    pf = np.empty((cap, DEC_H), np.float32)
    pc = np.empty((cap, DEC_H), np.float32)
    mov = np.zeros(cap, np.float32)

    c0, c1 = int(DEC_W * 0.20), int(DEC_W * 0.80)
    nb = DEC_W * DEC_H
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         bufsize=nb * 8)
    prev = None
    i = 0
    ultimo_aviso = 0.0
    try:
        while i < cap:
            buf = p.stdout.read(nb)
            if len(buf) < nb:
                break
            g = np.frombuffer(buf, np.uint8).reshape(DEC_H, DEC_W)
            gf = g.astype(np.float32)

            # firma 128x72 por promedio de cajas 2x2 (atenua el macrobloqueo)
            S[i] = gf.reshape(SIG_H, 2, SIG_W, 2).mean(axis=(1, 3)).astype(np.uint8)

            # perfiles de bordes por fila (para medir traslacion vertical)
            pf[i] = np.abs(np.diff(gf, axis=1)).mean(axis=1)
            pc[i] = np.abs(np.diff(gf[:, c0:c1], axis=1)).mean(axis=1)

            # sensor barato de movimiento, a resolucion de decodificacion
            mov[i] = 0.0 if prev is None else float(np.abs(gf - prev).mean())
            prev = gf
            i += 1

            if debug and i % 500 == 0:
                t = i / fps
                if t - ultimo_aviso > 0:
                    vlog(True, "muestras=%d  (t=%s)" % (i, hms(t)))
                    ultimo_aviso = t
    finally:
        try:
            p.stdout.close()
        except Exception:
            pass
        err = p.stderr.read().decode("utf8", "replace")
        p.stderr.close()
        p.wait()

    if i == 0:
        morir(EXIT_VIDEO, "no se pudo decodificar ningun fotograma del video "
                          "(archivo corrupto o codec no soportado).\n"
                          "Detalle de ffmpeg: %s" % err.strip()[:400])
    return S[:i], pf[:i], pc[:i], mov[:i]


# ---------------------------------------------------------------------------
# 4-5. Comparador: doble metrica sobre la misma firma
# ---------------------------------------------------------------------------

class Comparador(object):
    """Dos metricas complementarias, ambas enmascaradas:

    - frac(i, j): fraccion de baldosas GRUESAS cuya distancia 1-NCC supera D_TILE.
      NCC es invariante a brillo y contraste => inmune al drift de color y al
      reencodeo con perdida. Es la senal para cambios GLOBALES de pagina.

    - celdas(i, j): numero de celdas FINAS en las que mas de `pix_frac` de sus
      pixeles difieren en mas de `pix_delta` niveles. Es la senal para cambios
      SUTILES (una barra, una cifra) que el voto global diluye, y es lo que
      rechaza el cursor del raton (satura la media de una celda pero toca muy
      pocos pixeles).
    """

    def __init__(self, S, cfg):
        self.S = S
        self.N = len(S)
        self.pix_delta = cfg["pix_delta"]
        self.pix_frac = cfg["pix_frac"]
        self.mask_c = np.ones(NTC, bool)     # baldosas gruesas utiles
        self.mask_f = np.ones(NTF, bool)     # celdas finas utiles
        self._precalcular()

    # -- vistas por rejilla (reshape + transpose, sin copiar el array grande) --
    def gruesa(self, i):
        return (self.S[i].reshape(GYC, THC, GXC, TWC)
                .transpose(0, 2, 1, 3).reshape(NTC, TPXC).astype(np.float32))

    def fina(self, i):
        return (self.S[i].reshape(GYF, THF, GXF, TWF)
                .transpose(0, 2, 1, 3).reshape(NTF, TPXF).astype(np.int16))

    def _precalcular(self):
        """Media y desviacion tipica por baldosa gruesa, para todas las muestras.

        Se hace por bloques para no materializar una copia transpuesta del array
        completo de firmas.
        """
        N = self.N
        self.m = np.empty((N, NTC), np.float32)
        self.sd = np.empty((N, NTC), np.float32)
        paso = 512
        for a in range(0, N, paso):
            b = min(N, a + paso)
            blk = (self.S[a:b].reshape(-1, GYC, THC, GXC, TWC)
                   .transpose(0, 1, 3, 2, 4).reshape(-1, NTC, TPXC).astype(np.float32))
            self.m[a:b] = blk.mean(axis=2)
            self.sd[a:b] = blk.std(axis=2)
        # contraste RMS medio por muestra (se recalcula tras la mascara)
        self.contraste = self.sd.mean(axis=1)

    # ---------------- metrica gruesa (1 - NCC) ----------------
    def dist_gruesa(self, i, j):
        A, B = self.gruesa(i), self.gruesa(j)
        ma, mb = self.m[i], self.m[j]
        sa, sb = self.sd[i], self.sd[j]
        ncc = ((A * B).mean(axis=1) - ma * mb) / np.maximum(sa * sb, 1e-6)
        d = np.clip(1.0 - ncc, 0.0, 2.0)
        fa, fb = sa < FLAT_STD, sb < FLAT_STD
        dl = np.abs(ma - mb) / LUMA_NORM
        d = np.where(fa & fb, np.clip(dl, 0.0, 1.0), d)   # ambas planas -> solo brillo
        d = np.where(fa ^ fb, 1.0, d)                     # una plana, otra no -> cambio
        return np.maximum(d, np.clip(dl - 0.3, 0.0, 1.0))

    def frac(self, i, j):
        ch = self.dist_gruesa(i, j) > D_TILE
        mk = self.mask_c
        return float(ch[mk].mean()) if mk.any() else float(ch.mean())

    # ---------------- metrica fina (fraccion de pixeles) ----------------
    def celdas_cambiadas(self, i, j, enmascarar=True, delta=None, frac=None):
        d = self.pix_delta if delta is None else delta
        f = self.pix_frac if frac is None else frac
        ch = (np.abs(self.fina(i) - self.fina(j)) > d).mean(axis=1) > f
        if enmascarar:
            ch = ch & self.mask_f
        return ch

    def celdas(self, i, j):
        """Celdas cambiadas con los umbrales de DETECCION (segun sensibilidad)."""
        return int(self.celdas_cambiadas(i, j).sum())

    def celdas_dedup(self, i, j):
        """Celdas cambiadas con los umbrales FIJOS del deduplicado.

        No usa self.pix_delta / self.pix_frac a proposito: esos suben al bajar
        la sensibilidad y, aplicados al deduplicado, hacian que dos paginas
        distintas dieran 0 celdas cambiadas y se fundieran en una.
        """
        return int(self.celdas_cambiadas(i, j, delta=DEDUP_PIX_DELTA,
                                         frac=DEDUP_PIX_FRAC).sum())

    def mascara_imagen(self):
        """La mascara fina expandida a la forma de la firma (SIG_H, SIG_W)."""
        g = self.mask_f.reshape(GYF, GXF)
        return np.repeat(np.repeat(g, THF, axis=0), TWF, axis=1)

    def serie_mad(self):
        """MAD enmascarado entre muestras consecutivas.

        Complementa a `frac`: 1-NCC es invariante al contraste y por eso es
        estructuralmente CIEGO a las mezclas de un fundido cruzado (medido:
        0.0000 durante fundidos completos). El MAD no es invariante y si las ve
        (medido: pagina asentada 0.05-0.15, fundido 0.36-1.86). Es el sensor
        barato que separa lo asentado de lo que esta en transicion.
        """
        mi = self.mascara_imagen()
        out = np.zeros(self.N, np.float32)
        for i in range(1, self.N):
            d = np.abs(self.S[i].astype(np.int16) - self.S[i - 1].astype(np.int16))
            out[i] = float(d[mi].mean())
        return out

    # ---------------- mascara de zonas cronicamente animadas ----------------
    def aprender_mascara(self, debug=False):
        """Webcam, reloj, cursor y barra de progreso.

        CLAVE (los tres candidatos coinciden): medir la actividad SOLO en pares
        donde el resto del cuadro esta quieto. Promediando sobre todos los pares,
        los cambios de pagina reales contaminan el mapa y sale plano.
        """
        N = self.N
        if N < 12:
            return 0

        CH = np.zeros((N, NTF), bool)
        for i in range(1, N):
            CH[i] = ((np.abs(self.fina(i) - self.fina(i - 1)) > ACT_PIX)
                     .mean(axis=1) > ACT_FRAC)
        chs = CH.mean(axis=1)

        # El limite para considerar un par "de la misma pagina" tiene que ser
        # ADAPTATIVO. Con un umbral fijo bajo, una webcam grande (que por si sola
        # enciende ~25% de las celdas en TODOS los pares) hace que ningun par
        # llegue a considerarse quieto, la mascara nunca se aprende y el video se
        # descompone en cientos de falsas paginas (medido: 119 en vez de 12).
        # Tomando la mediana se garantiza que siempre haya pares de referencia:
        # en un video de documento la mayoria de los pares SI son de la misma
        # pagina, y un cambio de pagina real queda muy por encima de la mediana.
        lim = float(np.clip(max(MASK_QUIET_PAIR, np.median(chs[1:])), 0.0, 0.45))
        sel = chs <= lim
        sel[0] = False
        nq = int(sel.sum())
        if nq < 10:
            return 0
        act = CH[sel].mean(axis=0)
        cand = act > ACT_CHRONIC
        if not cand.any():
            return 0

        # dilatar 1 celda para atrapar los bordes del overlay (solo si es pequena)
        if cand.mean() <= 0.15:
            g = cand.reshape(GYF, GXF)
            d = g.copy()
            for r in range(GYF):
                for c in range(GXF):
                    if g[r, c]:
                        d[max(0, r - 1):r + 2, max(0, c - 1):c + 2] = True
            cand = d.reshape(-1)

        if cand.mean() > ACT_MAXFRAC:
            vlog(debug, "mascara descartada (%.0f%% de celdas): el contenido es "
                        "mayoritariamente animado" % (100 * cand.mean()))
            return 0

        self.mask_f = ~cand
        # derivar la mascara gruesa por mayoria de celdas finas hijas
        gf = cand.reshape(GYF, GXF)
        gc = np.zeros((GYC, GXC), bool)
        for r in range(GYC):
            for c in range(GXC):
                r0, r1 = r * GYF // GYC, max(r * GYF // GYC + 1, (r + 1) * GYF // GYC)
                c0, c1 = c * GXF // GXC, max(c * GXF // GXC + 1, (c + 1) * GXF // GXC)
                gc[r, c] = gf[r0:r1, c0:c1].mean() > 0.5
        if gc.mean() < ACT_MAXFRAC:
            self.mask_c = ~gc.reshape(-1)
        # recalcular el contraste solo sobre baldosas utiles
        if self.mask_c.any():
            self.contraste = self.sd[:, self.mask_c].mean(axis=1)
        return int(cand.sum())


# ---------------------------------------------------------------------------
# 7. Traslacion vertical (scroll) por correlacion normalizada de perfiles
# ---------------------------------------------------------------------------

def desplazamiento(A, B, i, j, K=SCROLL_K):
    """Correlacion cruzada normalizada con solape exacto via sumas acumuladas.

    Vectorizada: ~55 us por llamada frente a ~2100 us con un bucle Python.
    Devuelve (es_scroll, filas_desplazadas, correlacion).
    """
    a = A[i].astype(np.float64)
    b = B[j].astype(np.float64)
    L = a.size
    K = min(K, L - 1)
    n = np.arange(-K, K + 1)
    m = L - np.abs(n)
    ok = m >= int(L * 0.45)

    Sxy = np.correlate(a, b, "full")[L - 1 - K: L + K]
    ca = np.concatenate(([0.0], np.cumsum(a)))
    ca2 = np.concatenate(([0.0], np.cumsum(a * a)))
    cb = np.concatenate(([0.0], np.cumsum(b)))
    cb2 = np.concatenate(([0.0], np.cumsum(b * b)))
    p = np.maximum(n, 0)
    q = np.maximum(-n, 0)
    Sx = ca[p + m] - ca[p]
    Sxx = ca2[p + m] - ca2[p]
    Sy = cb[q + m] - cb[q]
    Syy = cb2[q + m] - cb2[q]
    num = Sxy - Sx * Sy / m
    den = np.sqrt(np.maximum(Sxx - Sx * Sx / m, 0) * np.maximum(Syy - Sy * Sy / m, 0))
    c = np.where(ok, np.where(den > 1e-9, num / np.maximum(den, 1e-30), 0.0), -9.0)

    k = int(np.argmax(c))
    mejor_s, mejor_c, c0 = int(n[k]), float(c[k]), float(c[K])
    es = (abs(mejor_s) >= 1 and mejor_c >= SCROLL_CORR and mejor_c - c0 >= SCROLL_GAP)
    return es, mejor_s, mejor_c


# ---------------------------------------------------------------------------
# 6-9. Deteccion de paginas
# ---------------------------------------------------------------------------

def detectar_paginas(cmp_, pf, pc, mov, fps, cfg, debug=False):
    """Devuelve [(indice_de_muestra, etiqueta), ...] en orden cronologico."""
    N = cmp_.N
    if N == 0:
        return [], {}
    if N == 1:
        return [(0, "unica")], dict(q_thr=0.0, quietos=1)

    frac_new = cfg["frac_new"]
    min_celdas = cfg["min_celdas"]
    fuerte = cfg["fuerte"]
    sep_debil = cfg["sep_debil"]
    max_mov = max(2, int(cfg["max_mov_s"] * fps))

    # --- serie de cambio muestra a muestra, ya enmascarada ---
    f2f = np.empty(N - 1, np.float32)
    for i in range(1, N):
        f2f[i - 1] = cmp_.frac(i, i - 1)

    # umbral de quietud adaptado al ruido real del video
    q_thr = float(np.clip(max(QUIET_FLOOR, np.percentile(f2f, 25) * 2.0),
                          0.0, frac_new * 0.45))

    # SEGUNDO SENSOR, independiente y complementario. `frac` (1-NCC) es ciego a
    # los fundidos por ser invariante al contraste; el MAD si los ve. Una muestra
    # solo se considera ASENTADA si AMBOS sensores estan de acuerdo, y asi ningun
    # fotograma mezclado puede llegar a ser representante de una pagina.
    madm = cmp_.serie_mad()
    mad_thr = max(MAD_FLOOR, float(np.median(madm)) * 2.5)

    quieto = np.zeros(N, bool)
    quieto[0] = True
    quieto[1:] = (f2f < q_thr) & (madm[1:] < mad_thr)

    contraste = cmp_.contraste
    min_q = max(1, int(MIN_QUIET_S * fps))
    min_b = max(2, int(MIN_BUSY_S * fps))

    ext_fwd = max(1, int(2.0 * fps))

    def representante(a, b):
        """Fotograma ASENTADO: maximo contraste RMS entre las muestras quietas
        del 80% central. Una mezcla de fundido superpone dos textos y baja el
        contraste de forma consistente; el medoide con NCC es ciego a las mezclas
        (es invariante al contraste) y la nitidez de bordes tambien falla.

        ANTI-MEZCLA: un fundido lento no mueve casi nada entre muestras, asi que
        el tramo entero puede quedar DENTRO del fundido y entonces no hay ningun
        fotograma limpio que elegir. Si el mejor del tramo sigue en un valle de
        contraste, se busca HACIA ADELANTE el estado asentado.

        La busqueda se limita a muestras que NCC considera "la misma pagina"
        (frac < frac_new). Esto es seguro precisamente porque NCC es ciego a las
        mezclas: el estado asentado de un fundido SI entra en ese vecindario,
        mientras que una pagina realmente distinta NO, de modo que este ajuste
        nunca puede saltarse una pagina.
        """
        if b <= a:
            return a
        lo = a + int((b - a) * 0.10)
        hi = a + int((b - a) * 0.90)
        if hi <= lo:
            lo, hi = a, b
        seg = np.arange(lo, min(hi, N - 1) + 1)
        sub = seg[quieto[seg]]
        if sub.size == 0:
            sub = seg
        mejor = int(sub[int(np.argmax(contraste[sub]))])

        fin = min(N - 1, b + ext_fwd)
        ext = np.arange(a, fin + 1)
        ext = ext[quieto[ext]]
        if ext.size and contraste[mejor] < 0.985 * float(contraste[ext].max()):
            cand = [x for x in ext.tolist() if cmp_.frac(x, mejor) < frac_new]
            if cand:
                mejor = max(cand, key=lambda x: contraste[x])
        return mejor

    def rep_movimiento(w0, k, ini_tramo, prev_idx, lim):
        """Representante dentro de un tramo EN MOVIMIENTO (zoom, pan, scroll).

        Aqui no existe ningun fotograma realmente asentado, asi que se combinan
        las dos senales:
          1. se descarta la muestra de FRONTERA del tramo (todavia muestra la
             pagina ANTERIOR, no la nueva);
          2. entre el 50% de muestras que menos se mueven se elige la de MAYOR
             contraste RMS. Solo con el minimo de movimiento se caia dentro de
             los fundidos, que se mueven poco pero son mezclas de dos paginas.

        SEPARACION MINIMA (`prev_idx`): al principio de un scroll que arranca
        desde una posicion mantenida, las primeras muestras del tramo todavia
        muestran, casi identica, la vista que ya se capturo como pagina estable.
        Medido: la captura forzada caia a 1.0 s del ultimo estable, con solo
        56 px de scroll (5% de la altura), y producia una imagen redundante.
        No basta con descartar la muestra de frontera, porque el comparador
        1-NCC se satura con cualquier traslacion de texto y no ve la
        redundancia. Se exige por tanto que el representante este al menos a
        medio intervalo de captura de la anterior emision; asi las capturas de
        un tramo largo quedan repartidas de forma regular. Si la restriccion
        vaciara la ventana, se ignora (nunca se pierde contenido por esto).
        """
        w = np.arange(w0, k + 1)
        if w.size > 2 and w[0] <= ini_tramo:
            w = w[1:]
        if prev_idx is not None:
            sep = w[w >= prev_idx + max(1, lim // 2)]
            if sep.size:
                w = sep
        mv = mov[w]
        med = float(np.median(mv))
        cal = w[mv <= med]
        if cal.size == 0:
            cal = w
        return int(cal[int(np.argmax(contraste[cal]))])

    cands = []
    t_ult = -1e9
    i = 0
    while i < N:
        if quieto[i]:
            # ---------------- tramo QUIETO ----------------
            j = i
            while j + 1 < N and quieto[j + 1]:
                j += 1
            if (j - i + 1) < min_q and cands:
                i = j + 1
                continue

            ancla = i
            k = i + 1
            while k <= j + 1:
                if k > j:
                    cands.append((representante(ancla, j), "estable"))
                    break
                fr = cmp_.frac(k, ancla)
                nt = cmp_.celdas(k, ancla)
                cambio_global = fr >= frac_new
                cambio_sutil = (not cambio_global) and nt >= min_celdas

                if cambio_sutil:
                    # Guarda 1: no encadenar fundidos lentos en casi-duplicados.
                    if (k / fps) - t_ult < sep_debil and nt < fuerte:
                        k += 1
                        continue
                    # Guarda 2: PERSISTENCIA. Un cambio real permanece; el ruido
                    # de compresion y los parpadeos transitorios no.
                    conf = [cmp_.celdas(x, ancla) >= min_celdas
                            for x in (k + 1, k + 2) if x <= j]
                    if conf and not all(conf):
                        k += 1
                        continue

                if cambio_global or cambio_sutil:
                    cands.append((representante(ancla, k - 1),
                                  "estable" if cambio_global else "sutil"))
                    t_ult = k / fps
                    ancla = k
                k += 1
            i = j + 1
        else:
            # ---------------- tramo EN MOVIMIENTO ----------------
            j = i
            while j + 1 < N and not quieto[j + 1]:
                j += 1
            dur_b = (j - i + 1)
            if dur_b < min_b:
                # corte seco: los tramos quietos vecinos ya lo cubren
                i = j + 1
                continue

            # Scroll / zoom / animacion continua: capturas forzadas POR TIEMPO.
            # Esto es lo unico que cubre un scroll que NUNCA se detiene (un tramo
            # sin quietud no produciria ninguna pagina por si solo).
            #
            # Deliberadamente NO se usa la MAGNITUD del desplazamiento para
            # decidir cuando capturar. Medido en este entorno sobre un documento
            # de texto: la correlacion se satura en 1.000 y el desplazamiento
            # estimado oscila entre -44 y +43 filas de una muestra a la otra. El
            # perfil de un texto es cuasi-periodico (una linea cada pocas filas),
            # asi que cualquier multiplo del interlineado casa perfectamente y la
            # magnitud es ruido. Usarla multiplicaba por 5 el numero de paginas.
            # El BOOLEANO "esto es una traslacion" si es fiable, y solo se usa
            # para etiquetar y para muestrear mas denso durante un scroll.
            n_scroll = 0
            w0 = i
            for k in range(i, j + 1):
                if k > 0:
                    es, _, _ = desplazamiento(pc, pc, k, k - 1)
                    if not es:
                        es, _, _ = desplazamiento(pf, pf, k, k - 1)
                    if es:
                        n_scroll += 1
                hay_scroll = n_scroll >= 2
                # el zoom/pan genera los duplicados mas inutiles -> se muestrea
                # mas espaciado que un scroll, que si aporta contenido nuevo
                lim = max_mov if hay_scroll else int(max_mov * 1.5)
                if (k - w0 + 1) >= lim:
                    prev = max((c[0] for c in cands), default=None)
                    cands.append((rep_movimiento(w0, k, i, prev, lim),
                                  "desplazamiento" if hay_scroll else "movimiento"))
                    w0, n_scroll = k + 1, 0
            i = j + 1

    # ---------------- aceptacion cronologica + deduplicado global ----------------
    # El deduplicado usa el mismo criterio DUAL que la deteccion (si usara solo
    # la metrica global borraria justamente las paginas de cambio sutil) pero con
    # umbrales FIJOS, ajenos a --sensibilidad: DEDUP_FRAC / DEDUP_CELDAS. Medido:
    # con los umbrales de deteccion, --sensibilidad 3 fundia p01 con p04 y p02 con
    # p05 y perdia 4 paginas reales sin decir nada. La sensibilidad decide cuantos
    # CANDIDATOS se proponen; nunca puede borrar una pagina ya propuesta.
    #
    # Se compara contra TODAS las paginas ya aceptadas, no solo contra la
    # anterior: el objetivo declarado es reconstruir un DOCUMENTO, y una pagina
    # que vuelve a salir (una diapositiva de resumen que se repite) no debe
    # aparecer dos veces en el PDF. Pero esa segunda aparicion es informacion
    # real del video, asi que en vez de tirarla se ANOTA como "reaparicion" de
    # la pagina correspondiente y se publica en el manifiesto: el PDF queda
    # limpio y la linea de tiempo sigue reflejando el video.
    out = []
    descartes = []
    reapariciones = {}
    vistos = set()
    for idx, tag in sorted(cands):
        if idx in vistos:
            descartes.append((idx, tag, "repetido"))
            continue
        vistos.add(idx)
        dup = None
        for rep, _ in reversed(out):
            if (cmp_.frac(idx, rep) < DEDUP_FRAC
                    and cmp_.celdas_dedup(idx, rep) < DEDUP_CELDAS):
                dup = rep
                break
        if dup is None:
            out.append((idx, tag))
        else:
            reapariciones.setdefault(dup, []).append(idx / fps)
            descartes.append((idx, tag, "igual a %.2fs" % (dup / fps)))

    if debug:
        for idx, tag in sorted(cands):
            marca = "OK " if (idx, tag) in out else "   "
            extra = ""
            for i2, t2, mot in descartes:
                if i2 == idx and t2 == tag:
                    extra = "  <- descartado (%s)" % mot
                    break
            vlog(True, "%scand %7.2fs  %-14s%s" % (marca, idx / fps, tag, extra))

    info = dict(q_thr=q_thr, mad_thr=mad_thr, quietos=int(quieto.sum()),
                muestras=N, candidatos=len(cands), tras_dedup=len(out),
                reapariciones={k: sorted(v) for k, v in reapariciones.items()})
    return out, info


# ---------------------------------------------------------------------------
# 10. Extraccion a resolucion completa + segunda opinion con phash
# ---------------------------------------------------------------------------

def extraer_fotograma(video, ff, t, crop, destino, dur):
    t = max(0.0, min(t, max(0.0, dur - 0.05)))
    cmd = [ff, "-nostdin", "-v", "error", "-ss", "%.3f" % t, "-i", video,
           "-frames:v", "1", "-an", "-sn", "-dn"]
    if crop:
        cmd += ["-vf", crop]
    cmd += ["-q:v", "2", "-y", destino]
    r = correr(cmd, timeout=300)
    return r.returncode == 0 and os.path.exists(destino) and os.path.getsize(destino) > 0


def dedup_phash(rutas, debug=False):
    """Segunda opinion sobre las imagenes ya extraidas a RESOLUCION COMPLETA.

    A resolucion completa phash SI funciona bien en documentos (duplicado real
    ~14/256 bits, paginas distintas 72-94/256). Solo se eliminan repeticiones
    CONSECUTIVAS, para no borrar una pagina que reaparece legitimamente.

    Devuelve (indices_conservados, descartados_por_conservado). El segundo valor
    dice, para cada indice conservado, que indices se absorbieron en el: sirve
    para que el manifiesto anote esas repeticiones en vez de perderlas.
    """
    try:
        import imagehash
        from PIL import Image
    except Exception:
        return list(range(len(rutas))), {}

    keep = []
    absorbidos = {}
    prev = None
    for i, p in enumerate(rutas):
        try:
            with Image.open(p) as im:
                h = imagehash.phash(im.convert("L"), hash_size=16)
        except Exception:
            keep.append(i)
            prev = None
            continue
        if prev is not None and keep:
            d = h - prev
            if d <= PHASH_DUP:
                vlog(debug, "phash: descartada %s (distancia %d bits)"
                     % (os.path.basename(p), d))
                absorbidos.setdefault(keep[-1], []).append(i)
                continue
        keep.append(i)
        prev = h
    return keep, absorbidos


# ---------------------------------------------------------------------------
# 11. Salidas
# ---------------------------------------------------------------------------

def construir_pdf(imagenes, destino):
    import img2pdf
    try:
        layout = img2pdf.get_fixed_dpi_layout_fun((150, 150))
        datos = img2pdf.convert(imagenes, layout_fun=layout)
    except Exception:
        datos = img2pdf.convert(imagenes)
    with open(destino, "wb") as f:
        f.write(datos)


def extraer_audio(video, ff, destino):
    r = correr([ff, "-nostdin", "-v", "error", "-i", video, "-vn", "-sn", "-dn",
                "-c:a", "libmp3lame", "-b:a", "192k", "-y", destino], timeout=3600)
    if r.returncode != 0 or not os.path.exists(destino) or os.path.getsize(destino) == 0:
        return False, r.stderr.decode("utf8", "replace").strip()[:300]
    return True, ""


def escribir_manifiesto(salida, video, meta, paginas, cfg, crop, fps, dur, audio_ok):
    man = {
        "video_origen": os.path.abspath(video),
        "duracion_segundos": round(dur, 3),
        "duracion": hms(dur),
        "resolucion": "%dx%d" % (meta["w"], meta["h"]),
        "codec": meta["codec"],
        "recorte_aplicado": crop or "ninguno",
        "fps_analisis": fps,
        "sensibilidad": cfg["nivel"],
        "audio": "audio.mp3" if audio_ok else None,
        "pdf": "informe.pdf" if paginas else None,
        "total_paginas": len(paginas),
        "paginas": [
            {"numero": n,
             "archivo": arch,
             "segundo": round(t, 3),
             "tiempo": hms(t),
             "tipo": tag,
             # instantes en los que esta MISMA pagina vuelve a verse; no generan
             # otra imagen (el PDF no debe repetir paginas) pero se publican para
             # que la linea de tiempo siga reflejando el video
             "reapariciones": [{"segundo": round(x, 3), "tiempo": hms(x)}
                               for x in rep]}
            for n, (arch, t, tag, rep) in enumerate(paginas, 1)
        ],
    }
    with open(os.path.join(salida, "manifest.json"), "w", encoding="utf8") as f:
        json.dump(man, f, ensure_ascii=False, indent=2)

    tipos = {"estable": "pagina estable",
             "sutil": "cambio sutil",
             "desplazamiento": "desplazamiento (scroll)",
             "movimiento": "movimiento / zoom",
             "unica": "unica"}
    L = []
    L.append("=" * 66)
    L.append("  INFORME EXTRAIDO DEL VIDEO")
    L.append("=" * 66)
    L.append("")
    L.append("Video original : %s" % os.path.basename(video))
    L.append("Duracion       : %s  (%dx%d, %s)"
             % (hms(dur), meta["w"], meta["h"], meta["codec"]))
    L.append("Recorte        : %s" % (crop or "ninguno (sin bandas negras)"))
    L.append("Sensibilidad   : %d de 10" % cfg["nivel"])
    L.append("Muestreo       : %g imagenes por segundo" % fps)
    L.append("")
    L.append("Paginas encontradas: %d" % len(paginas))
    L.append("")
    if paginas:
        L.append("  N.   Momento    Archivo                  Tipo")
        L.append("  " + "-" * 62)
        for n, (arch, t, tag, rep) in enumerate(paginas, 1):
            L.append("  %-4d %-10s %-24s %s"
                     % (n, hms(t), arch, tipos.get(tag, tag)))
            if rep:
                L.append("       %s vuelve a verse en: %s"
                         % (" " * 10, ", ".join(hms(x) for x in rep[:8])
                            + (" ..." if len(rep) > 8 else "")))
    else:
        L.append("  (no se detecto ninguna pagina)")
    L.append("")
    if any(rep for _, _, _, rep in paginas):
        L.append("Nota: algunas paginas se muestran mas de una vez en el video. El PDF")
        L.append("      incluye cada pagina UNA sola vez (es un documento), pero arriba")
        L.append("      quedan anotados todos los momentos en que aparece.")
        L.append("")
    L.append("Archivos generados:")
    if paginas:
        L.append("  informe.pdf   -> el documento reconstruido, todas las paginas en orden")
        L.append("  pagina_XXX.jpg-> cada pagina por separado, en calidad original")
    L.append("  audio.mp3     -> %s" % ("la narracion completa" if audio_ok
                                        else "NO DISPONIBLE (el video no tiene audio)"))
    L.append("  manifest.json -> los mismos datos en formato para programas")
    L.append("  resumen.txt   -> este archivo")
    L.append("")
    L.append("-" * 66)
    L.append("SI ALGO NO ESTA BIEN")
    L.append("-" * 66)
    L.append("Falta alguna pagina:")
    L.append("  vuelve a ejecutar con  --sensibilidad 8  (o hasta 10). Saldran mas")
    L.append("  imagenes, algunas repetidas, pero es mucho mas dificil que se")
    L.append("  escape una pagina.")
    L.append("")
    L.append("Sobran imagenes casi iguales:")
    L.append("  lo mas seguro es BORRAR A MANO las que sobran: son archivos")
    L.append("  sueltos y el PDF se puede volver a armar con el resto.")
    L.append("  Tambien puedes probar  --sensibilidad 4  , que agrupa mas.")
    L.append("  AVISO: cuanto mas BAJES la sensibilidad, mas riesgo hay de que dos")
    L.append("  paginas que se parecen (misma cabecera, mismo pie) se cuenten como")
    L.append("  una sola y una de ellas desaparezca del PDF SIN AVISO. El valor 5")
    L.append("  que viene de fabrica es el comprobado; por debajo de 4 no se")
    L.append("  recomienda bajar.")
    L.append("")
    L.append("  Compara siempre el numero de paginas de informe.pdf con las que")
    L.append("  esperabas del informe original antes de dar el trabajo por bueno.")
    L.append("")
    with open(os.path.join(salida, "resumen.txt"), "w", encoding="utf8") as f:
        f.write("\n".join(L))


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def construir_parser():
    p = argparse.ArgumentParser(
        prog="extraer_informe.py",
        description="Extrae las paginas de un documento mostrado en un video, "
                    "arma un PDF y separa el audio.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Ejemplos:
  python3 extraer_informe.py informe.mp4
  python3 extraer_informe.py informe.mp4 --salida ~/Escritorio/informe
  python3 extraer_informe.py informe.mp4 --sensibilidad 8
  python3 extraer_informe.py informe.mp4 --sin-audio
""")
    p.add_argument("video", help="archivo de video de entrada")
    p.add_argument("--salida", default="./informe_extraido",
                   help="carpeta donde dejar los resultados "
                        "(por defecto: ./informe_extraido)")
    p.add_argument("--sensibilidad", type=int, default=5, metavar="N",
                   help="1 a 10. Mas alto = mas capturas (y mas repetidas); mas "
                        "bajo = menos repeticiones, pero con riesgo de agrupar dos "
                        "paginas parecidas en una. Por defecto: 5 (comprobado). "
                        "Si falta alguna pagina, sube a 8.")
    p.add_argument("--sin-audio", action="store_true", dest="sin_audio",
                   help="no extraer el audio a MP3")
    p.add_argument("--fps", type=float, default=None, metavar="N",
                   help="imagenes por segundo a analizar (por defecto 4, se reduce "
                        "solo en videos muy largos)")
    p.add_argument("--debug", action="store_true",
                   help="mensajes tecnicos y conservar los archivos temporales")
    return p


def main(argv=None):
    args = construir_parser().parse_args(argv)

    if not (1 <= args.sensibilidad <= 10):
        morir(EXIT_ARGS, "--sensibilidad debe estar entre 1 y 10 "
                         "(has puesto %s)." % args.sensibilidad)
    if args.fps is not None and not (0.2 <= args.fps <= 30):
        morir(EXIT_ARGS, "--fps debe estar entre 0.2 y 30 (has puesto %s)." % args.fps)

    ff, fp = buscar_herramientas()
    cfg = perfil_sensibilidad(args.sensibilidad)

    log("")
    log("=" * 62)
    log("  EXTRACTOR DE INFORME  -  paginas + PDF + audio")
    log("=" * 62)

    if args.sensibilidad < 4:
        log("")
        log("  AVISO: has elegido --sensibilidad %d. Con valores bajos se agrupan"
            % args.sensibilidad)
        log("  mas las imagenes parecidas, y dos paginas que compartan cabecera y")
        log("  pie pueden acabar contadas como una sola. Si el PDF sale con menos")
        log("  paginas de las que esperas, vuelve a ejecutar con --sensibilidad 5")
        log("  (el valor de fabrica) o con 8.")

    # ---- 1. sondeo ----
    log("\n[1/7] Revisando el video...")
    meta = sondear(args.video, fp)
    dur, W, H = meta["dur"], meta["w"], meta["h"]
    log("      Duracion: %s   Resolucion: %dx%d   Codec: %s"
        % (hms(dur), W, H, meta["codec"]))
    log("      Pista de audio: %s" % ("si" if meta["audio"] else "NO"))

    fps = args.fps
    if fps is None:
        fps = 4.0
        if dur * fps > MAX_SAMPLES:
            fps = max(1.0, MAX_SAMPLES / dur)
            log("      Video largo: se analizara a %.1f imagenes/s para no agotar "
                "la memoria." % fps)
    elif dur * fps > MAX_SAMPLES:
        fps = max(0.5, MAX_SAMPLES / dur)
        log("      AVISO: --fps reducido a %.2f para no agotar la memoria." % fps)

    salida = os.path.abspath(os.path.expanduser(args.salida))
    try:
        os.makedirs(salida, exist_ok=True)
    except OSError as e:
        morir(EXIT_ARGS, "no se pudo crear la carpeta de salida '%s': %s" % (salida, e))

    tmp = tempfile.mkdtemp(prefix="informe_")
    t_ini = time.time()
    try:
        # ---- 2. recorte ----
        log("\n[2/7] Buscando bandas negras y bordes que sobran...")
        crop = detectar_recorte(args.video, ff, dur, W, H, args.debug)
        if crop:
            cw, ch, cx, cy = (int(v) for v in crop.split("=")[1].split(":"))
            log("      Se recortara a %dx%d (quitando %d px de ancho y %d de alto)."
                % (cw, ch, W - cw, H - ch))
        else:
            log("      No hay bandas que recortar; se usa la imagen completa.")

        # ---- 3. analisis ----
        log("\n[3/7] Analizando el video a %g imagenes/s (una sola pasada)..." % fps)
        S, pf, pc, mov = analizar(args.video, ff, crop, fps, dur, args.debug)
        N = len(S)
        log("      %d muestras analizadas (%.0f MB en memoria)."
            % (N, (S.nbytes + pf.nbytes + pc.nbytes) / 1e6))

        # ---- 4. mascara ----
        log("\n[4/7] Localizando webcam, cursor, reloj y otras zonas que se mueven...")
        cmp_ = Comparador(S, cfg)
        n_mask = cmp_.aprender_mascara(args.debug)
        if n_mask:
            log("      Se ignoraran %d de %d zonas de la imagen (%.0f%%) por estar "
                "siempre en movimiento." % (n_mask, NTF, 100.0 * n_mask / NTF))
        else:
            log("      No hay zonas permanentemente animadas; se usa toda la imagen.")

        # ---- 5. deteccion ----
        log("\n[5/7] Detectando los cambios de pagina...")
        paginas_idx, info = detectar_paginas(cmp_, pf, pc, mov, fps, cfg, args.debug)
        vlog(args.debug, "umbral quietud=%.4f  umbral MAD=%.3f  quietas=%d/%d  "
                         "candidatos=%d  tras dedup=%d"
             % (info.get("q_thr", 0), info.get("mad_thr", 0), info.get("quietos", 0),
                N, info.get("candidatos", 0), info.get("tras_dedup", 0)))

        if not paginas_idx:
            # nunca dejar al usuario con las manos vacias
            log("      AVISO: no se detecto ningun cambio de pagina. Se guardara "
                "un unico fotograma representativo.")
            mejor = int(np.argmax(cmp_.contraste)) if N else 0
            paginas_idx = [(mejor, "unica")]

        log("      %d paginas candidatas." % len(paginas_idx))

        # ---- 6. extraccion a resolucion completa ----
        log("\n[6/7] Extrayendo cada pagina en calidad original...")
        reap = info.get("reapariciones", {}) or {}
        tmp_imgs = []
        for n, (idx, tag) in enumerate(paginas_idx, 1):
            t = idx / fps
            dst = os.path.join(tmp, "cand_%04d.jpg" % n)
            if extraer_fotograma(args.video, ff, t, crop, dst, dur):
                tmp_imgs.append((dst, t, tag, list(reap.get(idx, []))))
            else:
                log("      AVISO: no se pudo extraer el fotograma de %s, se omite."
                    % hms(t))
            if n % 10 == 0 or n == len(paginas_idx):
                log("      %d/%d..." % (n, len(paginas_idx)))

        if not tmp_imgs:
            morir(EXIT_PROC, "no se pudo extraer ninguna imagen del video.")

        keep, absorbidos = dedup_phash([p for p, _, _, _ in tmp_imgs], args.debug)
        if absorbidos:
            # la repeticion no se pierde: pasa a ser una "reaparicion" de la que
            # si se conserva, y quedara anotada en el manifiesto
            for k, ids in absorbidos.items():
                tmp_imgs[k][3].extend(tmp_imgs[i][1] for i in ids)
            log("      Se descartaron %d repeticiones casi identicas."
                % sum(len(v) for v in absorbidos.values()))
        tmp_imgs = [tmp_imgs[i] for i in keep]

        # limpiar paginas anteriores de la carpeta de salida
        for viejo in sorted(os.listdir(salida)):
            if re.match(r"^pagina_\d+\.jpg$", viejo):
                try:
                    os.remove(os.path.join(salida, viejo))
                except OSError:
                    pass

        paginas = []
        finales = []
        for n, (src, t, tag, rep) in enumerate(tmp_imgs, 1):
            arch = "pagina_%03d.jpg" % n
            dst = os.path.join(salida, arch)
            shutil.copyfile(src, dst)
            finales.append(dst)
            paginas.append((arch, t, tag, sorted(rep)))
        log("      %d paginas finales." % len(paginas))
        n_reap = sum(len(r) for _, _, _, r in paginas)
        if n_reap:
            log("      %d de esas paginas vuelven a verse mas tarde en el video; "
                "no se repiten en el PDF, quedan anotadas en el resumen." % n_reap)

        # ---- 7. PDF, audio, manifiesto ----
        log("\n[7/7] Armando el PDF, el audio y el resumen...")
        pdf = os.path.join(salida, "informe.pdf")
        try:
            construir_pdf(finales, pdf)
            log("      informe.pdf  (%d paginas, %.1f MB)"
                % (len(finales), os.path.getsize(pdf) / 1e6))
        except Exception as e:
            log("      AVISO: no se pudo crear el PDF (%s). Las imagenes si estan "
                "guardadas." % e)

        audio_ok = False
        if args.sin_audio:
            log("      Audio omitido (--sin-audio).")
        elif not meta["audio"]:
            log("      AVISO: este video NO tiene pista de audio; se omite audio.mp3.")
        else:
            mp3 = os.path.join(salida, "audio.mp3")
            audio_ok, err = extraer_audio(args.video, ff, mp3)
            if audio_ok:
                log("      audio.mp3  (%.1f MB)" % (os.path.getsize(mp3) / 1e6))
            else:
                log("      AVISO: no se pudo extraer el audio (%s)." % err)

        escribir_manifiesto(salida, args.video, meta, paginas, cfg, crop, fps,
                            dur, audio_ok)

        el = time.time() - t_ini
        log("")
        log("=" * 62)
        log("  LISTO en %s  (%.1f veces mas rapido que el video)"
            % (hms(el), dur / max(el, 1e-6)))
        log("  Carpeta: %s" % salida)
        log("  %d paginas  ->  informe.pdf" % len(paginas))
        log("=" * 62)
        log("")
        if args.debug:
            log("Carpeta temporal conservada (--debug): %s" % tmp)
        return 0

    except KeyboardInterrupt:
        morir(EXIT_PROC, "proceso interrumpido por el usuario.")
    except SystemExit:
        raise
    except MemoryError:
        morir(EXIT_PROC, "memoria insuficiente. Prueba con --fps 2.")
    except Exception as e:
        if args.debug:
            import traceback
            traceback.print_exc()
        morir(EXIT_PROC, "fallo inesperado durante el proceso: %s" % e)
    finally:
        if not args.debug:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
