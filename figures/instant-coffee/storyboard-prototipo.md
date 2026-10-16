# Prototipo del vídeo: tomas, cámara y prompts para ChatGPT

Cómo funciona: tú generas **una imagen por toma** en ChatGPT con los prompts de abajo, me las pasas con el
nombre indicado, y yo las convierto en vídeo con el movimiento de cámara de cada toma (paneo, acercamiento,
inclinación), los rótulos y los cortes. El resultado es un prototipo (animatic) para probar ritmo, orden y
texto antes de hacer la versión final.

Versión corta (Reel / Shorts): tomas 1 a 11 sin las "A/B", unos **76 s**. Versión larga (YouTube): con 5A y 5B, unos **89 s**.

---

## Paso 1 · Estilo (pégalo una sola vez al principio del chat)

```
From now on, every image in this chat uses exactly this style:
Clean technical 3D render of industrial coffee-processing machinery, CUTAWAY view so the inside of the
machine is visible, brushed stainless steel and glass, soft studio lighting, dark charcoal background
(#141414), subtle floor reflection. Near-monochrome: the coffee itself (beans, liquid, syrup, granules)
is the only strong colour, a warm amber-brown. No text, no labels, no logos, no people, no watermarks.
Composition: the machine centred with EMPTY MARGINS on both sides (about 15 % each), nothing important
touching the edges, so a camera can move over the picture later. Output 16:9 at the highest resolution.
```

Si prefieres fotografía real en vez de render, cambia la primera frase por:
`Clean industrial photograph, real food-processing plant, stainless steel equipment, soft diffused light,`
y mantén el resto igual.

## Paso 2 · Las tomas (un prompt cada una)

Después de cada imagen pide también: **"Recompose the same scene for 9:16, subject centred, keep empty
space at the bottom"** y guárdala como `shot-NN-v.png`. Nombra los archivos exactamente así.

| Toma | Archivo | Dur. | Cámara (la aplico yo) | Rótulo en pantalla |
|------|---------|------|------------------------|--------------------|
| 1 | shot-01 | 4 s | Acercamiento lento | How instant coffee is made |
| 2 | shot-02 | 8 s | Paneo izquierda → derecha siguiendo los granos | 1 · Roasting |
| 3 | shot-03 | 6 s | Acercamiento a los rodillos | 2 · Grinding |
| 4 | shot-04 | 9 s | Inclinación de abajo (salida) a arriba (entrada de agua) | 3 · Extraction |
| 5 | shot-05 | 5 s | Acercamiento lento | 4 · Clarification |
| 6 | shot-06 | 8 s | Paneo siguiendo los efectos del evaporador | 5 · Concentration |
| 5A | shot-06a | 8 s | Inclinación de arriba (atomizador) a abajo (polvo) · opcional | 5A · Spray drying |
| 5B | shot-06b | 5 s | Acercamiento · opcional | 5B · Agglomeration |
| 7 | shot-07 | 8 s | Paneo siguiendo la banda | 6 · Freezing |
| 8 | shot-08 | 5 s | Acercamiento al rotor | 7 · Granulating |
| 9 | shot-09 | 10 s | Alejamiento: de las bandejas a toda la cámara | 8 · Freeze drying |
| 10 | shot-10 | 7 s | Paneo siguiendo la línea de frascos | 9 · Packing |
| 11 | shot-11 | 6 s | Acercamiento lento | 120 g → 41 g · about 21 cups |

### shot-01 · Portada
```
A glass jar of instant coffee granules, open, with a few granules spilled beside it, next to a white cup of
hot coffee with a thin curl of steam, on a dark surface. Centred, lots of empty background above and around.
```

### shot-02 · Roasting (paneo izquierda → derecha)
```
Cutaway of an industrial DRUM ROASTER seen from the side. On the LEFT, a hopper pours pale green coffee
beans into the drum; inside the rotating drum the beans tumble and change colour from green to brown
across the frame; on the RIGHT, dark brown roasted beans pour out of the door onto a round cooling tray
with a rotating arm. A burner glows under the drum and a chimney rises above it. The machine spans the
whole width so the camera can travel along it.
```

### shot-03 · Grinding (acercamiento)
```
Cutaway of an industrial ROLLER MILL: a hopper of roasted brown beans at the top feeding two corrugated
steel rollers turning towards each other in the middle of the frame, coarse ground coffee falling out
below into a chute. The two rollers are the hero of the image, centred, with room around them.
```

### shot-04 · Extraction (inclinación de abajo a arriba)
```
A battery of six tall vertical stainless-steel PERCOLATION COLUMNS, cutaway on the nearest one so the
packed bed of dark ground coffee inside is visible. Clear hot water enters through a pipe at the TOP, dark
amber coffee liquor leaves through a pipe at the BOTTOM into a collecting tank. Tall composition: the
columns fill the height, pipe outlet at the bottom edge area, water inlet near the top edge area.
```

### shot-05 · Clarification (acercamiento)
```
Cutaway of an industrial DISC CENTRIFUGE: a spinning bowl with a stack of conical discs inside, cloudy
coffee liquor entering from the top, clear amber liquor leaving through an upper outlet and dark sludge
leaving through a lower outlet. Motion blur on the bowl to show it spinning fast. Centred.
```

### shot-06 · Concentration (paneo a lo largo)
```
Cutaway of a MULTI-EFFECT VACUUM EVAPORATOR: three tall vertical tube vessels in a row connected by
pipes, coffee liquor boiling gently with fine bubbles inside the tubes, vapour rising to a condenser on
the far right where clear water drips into a receiver, a vacuum gauge on the first vessel. The liquid
gets darker and thicker from left to right. The row spans the frame width.
```

### shot-06a · Spray drying (opcional, inclinación de arriba a abajo)
```
Cutaway of a very tall SPRAY-DRYING TOWER, several storeys high. At the TOP a rotating atomizer wheel
sprays coffee syrup into a fine mist inside a stream of hot air; the droplets dry as they fall and at the
BOTTOM dry brown coffee powder collects in a cone outlet and a cyclone beside the tower catches the fine
dust. Tall composition filling the height.
```

### shot-06b · Agglomeration (opcional, acercamiento)
```
Cutaway of an AGGLOMERATION TOWER: fine brown coffee powder falls from the top through a curtain of soft
steam mist and comes out at the bottom as larger porous clumps of granules on a belt. Macro feeling, the
change from dust to clumps clearly visible. Centred.
```

### shot-07 · Freezing (paneo siguiendo la banda)
```
Side view of a BELT FREEZER: on the LEFT thick dark coffee syrup pours from a nozzle onto a stainless-steel
belt as a continuous sheet; the belt runs through a frosty cold tunnel in the middle of the frame, with
cold mist at its mouth; on the RIGHT the sheet comes out as a solid, pale, frosted frozen slab. The belt
spans the whole width.
```

### shot-08 · Granulating (acercamiento al rotor)
```
Cutaway of a GRANULATOR: a toothed steel rotor breaking a frosted frozen coffee slab into small frosted
granules of 1 to 3 mm that fall onto a conveyor below, with a sieve screen under the rotor. The rotor is
the hero, centred, with cold mist around the granules.
```

### shot-09 · Freeze drying (alejamiento: de las bandejas a toda la cámara)
```
Cutaway of an industrial VACUUM FREEZE DRYER: a long horizontal sealed chamber with stacked metal trays of
frosted coffee granules on gently warmed shelves, faint vapour rising from the granules toward a large
duct on top that leads to a tall cold condenser covered in white ice, and a vacuum pump beside it. The
granules on the nearest trays are the detail; the whole chamber fits in the frame with margins.
```

### shot-10 · Packing (paneo siguiendo la línea)
```
Side view of an automated PACKING LINE: glass jars moving on a conveyor from LEFT to RIGHT; on the left a
filler nozzle pours dry brown coffee granules into a jar; in the middle a small nozzle blows a visible puff
of nitrogen gas into the next jar; on the right a capper presses the lid onto a filled jar. The line spans
the whole width.
```

### shot-11 · Cierre (acercamiento)
```
Top-down view of a white cup of hot water on a dark surface, a spoon dropping brown instant coffee
granules that dissolve instantly into dark swirls. Simple, calm, centred, with empty space around.
```

## Paso 3 · Me pasas las imágenes

Súbelas aquí con esos nombres (`shot-01.png`, `shot-02.png`, … y las verticales `shot-01-v.png`, …).
Con ellas genero `prototipo.mp4` (1920×1080) y `prototipo-vertical.mp4` (1080×1920), con la cámara,
los rótulos y los tiempos de la tabla. Luego ajustamos: duraciones, orden, textos, qué toma necesita otra
imagen.

## Locución (inglés, para grabar o para una voz sintética)

1. Instant coffee is real coffee, brewed in a factory, with the water taken back out. Here is how it is made.
2. Green beans tumble in a drum at over 200 degrees for about twelve minutes. They lose a fifth of their weight and turn brown.
3. Corrugated rollers crack the roasted beans into a coarse, even grind, so water can flow through it.
4. In tall steel columns, water at up to 180 degrees and high pressure dissolves about forty percent of the grounds. What comes out is a strong, dark liquor.
5. A centrifuge spins the liquor and throws out the fine sediment, leaving it clear.
6. Under vacuum, the liquor boils at only fifty degrees. More than half of the water leaves without cooking the flavour. Now it is a thick coffee syrup.
- 5A (opcional). The cheaper route: the syrup is sprayed into air at 250 degrees. Each droplet dries in a fraction of a second into a fine powder.
- 5B (opcional). A mist of steam sticks the powder into porous clumps that dissolve easily.
7. The syrup is poured on a belt and runs through a tunnel at minus forty-five degrees. It comes out as a solid frozen slab.
8. The slab is broken into small frozen granules, sized for how fast they should dissolve.
9. In a vacuum chamber the trays are gently warmed. At half a millibar the ice does not melt: it turns straight into vapour, which freezes again on a cold condenser. The granules dry without ever getting hot.
10. The dry granules go into jars. A puff of nitrogen pushes out the oxygen before the seal, so the coffee stays fresh for years.
11. Nothing added. Brewed coffee with the water taken out, frozen and dried. Back to coffee in a stir.
