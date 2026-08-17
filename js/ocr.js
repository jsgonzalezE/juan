/*
 * OCR asistido: lee el número de libras impreso junto al QR en etiquetas antiguas.
 * - Se carga solo cuando hace falta (no toca la velocidad del escáner de QR).
 * - Todo local (vendor/tesseract), funciona sin internet una vez cacheado.
 * - Es una ayuda con respaldo: si no logra leer, la app pregunta con botones.
 */
(function (root) {
  'use strict';

  var worker = null;
  var initPromise = null;
  var unavailable = false;

  // detección de SIMD en WebAssembly (módulo mínimo con v128)
  function hasSimd() {
    try {
      return WebAssembly.validate(new Uint8Array([
        0, 97, 115, 109, 1, 0, 0, 0, 1, 5, 1, 96, 0, 1, 123, 3,
        2, 1, 0, 10, 10, 1, 8, 0, 65, 0, 253, 15, 253, 98, 11
      ]));
    } catch (e) { return false; }
  }

  function base() {
    // ruta relativa a la página (funciona en subdirectorios como GitHub Pages)
    return new URL('vendor/tesseract/', root.location.href).href;
  }

  function ensure() {
    if (unavailable) return Promise.reject(new Error('OCR no disponible'));
    if (initPromise) return initPromise;
    if (!root.Tesseract) { unavailable = true; return Promise.reject(new Error('Tesseract no cargado')); }
    var b = base();
    var core = b + (hasSimd() ? 'tesseract-core-simd-lstm.wasm.js' : 'tesseract-core-lstm.wasm.js');
    initPromise = root.Tesseract.createWorker('eng', 1, {
      workerPath: b + 'worker.min.js',
      corePath: core,
      langPath: b.replace(/\/$/, ''),
      gzip: true
    }).then(function (w) {
      worker = w;
      return w.setParameters({
        tessedit_char_whitelist: '0123456789./LBSOZlbsoz ',
        user_defined_dpi: '300'
      }).then(function () { return w; });
    }).catch(function (err) {
      unavailable = true;
      initPromise = null;
      throw err;
    });
    return initPromise;
  }

  /** Precalienta el worker en segundo plano (llamar al iniciar una sesión de escaneo). */
  function warmup() { ensure().catch(function () {}); }

  /**
   * Prepara el recorte alrededor del QR: zona ampliada (el número está al lado),
   * escalada y en escala de grises con contraste estirado.
   */
  function buildCrop(source, loc) {
    var sw = source.videoWidth || source.width;
    var sh = source.videoHeight || source.height;
    if (!sw || !sh || !loc || !loc.w) return null;
    // expandir la caja del QR 1.7x hacia los lados y 1.4x vertical
    var cx = loc.x + loc.w / 2, cy = loc.y + loc.h / 2;
    var w = loc.w * 3.4, h = loc.h * 2.8;
    var x = Math.max(0, cx - w / 2), y = Math.max(0, cy - h / 2);
    w = Math.min(sw - x, w); h = Math.min(sh - y, h);
    if (w < 20 || h < 20) return null;
    var scale = Math.max(1, Math.min(3, 520 / w));
    var canvas = document.createElement('canvas');
    canvas.width = Math.round(w * scale);
    canvas.height = Math.round(h * scale);
    var ctx = canvas.getContext('2d', { willReadFrequently: true });
    ctx.imageSmoothingEnabled = true;
    ctx.drawImage(source, x, y, w, h, 0, 0, canvas.width, canvas.height);
    // tapar el QR en blanco: sus módulos generan "dígitos fantasma" en el OCR
    var mx = (loc.x - x) * scale, my = (loc.y - y) * scale;
    var mw = loc.w * scale, mh = loc.h * scale;
    var pad = Math.max(mw, mh) * 0.08;
    ctx.fillStyle = '#fff';
    ctx.fillRect(mx - pad, my - pad, mw + pad * 2, mh + pad * 2);
    // gris + estiramiento de contraste
    var img = ctx.getImageData(0, 0, canvas.width, canvas.height);
    var d = img.data, min = 255, max = 0, i, g;
    for (i = 0; i < d.length; i += 4) {
      g = (d[i] * 0.299 + d[i + 1] * 0.587 + d[i + 2] * 0.114) | 0;
      d[i] = d[i + 1] = d[i + 2] = g;
      if (g < min) min = g;
      if (g > max) max = g;
    }
    var range = Math.max(1, max - min);
    for (i = 0; i < d.length; i += 4) {
      g = ((d[i] - min) * 255 / range) | 0;
      d[i] = d[i + 1] = d[i + 2] = g;
    }
    ctx.putImageData(img, 0, 0);
    return canvas;
  }

  /*
   * Busca un número de libras plausible en el texto reconocido.
   * Conservador a propósito: un número suelto que no sea un tamaño real de bolsa
   * (código de lote, fecha) NO debe contarse — mejor preguntar con botones.
   */
  var SAFE_SIZES = [1, 2, 5, 0.5];
  function pickLbs(text) {
    if (!text) return null;
    var s = String(text);
    // 1) número con "LB" explícito al lado (el OCR puede meter espacios)
    var m = /(\d+(?:[.,]\d+)?)\s*l\s?b/i.exec(s);
    if (m) {
      var v = parseFloat(m[1].replace(',', '.'));
      return (v > 0 && v <= 20) ? v : null;
    }
    // 2) onzas explícitas → convertir a libras (16 OZ = 1 lb, 12 OZ = 0.75 lb)
    m = /(\d+(?:[.,]\d+)?)\s*oz/i.exec(s);
    if (m) {
      var oz = parseFloat(m[1].replace(',', '.'));
      var lbs = Math.round((oz / 16) * 100) / 100;
      return (lbs > 0 && lbs <= 20) ? lbs : null;
    }
    // 3) número suelto: solo si es un tamaño real de bolsa
    var tokens = s.match(/\d+(?:\.\d+)?/g) || [];
    for (var p = 0; p < SAFE_SIZES.length; p++) {
      for (var i = 0; i < tokens.length; i++) {
        if (parseFloat(tokens[i]) === SAFE_SIZES[p]) return SAFE_SIZES[p];
      }
    }
    return null;
  }

  /**
   * Lee las libras impresas cerca del QR.
   * source: video o canvas con el cuadro; loc: {x,y,w,h} del QR en coords del source.
   * Devuelve Promise<{lbs, text} | null>. Nunca rechaza: en error devuelve null.
   */
  function readLbsNear(source, loc, timeoutMs) {
    var crop;
    try { crop = buildCrop(source, loc); } catch (e) { crop = null; }
    if (!crop) return Promise.resolve(null);
    var work = ensure().then(function (w) {
      return w.recognize(crop);
    }).then(function (res) {
      var text = res && res.data ? res.data.text : '';
      var lbs = pickLbs(text);
      return lbs ? { lbs: lbs, text: text.trim() } : null;
    }).catch(function () { return null; });
    var timeout = new Promise(function (resolve) {
      setTimeout(function () { resolve(null); }, timeoutMs || 4000);
    });
    return Promise.race([work, timeout]);
  }

  function isAvailable() { return !unavailable && !!root.Tesseract; }

  root.BCOcr = { warmup: warmup, readLbsNear: readLbsNear, isAvailable: isAvailable, _pickLbs: pickLbs };
})(typeof window !== 'undefined' ? window : this);
