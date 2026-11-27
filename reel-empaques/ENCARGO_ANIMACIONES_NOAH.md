# Encargo: animaciones de Noah para el reel

Para quien esté haciendo las animaciones de Noah. Va junto con la lámina
`idea_d_mezcla_pixel.jpg`, que muestra cuadro por cuadro dónde entra cada animación.

## El video en dos líneas

Reel vertical de 20 segundos, en pixel art. Cada variedad tiene una ficha con su color. La ficha
empieza apagada; Noah ladra, con cada ladrido aparecen letras del nombre y, al completarlo, todo se
enciende con el color del empaque. Son cuatro variedades y un cierre con el logo.

En la lámina Noah aparece con las ilustraciones fijas que ya existen. Son marcadores: hay que
reemplazarlos por las animaciones de esta lista.

## Qué hay que mejorar en Noah

No he visto las animaciones que llevas, así que estos son los criterios generales, no una
corrección de tu trabajo.

1. **Que sea el mismo Noah de las 11 ilustraciones aprobadas** (carpeta `05_noah_pixel_art`).
   Rasgos que no pueden cambiar:
   - Pelaje crema, contorno café muy oscuro.
   - Orejas negras, largas y caídas.
   - Copete amarrado arriba con una cinta clara.
   - Marca oscura en la frente, en forma de "Y".
   - Manchas negras en el lomo y la cadera.
   - Cabeza grande: más o menos la mitad del alto total.
   - Expresión amable; ojos cerrados en arco cuando está contento.
2. **Pixel art de verdad.** En las ilustraciones actuales los "pixeles" tienen tamaños distintos.
   En las animaciones todos los pixeles deben medir lo mismo, sin bordes suavizados ni degradados.
3. **Que no cambie de un cuadro a otro.** Mismas manchas, mismo tamaño de cabeza y mismo copete en
   todos los cuadros de una animación. Solo se mueve lo que la acción pide.
4. **Ni más realista ni más detallado.** El cliente rechazó una versión anterior porque "daba
   miedo" y "no se parecía al real".

## Formato

| Qué | Cómo |
|---|---|
| Tamaño de cada cuadro | 96 × 96 pixeles reales |
| Tamaño de Noah | entre 60 y 68 pixeles de alto cuando está sentado o de pie |
| Posición | centrado, con las patas siempre en la misma fila (fila 88), mirando a la derecha |
| Fondo | transparente; sin sombra en el piso |
| Colores | 12 como máximo, tomados con gotero de las ilustraciones aprobadas |
| Velocidad | pensadas para 8 cuadros por segundo |
| Archivos | PNG sin ampliar, uno por cuadro: `noah_ladrar_01.png`, `noah_ladrar_02.png`… |
| Además | una hoja con todos los cuadros de cada animación, para revisarla de un vistazo |

Colores de referencia, aproximados: contorno y orejas `#261414`, pelaje `#FCF4E8`, sombra del
pelaje `#E6D6C2`.

No hace falta ampliar los cuadros: se amplían seis veces en el montaje, sin suavizado.

## Animaciones, por prioridad

| N.º | Animación | Cuadros | Qué hace | Dónde se usa |
|---|---|---|---|---|
| 1 | Ladrar | 4 | Sentado: toma aire, ladra con la boca abierta y un saltito, vuelve | Escenas 2 a 6. Es la más importante: cada ladrido pone letras |
| 2 | Reposo sentado | 4 a 6, en bucle | Respira y mueve la cola | Todas las escenas, entre acciones |
| 3 | Celebrar | 6 | Saltito corto de alegría cuando se enciende la ficha | Escenas 3, 4 y 5 |
| 4 | Mirar de reojo | 3 | Gira un poco la cabeza y entrecierra los ojos; se queda así | Escena 6, cuando ve al perro pintado en el empaque |
| 5 | Entrar caminando | 6 a 8, en bucle | Camina de perfil | Escena 1 |
| 6 | Dormirse | 4 + 4 en bucle | Se echa; luego respira dormido | Escena 8 |
| 7 | Olfatear (opcional) | 4 | Estira el hocico y olfatea | Reserva, por si sobra tiempo |

Si solo alcanza para tres, que sean las tres primeras.

## Si se escoge la otra versión: el recorrido

Hay una segunda lámina, `idea_e_recorrido.jpg`. Ahí Noah no ladra letras: camina de izquierda a
derecha, se detiene en cada empaque y al final llega a la tostadora. Para esa versión cambia la
prioridad:

| N.º | Animación | Cuadros | Qué hace |
|---|---|---|---|
| 1 | Caminar de perfil | 6 a 8, en bucle | Es la más importante: Noah camina casi todo el video. Debe poder repetirse sin salto |
| 2 | Frenar y sentarse | 4 | Pasa de caminar a sentado al llegar a cada empaque |
| 3 | Reposo sentado | 4 a 6, en bucle | Respira y mueve la cola mientras presenta |
| 4 | Levantarse y arrancar | 3 | De sentado a caminar otra vez |
| 5 | Mirar de reojo | 3 | En el último empaque, al ver al perro pintado |
| 6 | Junto a la tostadora | 4, en bucle | Sentado, oreja levantada, como en la ilustración aprobada de la tostadora |

El formato es el mismo de arriba.

## Qué no hacer

- No cambiar el diseño de Noah ni agregarle accesorios.
- No incluir texto, fondo ni objetos dentro de los cuadros.
- No entregar video: se necesitan los cuadros sueltos.
