/*
 * Escáner QR con la cámara.
 * - Usa BarcodeDetector nativo cuando está disponible (Android/Chrome: muy rápido).
 * - Respaldo con jsQR sobre un canvas reducido (iPhone/Safari y otros).
 * - Linterna y zoom cuando la cámara los soporta.
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
  }

  QRScanner.prototype.start = async function () {
    if (this.running) return;
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      throw new Error('Este navegador no permite usar la cámara. Abre la app en Chrome o Safari con HTTPS.');
    }
    var constraints = {
      audio: false,
      video: {
        facingMode: { ideal: 'environment' },
        width: { ideal: 1280 },
        height: { ideal: 720 }
      }
    };
    this.stream = await navigator.mediaDevices.getUserMedia(constraints);
    this.video.srcObject = this.stream;
    this.video.setAttribute('playsinline', 'true');
    this.video.muted = true;
    await this.video.play();
    this.track = this.stream.getVideoTracks()[0];

    // detector nativo si soporta QR
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

  QRScanner.prototype._loop = async function () {
    var self = this;
    while (this.running) {
      try {
        if (this.video.readyState >= 2) {
          if (this.detector) {
            var codes = await this.detector.detect(this.video);
            if (codes && codes.length) this.onDecode(codes[0].rawValue);
          } else if (root.jsQR) {
            var vw = this.video.videoWidth, vh = this.video.videoHeight;
            if (vw && vh) {
              // reducir a máx. 480px por lado: jsQR corre mucho más rápido
              var scale = Math.min(1, 480 / Math.max(vw, vh));
              var w = Math.max(1, Math.round(vw * scale));
              var h = Math.max(1, Math.round(vh * scale));
              if (this.canvas.width !== w) { this.canvas.width = w; this.canvas.height = h; }
              this.ctx.drawImage(this.video, 0, 0, w, h);
              var img = this.ctx.getImageData(0, 0, w, h);
              var code = root.jsQR(img.data, w, h, { inversionAttempts: 'dontInvert' });
              if (code && code.data) this.onDecode(code.data);
            }
          }
        }
      } catch (e) { /* un frame fallido no detiene el escáner */ }
      await new Promise(function (res) {
        if (root.requestAnimationFrame) root.requestAnimationFrame(function () { res(); });
        else setTimeout(res, 50);
      });
      // pequeño respiro extra para el modo jsQR en teléfonos lentos
      if (!this.detector) await new Promise(function (res) { setTimeout(res, 30); });
    }
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
