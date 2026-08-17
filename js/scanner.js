/*
 * Escáner QR con la cámara — optimizado para velocidad.
 * - BarcodeDetector nativo cuando existe (Android/Chrome: decodifica por hardware).
 * - Respaldo jsQR: recorte central adaptativo (rápido) + barrido completo periódico
 *   para atrapar códigos fuera de centro. La resolución de análisis se ajusta sola
 *   según lo que tarda cada cuadro en este teléfono.
 * - Reporta la posición del QR en el cuadro (para el OCR del número impreso)
 *   y permite capturar el cuadro actual.
 */
(function (root) {
  'use strict';

  function QRScanner(video, opts) {
    this.video = video;
    this.opts = opts || {};
    this.onDecode = this.opts.onDecode || function () {};
    this.onStatus = this.opts.onStatus || function () {};
    this.running = false;
    this.stream = null;
    this.track = null;
    this.detector = null;
    this.canvas = null;
    this.ctx = null;
    this.torchOn = false;
    this.engineName = '';
    // adaptativo (solo jsQR)
    this._maxSide = 480;
    this._frameN = 0;
    this._grabCanvas = null;
  }

  QRScanner.prototype.start = async function () {
    if (this.running) return;
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      throw new Error('Este navegador no permite usar la cámara. Abre la app en Chrome o Safari con HTTPS.');
    }
    this.stream = await navigator.mediaDevices.getUserMedia({
      audio: false,
      video: {
        facingMode: { ideal: 'environment' },
        width: { ideal: 1280 },
        height: { ideal: 720 },
        frameRate: { ideal: 30 }
      }
    });
    this.video.srcObject = this.stream;
    this.video.setAttribute('playsinline', 'true');
    this.video.muted = true;
    await this.video.play();
    this.track = this.stream.getVideoTracks()[0];

    if ('BarcodeDetector' in root) {
      try {
        var formats = await root.BarcodeDetector.getSupportedFormats();
        if (formats && formats.indexOf('qr_code') !== -1) {
          this.detector = new root.BarcodeDetector({ formats: ['qr_code'] });
        }
      } catch (e) { this.detector = null; }
    }
    if (!this.detector) {
      this.canvas = document.createElement('canvas');
      this.ctx = this.canvas.getContext('2d', { willReadFrequently: true });
    }
    this.engineName = this.detector ? 'nativo' : 'jsQR';
    this.onStatus({ engine: this.engineName, caps: this.getCapabilities() });
    this.running = true;
    this._loop();
  };

  QRScanner.prototype._decodeNative = async function () {
    var codes = await this.detector.detect(this.video);
    if (codes && codes.length) {
      var c = codes[0];
      var loc = null;
      if (c.boundingBox) {
        loc = { x: c.boundingBox.x, y: c.boundingBox.y, w: c.boundingBox.width, h: c.boundingBox.height };
      }
      this.onDecode(c.rawValue, loc);
    }
  };

  QRScanner.prototype._decodeJsqr = function () {
    var vw = this.video.videoWidth, vh = this.video.videoHeight;
    if (!vw || !vh || !root.jsQR) return;
    this._frameN++;
    // 4 de cada 5 cuadros: recorte central (más rápido); el 5º: cuadro completo
    var fullSweep = (this._frameN % 5 === 0);
    var sx = 0, sy = 0, sw = vw, sh = vh;
    if (!fullSweep) {
      var side = Math.min(vw, vh) * 0.78;
      sx = (vw - side) / 2; sy = (vh - side) / 2; sw = side; sh = side;
    }
    var scale = Math.min(1, this._maxSide / Math.max(sw, sh));
    var w = Math.max(1, Math.round(sw * scale));
    var h = Math.max(1, Math.round(sh * scale));
    if (this.canvas.width !== w || this.canvas.height !== h) {
      this.canvas.width = w; this.canvas.height = h;
    }
    var t0 = performance.now();
    this.ctx.drawImage(this.video, sx, sy, sw, sh, 0, 0, w, h);
    var img = this.ctx.getImageData(0, 0, w, h);
    var code = root.jsQR(img.data, w, h, { inversionAttempts: 'dontInvert' });
    var dt = performance.now() - t0;
    // ajustar la resolución de análisis a la velocidad real del teléfono
    if (dt > 34 && this._maxSide > 340) this._maxSide -= 20;
    else if (dt < 14 && this._maxSide < 600) this._maxSide += 20;
    if (code && code.data) {
      var loc = null;
      if (code.location) {
        var L = code.location;
        var xs = [L.topLeftCorner.x, L.topRightCorner.x, L.bottomLeftCorner.x, L.bottomRightCorner.x];
        var ys = [L.topLeftCorner.y, L.topRightCorner.y, L.bottomLeftCorner.y, L.bottomRightCorner.y];
        var minX = Math.min.apply(null, xs), maxX = Math.max.apply(null, xs);
        var minY = Math.min.apply(null, ys), maxY = Math.max.apply(null, ys);
        // volver a coordenadas del video completo
        loc = {
          x: sx + minX / scale, y: sy + minY / scale,
          w: (maxX - minX) / scale, h: (maxY - minY) / scale
        };
      }
      this.onDecode(code.data, loc);
    }
    return dt;
  };

  QRScanner.prototype._loop = async function () {
    while (this.running) {
      var dt = 0;
      try {
        if (this.video.readyState >= 2) {
          if (this.detector) await this._decodeNative();
          else dt = this._decodeJsqr() || 0;
        }
      } catch (e) { /* un cuadro fallido no detiene el escáner */ }
      await new Promise(function (res) {
        if (root.requestAnimationFrame) root.requestAnimationFrame(function () { res(); });
        else setTimeout(res, 40);
      });
      // respiro solo si el análisis fue lento (deja respirar a la interfaz)
      if (!this.detector && dt > 28) {
        await new Promise(function (res) { setTimeout(res, 25); });
      }
    }
  };

  /** Captura el cuadro actual a un canvas en resolución nativa (para OCR). */
  QRScanner.prototype.grabFrame = function () {
    var vw = this.video.videoWidth, vh = this.video.videoHeight;
    if (!vw || !vh) return null;
    if (!this._grabCanvas) this._grabCanvas = document.createElement('canvas');
    var c = this._grabCanvas;
    if (c.width !== vw || c.height !== vh) { c.width = vw; c.height = vh; }
    c.getContext('2d', { willReadFrequently: true }).drawImage(this.video, 0, 0, vw, vh);
    return c;
  };

  QRScanner.prototype.getCapabilities = function () {
    try {
      return this.track && this.track.getCapabilities ? (this.track.getCapabilities() || {}) : {};
    } catch (e) { return {}; }
  };

  QRScanner.prototype.setTorch = async function (on) {
    var caps = this.getCapabilities();
    if (!caps.torch || !this.track) return false;
    try {
      await this.track.applyConstraints({ advanced: [{ torch: !!on }] });
      this.torchOn = !!on;
      return true;
    } catch (e) { return false; }
  };

  QRScanner.prototype.setZoom = async function (value) {
    var caps = this.getCapabilities();
    if (!caps.zoom || !this.track) return false;
    try {
      await this.track.applyConstraints({ advanced: [{ zoom: value }] });
      return true;
    } catch (e) { return false; }
  };

  QRScanner.prototype.stop = function () {
    this.running = false;
    if (this.stream) {
      this.stream.getTracks().forEach(function (t) { t.stop(); });
      this.stream = null;
    }
    this.track = null;
    if (this.video) this.video.srcObject = null;
  };

  root.QRScanner = QRScanner;
})(typeof window !== 'undefined' ? window : this);
