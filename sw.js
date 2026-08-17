/* Service worker: la app funciona sin internet una vez cargada. */
var VERSION = 'burman-v2';
var ASSETS = [
  './',
  './index.html',
  './css/app.css',
  './js/engine.js',
  './js/scanner.js',
  './js/ocr.js',
  './js/sync.js',
  './js/app.js',
  './vendor/jsQR.js',
  './vendor/qrcode.js',
  './vendor/tesseract/tesseract.min.js',
  './manifest.webmanifest',
  './assets/icon.svg',
  './assets/icon-192.png',
  './assets/icon-512.png',
  './assets/apple-touch-icon.png'
];
/* Los archivos grandes del OCR (worker, wasm, idioma) se cachean al primer uso. */

self.addEventListener('install', function (e) {
  e.waitUntil(
    caches.open(VERSION).then(function (c) { return c.addAll(ASSETS); }).then(function () {
      return self.skipWaiting();
    })
  );
});

self.addEventListener('activate', function (e) {
  e.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.filter(function (k) { return k !== VERSION; }).map(function (k) {
        return caches.delete(k);
      }));
    }).then(function () { return self.clients.claim(); })
  );
});

/* mismo origen: red primero (para recibir actualizaciones), caché como respaldo */
self.addEventListener('fetch', function (e) {
  var url = new URL(e.request.url);
  if (e.request.method !== 'GET' || url.origin !== location.origin) return;
  e.respondWith(
    fetch(e.request).then(function (res) {
      var copy = res.clone();
      caches.open(VERSION).then(function (c) { c.put(e.request, copy); });
      return res;
    }).catch(function () {
      return caches.match(e.request, { ignoreSearch: true }).then(function (hit) {
        return hit || caches.match('./index.html');
      });
    })
  );
});
