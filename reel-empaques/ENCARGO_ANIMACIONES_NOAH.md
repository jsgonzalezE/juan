# Encargo: animaciones de Noah para el reel "Coffee Horizon"

Para quien esté haciendo las animaciones de Noah (ChatGPT / Codex). Este archivo es el punto de
encuentro: aquí está qué hace falta, en qué formato y dónde dejarlo para que encaje con los fondos
sin retoques.

## Cómo trabajamos juntos

| Quién | Qué hace |
|---|---|
| ChatGPT / Codex | Dibuja y anima a Noah: los cuadros de cada acción |
| Claude | Fondos, empaques en pixel art, cielos, textos, logo, montaje y sonido |

**Canal:** este repositorio de GitHub, `jsgonzalezE/juan`.

- Claude publica en la rama `claude/sharp-pasteur-xeb10s`, carpeta `reel-empaques/`. Este archivo
  siempre tiene la última versión del encargo.
- Las animaciones de Noah van en una rama aparte llamada `codex/noah`, dentro de
  `reel-empaques/noah_anim/`, con esta forma:

```
reel-empaques/noah_anim/
  caminar/noah_caminar_01.png, noah_caminar_02.png, ...
  contento/noah_contento_01.png, ...
  NOTAS.md        <- dudas, lo que falta, lo que cambió
```

- Claude lee esa rama, monta las animaciones sobre los fondos y deja sus comentarios en
  `reel-empaques/NOTAS_PARA_NOAH.md` de su propia rama.
- Si no se puede usar GitHub, sirve igual un zip con la misma estructura de carpetas.

El repositorio es público. Mientras siga así, no subir imágenes de los empaques.

## El video en dos líneas

Reel vertical de 20 segundos (1080 × 1920), en pixel art. Noah camina sobre un horizonte curvo,
que es la superficie de una taza de café. Cuando llega a cada empaque el piso se aplana y la cámara
se acerca; el cielo toma el color de esa variedad. Son cuatro empaques. Al final llega a la
tostadora, suena el primer "crack" y el logo cierra el video.

## Qué hay que cuidar en Noah

1. **Que sea el mismo Noah de las 11 ilustraciones aprobadas.** Rasgos que no pueden cambiar:
   - Pelaje crema, contorno café muy oscuro.
   - Orejas negras, largas y caídas.
   - Copete amarrado arriba con una cinta clara.
   - Marca oscura en la frente, en forma de "Y".
   - Manchas negras en el lomo y la cadera.
   - Cabeza grande: más o menos la mitad del alto total.
   - Expresión amable; ojos cerrados en arco cuando está contento.
2. **Pixel art de verdad.** Todos los pixeles del mismo tamaño, sin bordes suavizados ni degradados.
3. **Que no cambie de un cuadro a otro.** Mismas manchas, mismo tamaño de cabeza y mismo copete en
   todos los cuadros. Solo se mueve lo que la acción pide.
4. **Un solo vestuario.** Noah sin accesorios en todo el video. La única excepción es la escena de
   la tostadora, donde puede llevar la pañoleta de la ilustración aprobada.
5. **Ni más realista ni más detallado.** Una versión anterior se rechazó porque "daba miedo" y
   "no se parecía al real".

## Formato

| Qué | Cómo |
|---|---|
| Tamaño de cada cuadro | 128 × 128 pixeles reales |
| Tamaño de Noah | entre 100 y 104 pixeles de alto cuando está de pie o sentado |
| Posición | centrado, con las patas siempre en la fila 120, mirando a la derecha |
| Fondo | transparente; sin sombra en el piso |
| Colores | 12 como máximo, tomados con gotero de las ilustraciones aprobadas |
| Velocidad | pensadas para 8 cuadros por segundo |
| Archivos | PNG sin ampliar, uno por cuadro: `noah_caminar_01.png`, `noah_caminar_02.png`… |
| Además | una hoja con todos los cuadros de cada animación, para revisarla de un vistazo |

Colores de referencia, aproximados: contorno y orejas `#261414`, pelaje `#FCF4E8`, sombra del
pelaje `#E6D6C2`.

No hace falta ampliar: en el montaje cada cuadro se amplía 6 veces en las llegadas y 5 veces en
las caminatas, sin suavizado.

## Animaciones, por prioridad

| N.º | Carpeta | Cuadros | Qué hace | Dónde se usa |
|---|---|---|---|---|
| 1 | `caminar` | 6 a 8, en bucle | Camina de perfil, en el sitio. Debe repetirse sin salto | Cuadro 1 y entre cada llegada: es lo que más se ve |
| 2 | `frenar` | 3 | De caminar a quieto, girando hacia la cámara | Al llegar a cada empaque |
| 3 | `contento` | 3 a 4 | Sonríe con la lengua afuera; puede mover la cola | Llegada a Java |
| 4 | `oreja` | 3 a 4 | Levanta una oreja, atento | Llegada a Castillo |
| 5 | `serio` | 3 a 4 | Frunce el ceño. Solo se ven la cabeza y las patas delanteras: está asomado detrás del horizonte | Llegada a Geisha |
| 6 | `reojo` | 3 a 4 | Mira de lado con desconfianza | Llegada a Bourbon (el empaque tiene un perro pintado) |
| 7 | `arrancar` | 3 | De quieto a caminar otra vez | Al salir de cada empaque |
| 8 | `tostando` | 4, en bucle | Sentado junto a la tostadora, oreja levantada, como en la ilustración aprobada | Final |
| 9 | `crack` | 3 | Brinquito de sobresalto y mira hacia arriba | Final, cuando suena el primer "crack" |

Si solo alcanza para tres, que sean `caminar`, `contento` y `tostando`.

La tostadora puede ir dibujada dentro de los cuadros de `tostando` y `crack`, o aparte en
`tostadora/`. Si va aparte, mejor: así el tambor puede girar por su cuenta.

## Dónde va Noah en cada cuadro

Medidas en pixeles de pantalla (1080 × 1920). "Patas" es la fila donde pisa.

| Cuadro | Momento | Animación | Alto de Noah | Patas en y | Centro en x |
|---|---|---|---|---|---|
| 1 | Amanece, camina (horizonte curvo) | `caminar` | 510 | 1298 | 264 |
| 2 | Llegada a Java (plano) | `frenar` → `contento` | 640 | 1412 | 270 |
| 3 | Camina al siguiente (curvo) | `arrancar` → `caminar` | 510 | 1280 | 540 |
| 4 | Llegada a Castillo | `frenar` → `oreja` | 600 | 1412 | 264 |
| 5 | Llegada a Geisha | `serio` (asomado) | 420 | 1434 | 282 |
| 6 | Llegada a Bourbon | `frenar` → `reojo` | 590 | 1412 | 270 |
| 7 | La tostadora, primer "crack" | `tostando` → `crack` | 615 | 1412 | 516 |
| 8 | Los granos arman el logo | `tostando` (mirando arriba) | 615 | 1412 | 516 |
| 9–10 | Solo el logo | — | — | — | — |

## Qué no hacer

- No cambiar el diseño de Noah.
- No incluir texto, fondo ni empaques dentro de los cuadros.
- No entregar video: se necesitan los cuadros sueltos.
