# Prompts de imagen para el vídeo "How instant coffee is made"

Pega primero el **bloque de estilo** y después el prompt de la escena. Pide siempre dos versiones:
`16:9` (YouTube) y `9:16` (Reels / TikTok / Shorts). Los prompts están en inglés porque el vídeo es en inglés
y los modelos de imagen responden mejor así.

Hay dos estilos. Elige uno y úsalo en todas las escenas para que el vídeo sea coherente:

- **Estilo A, "blueprint"**: igual que la figura animada que ya tienes (fondo oscuro, línea monocroma, isométrico).
  Las imágenes encajan con el MP4 sin corte visual.
- **Estilo B, "fábrica real"**: fotografía industrial limpia. Sirve como B-roll entre las tomas animadas.

---

## Bloque de estilo A (blueprint, igual que la animación)

```
Technical illustration, isometric view, clean monochrome line art in light grey and white ink on a near-black
background (#0e0e0e), subtle flat shading, no colour except a single warm amber accent for the coffee itself.
Engineering-drawing feel, crisp 1px outlines, no text, no labels, no logos, no people, no watermarks,
plenty of empty background around the subject for captions.
```

## Bloque de estilo B (fábrica real)

```
Clean industrial photography, modern food-processing plant, stainless steel equipment, soft diffused daylight,
shallow depth of field, muted cool palette with warm brown coffee tones, documentary style, realistic,
no text, no logos, no visible faces, no watermarks, leave empty space on the lower third for captions.
```

---

## Escenas (un prompt por paso del proceso)

### 0 · Portada
```
A single glass jar of instant coffee granules next to a steaming cup of coffee on a plain surface,
centred, generous negative space above for a title. Mood: simple, calm, premium.
```

### 1 · Roasting (tostado)
```
Green unroasted coffee beans pouring from a hopper into a rotating drum roaster; a second view shows the same
beans turning deep brown inside the drum with heat shimmer and a thin wisp of smoke from a chimney.
Show the colour change from pale green to brown clearly.
```

### 2 · Grinding (molienda)
```
Roasted coffee beans dropping between two steel rollers of an industrial mill and leaving below as a coarse
1 mm grind, a conveyor carrying the grounds upward to the next machine. Focus on the bean-to-grounds change.
```

### 3 · Extraction (extracción)
```
A tall vertical extraction column, glass-walled, packed with a dark bed of ground coffee; hot water enters at
the top and dark brown liquid extract collects at the bottom and leaves through a pipe. A boiler stands behind
it. Emphasise the water going in clear and coming out as dark coffee.
```

### 4 · Concentration (concentración al vacío)
```
A sealed vacuum evaporator kettle with a glass dome; the coffee extract inside boils gently at low temperature
with fine bubbles, water vapour rises through a pipe into a condenser where it drips back as clear water into
a glass receiver. A pressure gauge reads near full vacuum. The coffee in the kettle looks thicker and darker.
```

### 5 · Freezing (congelación en banda)
```
Thick dark coffee concentrate being poured in a continuous sheet onto a slow stainless-steel belt that runs
through a frosty cold tunnel at minus 45 degrees Celsius; on the far side the sheet comes out as a solid,
frosted, dark-brown frozen slab. Visible frost and cold mist at the tunnel exit.
```

### 6 · Granulating (granulado)
```
The frozen coffee slab breaking into small 1 to 3 mm frozen granules inside a granulator with a toothed rotor;
the granules fall onto a climbing conveyor and are spread in an even layer on flat metal trays.
Macro detail of the frosted granules.
```

### 7 · Freeze drying (liofilización)
```
Inside a vacuum freeze-drying chamber: stacked metal trays of frozen coffee granules on gently warmed shelves,
a faint vapour rising from the granules toward a large duct, and a tall cold condenser where the vapour
freezes back as white ice. No melting, no liquid: the granules stay solid and turn from frosted to dry and
porous. Gauge reading 0.5 millibar.
```

### 8 · Packing (envasado)
```
Dry porous coffee granules flowing from a filler nozzle into glass jars on a conveyor; one jar waits empty,
one is filling, one is already capped. Clean packaging line, close view of the granules landing in the jar.
```

### 9 · Cierre
```
A spoon of instant coffee granules dissolving instantly in a cup of hot water, swirl of dark coffee spreading,
top-down view, soft light. Space on one side for the closing caption.
```

---

## Extras útiles

- **Comparativa de pesos** (para el dato de 120 g → 41 g):
  ```
  Two small piles side by side on a plain surface: 120 g of green coffee beans on the left and 41 g of dry
  instant coffee granules on the right, same scale, same lighting, seen from a low angle. No text.
  ```
- **Mapa del proceso** (una sola imagen con los ocho pasos):
  ```
  One wide isometric illustration of a small instant coffee plant in a continuous line, left to right:
  bean silo, drum roaster, roller mill, glass extraction column, vacuum kettle with condenser, belt freezer
  tunnel, granulator, freeze-drying chamber with trays and ice condenser, filler with jars. Material flows
  along conveyors between machines. No text.
  ```

## Consejos al pedir en ChatGPT

- Pide **"same style and lighting as the previous image"** a partir de la segunda escena, o genera todas en
  el mismo chat.
- Si sale texto o logotipos, añade `absolutely no text or letters anywhere in the image`.
- Si hace falta que coincida con la animación, adjunta una captura del MP4 (carpeta `shots/`) y escribe
  `match this illustration style exactly`.
- Para la versión vertical pide la escena **recompuesta** (no recortada): `recompose for 9:16, subject
  centred, keep the lower third empty`.
