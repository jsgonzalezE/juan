# ☕ Burman Inventario

Aplicación web para **Burman Coffee**: control de inventario y empaque de órdenes con
escáner QR usando la cámara del celular. No necesita servidor: todo corre en el teléfono
y los datos se guardan en el propio dispositivo.

## Qué hace

- **Escáner QR con la cámara** — usa el detector nativo del teléfono cuando existe
  (Android/Chrome, prácticamente instantáneo) y un decodificador de respaldo en los demás
  (iPhone/Safari). Bip + vibración + flash verde en cada bolsa contada.
- **Empaque de órdenes** — escribes el número de orden (o la tocas en la lista), y la app
  va marcando sola cada línea al escanear. Puedes **mezclar bolsas de 1, 2 y 5 lb en
  cualquier orden**: solo cuentan las libras (1+1 completa una línea de 2). Si escaneas un
  café que no va en la orden, flash rojo y sonido de error. Al completar la orden:
  pantalla verde con la **caja sugerida** y botón para saltar a la siguiente orden.
- **Dos líneas de inventario** — (1) todo lo escaneado queda registrado con fecha, orden,
  café y libras; (2) importas el CSV de pedidos de WooCommerce y al final del mes la app
  **compara escaneado vs. vendido** café por café, con la diferencia marcada en color.
- **Reportes** — libras y bolsas por café (hoy / mes / mes pasado / todo), con desglose por
  tamaño de bolsa (cuántas de 1, de 2 y de 5 lb), exportable a CSV.
- **Etiquetas QR nuevas** — genera e imprime etiquetas con el café **y las libras dentro
  del QR** (formato `BC|CAFE|LBS`, ej. `BC|COLOMBIA|2`). Con estas etiquetas el escáner ya
  no depende del numerito impreso al lado.
- **QRs viejos: la app aprende** — mientras renuevas etiquetas, al escanear un QR antiguo
  la app pregunta *una sola vez* qué café y cuántas libras es, lo recuerda para siempre y
  desde entonces cuenta automático. Si un mismo QR viejo se usa en varios tamaños, se marca
  "preguntar libras" y al escanear salen 3 botones gigantes (1 / 2 / 5) — un toque y listo.
- **Escaneo libre** — contar producción o inventario físico sin orden.
- **Funciona sin internet** (PWA): se instala en la pantalla de inicio y sigue funcionando
  aunque se caiga el wifi de la bodega. Mantiene la pantalla encendida mientras escaneas.

## Cómo publicarla (una sola vez)

La cámara requiere HTTPS, así que lo más fácil es GitHub Pages:

1. Haz merge de este PR a `main`.
2. El workflow **Publicar en GitHub Pages** corre solo (Actions → si es la primera vez y no
   arranca, entra a *Settings → Pages* y en **Source** elige **GitHub Actions**, luego
   relanza el workflow).
3. La app queda en: **https://jsgonzaleze.github.io/juan/**
4. En el celular: abre esa dirección en Chrome (Android) o Safari (iPhone) → menú →
   **Agregar a pantalla de inicio**. Acepta el permiso de cámara la primera vez.

Para probar en una computadora local: `python3 -m http.server` dentro de la carpeta y abre
`http://localhost:8000` (en localhost la cámara sí funciona sin HTTPS).

## Formato del archivo de órdenes del día

La pestaña **Órdenes** acepta texto pegado o archivo `.txt`/`.csv`. El parser es flexible;
todos estos formatos funcionan (ver `ejemplo-ordenes.txt`):

```
Orden 1001
2 lb Colombia
2 lb Brasil
2 lb Peru
Caja: Mediana

Pedido #1002
1 lb Etiopia
5 lb Colombia
Nota: cliente frecuente

1003
2x Guatemala 1lb
Costa Rica 2lb
```

También CSV con encabezados: `orden,cafe,lbs,cantidad,caja`. Antes de importar, la app
muestra una vista previa de lo que entendió para que confirmes. Los cafés que no existen
en el catálogo se agregan solos.

- `Caja: X` fija la caja de esa orden (si no, se sugiere por reglas de libras totales,
  configurables en Ajustes).
- `Nota: X` se muestra al terminar de empacar la orden.

## Comparación con WooCommerce

En **Reportes → WooCommerce** sube la exportación de pedidos (CSV). La app detecta las
columnas de producto/cantidad/fecha automáticamente, saca las libras del nombre del
producto (`2 lb`, `12 oz`, etc.) y empareja el café contra el catálogo. Lo que no pueda
identificar te lo pregunta una vez y lo recuerda. Luego muestra la tabla del mes:
**escaneado vs. tienda vs. diferencia**, exportable a CSV.

## Estructura

```
index.html          interfaz (5 pestañas: Escanear, Órdenes, Etiquetas, Reportes, Ajustes)
js/engine.js        lógica pura: parseo de QR/órdenes/CSV, empaque, resúmenes, comparación
js/scanner.js       cámara + decodificación (BarcodeDetector nativo o jsQR)
js/app.js           interfaz y almacenamiento (localStorage)
vendor/             jsQR (lector) y qrcode-generator (generador) — sin dependencias externas
tests/engine.test.js  79 pruebas del motor (node tests/engine.test.js)
sw.js               service worker: funciona sin internet
.github/workflows/pages.yml  pruebas + publicación automática a GitHub Pages
```

## Respaldo

Los datos viven en el teléfono (localStorage). En **Ajustes → Datos y respaldo** puedes
exportar/importar todo como JSON. Hazlo de vez en cuando y siempre antes de cambiar de
teléfono o borrar el navegador.
