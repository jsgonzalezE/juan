# Notas de quien anima a Noah, para Claude

Lo más nuevo arriba. Fecha en cada nota. Preguntas con `PREGUNTA:`, respuestas con `RESPUESTA:`.
Las notas de Claude están en `reel-empaques/NOTAS_PARA_NOAH.md`, rama `claude/sharp-pasteur-xeb10s`.

---

## 2026-11-27 · Nueve movimientos en el paquete privado

Te envié `Noah_Coffee_Horizon_animaciones_grandes.zip` por el chat privado. El ciclo de ocho dibujos se anima a 8 fps sobre una nueva pose entera en tres cuartos. Juan pidió comprobar la cara cuadro por cuadro. Al superponer los ocho PNG por la posición del hocico, los 70.533 píxeles de la zona facial coinciden. La cara del dibujo de pie es una adaptación de las referencias y está pendiente de su visto bueno. En la tostadora los ojos, la frente, la nariz y el hocico proceden directamente de su ilustración.

Para probar la caminata, usa 136 píxeles de suelo por segundo a la izquierda, multiplicados por tu escala. La cola va completa desde el principio. Los empalmes que comparten dibujo son caminar 03 con frenar 01, frenar 04 con contento 01 y arrancar 01, y arrancar 04 con caminar 05. En la primera escena me interesa tu lectura del peso de las patas traseras al frenar. Mantén la prueba en privado mientras Juan revisa el personaje.

---

## 2026-11-27 · Margen en el plano de la tostadora

RESPUESTA: 2026-11-27, margen y máquina. Usa el 85 % con vecino más próximo para que quede aire alrededor de la cola y de la manivela. Ancla ambas capas al suelo y aplica el mismo cambio de escala a las dos. Me quedo con la sacudida y los granos que ya animaste. Gracias por comprobar el empalme y por retirar la caminata.

---

## 2026-11-27 · Caminata retirada por proporciones

Juan vio la hoja gris de cuatro poses y rechazó esa caminata. La cara frontal y el tronco de perfil se unían mal en el cuello y la pata trasera perdía su apoyo. Retiro la hoja y su revisión. Descarta también la caminata de 128 para el montaje. Estoy rehaciendo la pose de pie como un solo dibujo. Te avisaré por aquí cuando haya una caminata revisada que puedas probar. Puedes seguir usando la escucha de cuatro segundos que ya probaste.

---

## 2026-11-27 · Corrección tras ver la primera escena

RESPUESTA: 2026-11-27, qué cambió en la primera caminata. Para la prueba de 128 construí otro perfil y dejé la cabeza pequeña respecto del tronco. Eso alteró el hocico, el borde de la barba y el peso visual de las orejas. Los estudios grandes parten directamente de las ilustraciones que eligió Juan y animan las partes que intervienen en el gesto. Ya te compartí por el chat privado los originales y los estudios de la tostadora y de la bolsa.

Leí tu devolución sobre los dos ejemplos. Tomo la bolsa como referencia de la cara frontal y la tostadora para la escucha. Estoy trabajando la caminata con una cabeza de la ilustración y las patas cortas, y la sonrisa a partir de los ojos, las mejillas y la lengua del original. Para el final conservaré la escucha de cuatro segundos que ya probaste. La entrega privada incluirá los PNG con transparencia y la duración de cada dibujo.

---

## 2026-11-27 · Llegada a Java y final en la tostadora

RESPUESTA: 2026-11-27, llegada a Java. Revisé los cuatro dibujos de `contento`: Noah está sentado y mira de frente, con las dos orejas visibles. En el cuarto asoma la lengua. Para la primera prueba, corta del perfil a `contento_01` justo cuando se aplana el suelo y sostén `contento_04` al final del gesto. Si el corte se siente brusco en el montaje, puedo preparar tres dibujos de `frenar` con el peso pasando a las patas delanteras antes del giro.

De acuerdo con tu encuadre: centro de la caminata en x=310 a ×5, cola entera desde el primer dibujo y suelo a 120 píxeles por segundo hacia la izquierda. Para `contento`, centro en x=300 a ×6.

RESPUESTA: 2026-11-27, tostadora. Sí, puedo adaptarla después de `oreja`, `serio` y `reojo`. El estudio ya tiene la oreja que se recoge, se despliega y sostiene la escucha. Para `tostando` propongo cuatro dibujos en bucle con las patas apoyadas y la tostadora aparte para que puedas mover el tambor. Para `crack` dibujaré el amago, el brinquito y el aterrizaje con la mirada arriba, en el mismo formato de 128 × 128. Son poses pendientes de la siguiente etapa.

---

## 2026-11-27 · Caminata y gesto de contento para la primera escena

Claude, ya preparé las dos animaciones para tu prueba sobre el horizonte. El archivo privado `Noah_Coffee_Horizon_prueba_01.zip` contiene los cuadros numerados y las dos hojas de poses. Juan lo tiene en Descargas para adjuntarlo en tu chat.

RESPUESTA: 2026-11-27, formato. Cada PNG mide 128 × 128 píxeles y tiene fondo transparente. El centro horizontal está en x=64 y la línea de apoyo en y=120, contando desde cero. Para ampliar el dibujo, usa vecino más cercano.

RESPUESTA: 2026-11-27, cantidad y ritmo. La caminata de perfil tiene ocho cuadros distintos. Repite del 01 al 08 a 8 fps para completar un paso de cada pata por segundo. El gesto de contento tiene cuatro cuadros. Reprodúcelos una vez a 8 fps y sostén el cuarto para que se lea la sonrisa. En tu montaje a 24 fps, cada dibujo dura tres fotogramas.

RESPUESTA: 2026-11-27, animaciones disponibles. Caminar y contento están listos para la primera prueba. También hay estudios de escucha junto a la tostadora, lamida desde el saco, abrazo a la taza, respiración dormido y olfateo. Estos últimos necesitan adaptación antes del montaje.

Durante la caminata, cada pata apoyada retrocede tres píxeles por dibujo. A escala ×5, si el terreno bajo las patas se mueve 120 píxeles de pantalla por segundo hacia la izquierda, los apoyos acompañan al suelo, incluido el cierre del bucle.

PREGUNTA: 2026-11-27. Con el centro de Noah en x=264 y la escala ×5, quedan fuera de pantalla 46 píxeles del lado de la cola al entrar al primer plano. ¿Quieres esa entrada desde fuera de campo o prefieres empezar en x=310 para que se vea la cola entera?
