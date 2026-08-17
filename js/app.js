/*
 * Burman Inventario — aplicación (v2).
 * Todo corre en el teléfono; los datos se guardan en localStorage.
 * La cámara vive fija abajo: en reposo identifica bolsas (sin contar),
 * con una orden activa cuenta y verifica cada escaneo.
 */
(function () {
  'use strict';
  var E = window.BCEngine;

  // ================= almacenamiento =================

  var DB = {
    get: function (key, fallback) {
      try {
        var raw = localStorage.getItem('bc.' + key);
        return raw == null ? fallback : JSON.parse(raw);
      } catch (e) { return fallback; }
    },
    set: function (key, value) {
      localStorage.setItem('bc.' + key, JSON.stringify(value));
    },
    KEYS: ['catalog', 'orders', 'scans', 'legacyMap', 'wooMap', 'wooData', 'wooImages', 'settings']
  };

  var DEFAULT_CATALOG = [
    { sku: 'COLOMBIA', name: 'Colombia', aliases: ['colombian'] },
    { sku: 'BRASIL', name: 'Brasil', aliases: ['brazil'] },
    { sku: 'PERU', name: 'Perú', aliases: [] },
    { sku: 'GUATEMALA', name: 'Guatemala', aliases: [] },
    { sku: 'ETIOPIA', name: 'Etiopía', aliases: ['ethiopia'] },
    { sku: 'COSTA-RICA', name: 'Costa Rica', aliases: [] },
    { sku: 'MEXICO', name: 'México', aliases: [] },
    { sku: 'HONDURAS', name: 'Honduras', aliases: [] },
    { sku: 'SUMATRA', name: 'Sumatra', aliases: [] },
    { sku: 'KENIA', name: 'Kenia', aliases: ['kenya'] },
    { sku: 'DESCAF', name: 'Descafeinado', aliases: ['decaf'] }
  ];

  var DEFAULT_SETTINGS = {
    sound: true,
    vibrate: true,
    ocr: true,
    cooldownMs: 1100,
    storeUrl: 'https://www.burmancoffee.com',
    boxRules: [
      { maxLbs: 2, box: 'Caja chica' },
      { maxLbs: 6, box: 'Caja mediana' },
      { maxLbs: 14, box: 'Caja grande' },
      { maxLbs: 999, box: 'Caja XL / dividir en 2' }
    ],
    sync: { enabled: false, url: '', secret: '' }
  };

  var catalog = DB.get('catalog', null) || DEFAULT_CATALOG.slice();
  var orders = DB.get('orders', []);
  var scans = DB.get('scans', []);
  var legacyMap = DB.get('legacyMap', {});
  var wooMap = DB.get('wooMap', {});
  var wooData = DB.get('wooData', {});
  var wooImages = DB.get('wooImages', {});
  var settings = Object.assign({}, DEFAULT_SETTINGS, DB.get('settings', {}));
  if (!settings.boxRules || !settings.boxRules.length) settings.boxRules = DEFAULT_SETTINGS.boxRules.slice();
  if (!settings.sync) settings.sync = { enabled: false, url: '', secret: '' };

  function saveCatalog() { DB.set('catalog', catalog); }
  function saveOrders() { DB.set('orders', orders); }
  function saveScans() { DB.set('scans', scans); }
  function saveLegacy() { DB.set('legacyMap', legacyMap); }
  function saveWooMap() { DB.set('wooMap', wooMap); }
  function saveWooData() { DB.set('wooData', wooData); }
  function saveWooImages() { DB.set('wooImages', wooImages); }
  function saveSettings() { DB.set('settings', settings); }

  // ================= utilidades DOM =================

  function $(id) { return document.getElementById(id); }
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function getCoffee(sku) {
    for (var i = 0; i < catalog.length; i++) if (catalog[i].sku === sku) return catalog[i];
    return null;
  }
  function coffeeName(sku) {
    var c = getCoffee(sku);
    return c ? c.name : sku;
  }

  var AVATAR_TONES = ['#9a8478', '#7d8a74', '#867f96', '#768a96', '#96857d', '#7f8c72', '#8a7d90', '#94766d'];
  function avatarHtml(sku, cls) {
    var c = getCoffee(sku);
    var name = c ? c.name : sku;
    var initials = name.split(/\s+/).map(function (w) { return w.charAt(0); }).join('').slice(0, 2).toUpperCase();
    var hash = 0;
    for (var i = 0; i < sku.length; i++) hash = (hash * 31 + sku.charCodeAt(i)) | 0;
    var tone = AVATAR_TONES[Math.abs(hash) % AVATAR_TONES.length];
    var img = c && c.image
      ? '<img src="' + esc(c.image) + '" alt="" loading="lazy" onerror="this.remove()">'
      : '';
    return '<span class="avatar ' + (cls || '') + '" style="background:' + tone + '">' +
      esc(initials) + img + '</span>';
  }

  function toast(msg, ms) {
    var t = $('toast');
    t.textContent = msg;
    t.classList.add('show');
    clearTimeout(toast._t);
    toast._t = setTimeout(function () { t.classList.remove('show'); }, ms || 2200);
  }
  function download(filename, text, mime) {
    var blob = new Blob([text], { type: mime || 'text/csv;charset=utf-8' });
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 500);
  }

  // ================= sonido y vibración =================

  var audioCtx = null;
  function ensureAudio() {
    if (!audioCtx) {
      try { audioCtx = new (window.AudioContext || window.webkitAudioContext)(); } catch (e) {}
    }
    if (audioCtx && audioCtx.state === 'suspended') audioCtx.resume();
  }
  function tone(freq, start, dur, type, gain) {
    if (!audioCtx) return;
    var o = audioCtx.createOscillator();
    var g = audioCtx.createGain();
    o.type = type || 'sine';
    o.frequency.value = freq;
    g.gain.setValueAtTime(gain || 0.18, audioCtx.currentTime + start);
    g.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + start + dur);
    o.connect(g); g.connect(audioCtx.destination);
    o.start(audioCtx.currentTime + start);
    o.stop(audioCtx.currentTime + start + dur + 0.02);
  }
  function soundOk() { if (settings.sound) { ensureAudio(); tone(1250, 0, 0.09); } }
  function soundErr() { if (settings.sound) { ensureAudio(); tone(220, 0, 0.16, 'square', 0.12); tone(180, 0.17, 0.2, 'square', 0.12); } }
  function soundWarn() { if (settings.sound) { ensureAudio(); tone(520, 0, 0.12, 'triangle'); tone(430, 0.13, 0.14, 'triangle'); } }
  function soundComplete() { if (settings.sound) { ensureAudio(); tone(880, 0, 0.11); tone(1108, 0.11, 0.11); tone(1318, 0.22, 0.22); } }
  function vibrate(pattern) {
    if (settings.vibrate && navigator.vibrate) { try { navigator.vibrate(pattern); } catch (e) {} }
  }
  function flash(kind) {
    var f = $('flash');
    f.className = '';
    void f.offsetWidth; // reiniciar animación
    f.className = kind;
  }

  // ================= navegación =================

  var currentView = 'scan';
  function showView(name) {
    currentView = name;
    document.querySelectorAll('.view').forEach(function (v) { v.classList.remove('active'); });
    $('view-' + name).classList.add('active');
    document.querySelectorAll('#tabbar button').forEach(function (b) {
      b.classList.toggle('active', b.dataset.view === name);
    });
    if (name === 'orders') renderOrders();
    if (name === 'reports') renderReports();
    if (name === 'settings') renderSettings();
    if (name === 'labels') renderLabelCoffees();
    if (name === 'scan') renderScanView();
    updateCamera();
  }
  document.querySelectorAll('#tabbar button').forEach(function (b) {
    b.addEventListener('click', function () { showView(b.dataset.view); });
  });

  // ================= sesión de escaneo =================

  var scanSession = {
    mode: null,          // null (consulta) | 'order' | 'free'
    orderId: null,
    freeTally: {},       // sku -> {lbs, bags}
    undoStack: [],
    paused: false,
    lastSeen: {},        // payload -> ts del último cuadro en que se vio
    lastAccept: {},      // payload -> ts de la última vez que se contó
    pendingGap: {}       // payload -> true si salió de cámara desde el último conteo
  };
  var scanner = null;
  var wakeLock = null;

  function getOrder(id) {
    for (var i = 0; i < orders.length; i++) if (orders[i].id === id) return orders[i];
    return null;
  }

  function orderSummaryText(o) {
    return o.items.map(function (it) {
      return it.name + ' ' + E.fmtLbs(it.lbsEach) + 'lb' + (it.qty > 1 ? '×' + it.qty : '');
    }).join(' · ');
  }

  function resetDedupe() {
    scanSession.lastSeen = {};
    scanSession.lastAccept = {};
    scanSession.pendingGap = {};
  }

  function findOrderLoose(id) {
    var o = getOrder(id);
    if (o) return o;
    var normId = String(id).trim().toUpperCase().replace(/^0+(?=.)/, '');
    for (var i = 0; i < orders.length; i++) {
      var cand = String(orders[i].id).trim().toUpperCase().replace(/^0+(?=.)/, '');
      if (cand === normId) return orders[i];
    }
    return null;
  }

  function startOrder(id) {
    var o = findOrderLoose(id);
    if (!o) { toast('No encontré la orden "' + id + '". Impórtala primero en Órdenes.'); return; }
    id = o.id;
    if (o.status === 'lista') {
      if (!confirm('La orden ' + id + ' ya está marcada como lista. ¿Abrirla de nuevo?')) return;
      o.status = 'en-proceso';
      if (o.job) o.job.completedAt = null;
    }
    if (!o.job) o.job = E.buildJob(o);
    if (o.status === 'pendiente') o.status = 'en-proceso';
    if (!o.job.startedAt) o.job.startedAt = Date.now();
    saveOrders();
    scanSession.mode = 'order';
    scanSession.orderId = id;
    scanSession.undoStack = [];
    resetDedupe();
    ensureAudio();
    if (settings.ocr && window.BCOcr) BCOcr.warmup();
    renderScanView();
    updateCamera();
  }

  function startFree() {
    scanSession.mode = 'free';
    scanSession.orderId = null;
    scanSession.freeTally = {};
    scanSession.undoStack = [];
    resetDedupe();
    ensureAudio();
    if (settings.ocr && window.BCOcr) BCOcr.warmup();
    renderScanView();
    updateCamera();
  }

  function exitScan() {
    scanSession.mode = null;
    scanSession.orderId = null;
    renderScanView();
    updateCamera();
  }

  // ---------- cámara ----------

  function updateCamera() {
    var wantCam = currentView === 'scan' && document.visibilityState === 'visible';
    document.body.classList.toggle('cam-on', wantCam);
    document.body.classList.toggle('scanning', !!scanSession.mode && currentView === 'scan');
    $('dock-actions').hidden = !scanSession.mode;
    if (wantCam) startCamera();
    else stopCamera();
  }

  var cameraStarting = false;

  async function startCamera() {
    if (cameraStarting || (scanner && scanner.running)) return;
    cameraStarting = true;
    var video = $('cam');
    $('cam-msg').textContent = 'Iniciando cámara…';
    scanner = new QRScanner(video, {
      onDecode: onDecode,
      onStatus: function (st) {
        $('cam-msg').textContent = '';
        var caps = st.caps || {};
        $('btn-torch').hidden = !caps.torch;
        var zoom = $('zoom');
        if (caps.zoom && caps.zoom.max > caps.zoom.min) {
          zoom.hidden = false;
          zoom.min = caps.zoom.min; zoom.max = Math.min(caps.zoom.max, 5);
          zoom.step = caps.zoom.step || 0.1;
          zoom.value = caps.zoom.min;
        } else zoom.hidden = true;
        $('cam-status').textContent = st.engine === 'nativo' ? 'ESCÁNER NATIVO' : 'ESCÁNER LISTO';
      }
    });
    try {
      await scanner.start();
      if (scanner.running) acquireWakeLock();
      if (!scanSession.mode) {
        $('cam-msg').textContent = 'Modo consulta · acerca una bolsa para identificarla';
        setTimeout(function () {
          if (!scanSession.mode && $('cam-msg').textContent.indexOf('consulta') !== -1) $('cam-msg').textContent = '';
        }, 3500);
      }
    } catch (err) {
      $('cam-msg').textContent = (err && err.name === 'NotAllowedError')
        ? 'Permiso de cámara denegado. Actívalo en los ajustes del navegador.'
        : 'No pude abrir la cámara: ' + (err && err.message ? err.message : err);
    }
    cameraStarting = false;
  }

  function stopCamera() {
    if (scanner) scanner.stop();
    releaseWakeLock();
    $('cam-status').textContent = '';
  }

  async function acquireWakeLock() {
    try {
      if ('wakeLock' in navigator) wakeLock = await navigator.wakeLock.request('screen');
    } catch (e) { wakeLock = null; }
  }
  function releaseWakeLock() {
    if (wakeLock) { try { wakeLock.release(); } catch (e) {} wakeLock = null; }
  }
  document.addEventListener('visibilitychange', updateCamera);

  $('btn-torch').addEventListener('click', function () {
    if (scanner) scanner.setTorch(!scanner.torchOn);
  });
  $('zoom').addEventListener('input', function () {
    if (scanner) scanner.setZoom(parseFloat(this.value));
  });

  // ---------- lógica de decodificación ----------

  var GAP_MS = 450; // el QR debe salir de cámara este tiempo para contar otra bolsa igual

  function onDecode(raw, loc) {
    if (scanSession.paused) return;
    if (!scanSession.mode) { lookupDecode(raw); return; }
    var now = performance.now();
    var seen = scanSession.lastSeen[raw];
    var accepted = scanSession.lastAccept[raw];
    // ¿hubo un hueco sin ver este QR? → es (o puede ser) otra bolsa igual
    if (seen == null || (now - seen) > GAP_MS) scanSession.pendingGap[raw] = true;
    scanSession.lastSeen[raw] = now;
    // sigue frente a la cámara desde el último conteo → no volver a contar
    if (accepted != null && !scanSession.pendingGap[raw]) return;
    // anti rebote general (protege contra parpadeos del decodificador)
    if (accepted != null && (now - accepted) < settings.cooldownMs) return;
    scanSession.lastAccept[raw] = now;
    scanSession.pendingGap[raw] = false;
    handlePayload(raw, loc);
  }

  // modo consulta: identifica la bolsa sin contar
  var lookupLast = { raw: null, ts: 0 };
  function lookupDecode(raw) {
    var now = performance.now();
    if (raw === lookupLast.raw && now - lookupLast.ts < 2200) { lookupLast.ts = now; return; }
    lookupLast.raw = raw; lookupLast.ts = now;
    var parsed = E.parseQR(raw);
    var card = $('lookup-card');
    var html = '';
    if (parsed.type === 'bc') {
      html = avatarHtml(parsed.sku) +
        '<span><span class="lk-name">' + esc(coffeeName(parsed.sku)) + '</span>' +
        '<span class="lk-sub">Etiqueta nueva · lista para contar</span></span>' +
        '<span class="lk-lbs">' + E.fmtLbs(parsed.lbs) + ' lb</span>';
    } else if (legacyMap[raw] && legacyMap[raw].sku) {
      var m = legacyMap[raw];
      html = avatarHtml(m.sku) +
        '<span><span class="lk-name">' + esc(coffeeName(m.sku)) + '</span>' +
        '<span class="lk-sub">QR antiguo aprendido</span></span>' +
        '<span class="lk-lbs">' + (m.lbs ? E.fmtLbs(m.lbs) + ' lb' : '¿lb?') + '</span>';
    } else {
      html = '<span class="avatar" style="background:var(--surface2);color:var(--muted)">?</span>' +
        '<span><span class="lk-name">Etiqueta desconocida</span>' +
        '<span class="lk-sub">Se aprende al escanearla dentro de una orden o escaneo libre</span></span>';
    }
    card.innerHTML = html;
    card.hidden = false;
    soundOk(); vibrate(15);
    clearTimeout(lookupDecode._t);
    lookupDecode._t = setTimeout(function () { card.hidden = true; }, 2600);
  }

  function handlePayload(raw, loc) {
    var parsed = E.parseQR(raw);
    if (parsed.type === 'bc') {
      ensureCoffee(parsed.sku);
      applyBag(parsed.sku, parsed.lbs, 'scan');
      return;
    }
    // QR antiguo: buscar en el mapa aprendido
    var mapping = legacyMap[raw];
    if (mapping && mapping.sku) {
      if (mapping.lbs) { applyBag(mapping.sku, mapping.lbs, 'scan'); return; }
      resolveLbsViaOcr(mapping.sku, raw, loc);
      return;
    }
    openLegacySheet(raw, loc);
  }

  /*
   * Modo transición: la cámara lee el QR y el numerito impreso al mismo tiempo.
   * Si el OCR alcanza a leer las libras, la bolsa cuenta sola sin tocar nada;
   * la hoja con botones gigantes solo aparece si no se pudo leer.
   */
  function resolveLbsViaOcr(sku, raw, loc) {
    var canOcr = settings.ocr && window.BCOcr && BCOcr.isAvailable() && scanner && loc;
    var frame = canOcr ? scanner.grabFrame() : null;
    if (!frame) { openLbsSheet(sku, raw, null); return; }
    setMiniLog('🔍 Leyendo el número impreso de ' + coffeeName(sku) + '…');
    BCOcr.readLbsNear(frame, loc, 2600).then(function (res) {
      if (res && res.lbs) {
        applyBag(sku, res.lbs, 'ocr');
      } else {
        openLbsSheet(sku, raw, null);
      }
    });
  }

  function ensureCoffee(sku) {
    if (getCoffee(sku)) return;
    var name = sku.split('-').map(function (w) {
      return w.charAt(0) + w.slice(1).toLowerCase();
    }).join(' ');
    catalog.push({ sku: sku, name: name, aliases: [] });
    saveCatalog();
    toast('Café nuevo agregado al catálogo: ' + name);
  }

  function applyBag(sku, lbs, source) {
    if (scanSession.mode === 'free') {
      logScan(sku, lbs, null, source);
      var t = scanSession.freeTally[sku] || (scanSession.freeTally[sku] = { lbs: 0, bags: 0 });
      t.lbs = E.round2(t.lbs + lbs); t.bags++;
      scanSession.undoStack.push({ sku: sku, lbs: lbs, orderId: null });
      feedbackOk(sku, lbs, null);
      renderScanLines();
      return;
    }
    if (scanSession.mode !== 'order') return;
    var o = getOrder(scanSession.orderId);
    if (!o || !o.job) return;
    var r = E.applyScan(o.job, sku, lbs, Date.now());
    switch (r.status) {
      case 'ok':
      case 'line-complete':
        logScan(sku, lbs, o.id, source);
        scanSession.undoStack.push({ sku: sku, lbs: lbs, orderId: o.id });
        saveOrders();
        feedbackOk(sku, lbs, r);
        renderScanLines();
        break;
      case 'order-complete':
        logScan(sku, lbs, o.id, source);
        scanSession.undoStack.push({ sku: sku, lbs: lbs, orderId: o.id });
        o.status = 'lista';
        o.job.completedAt = Date.now();
        saveOrders();
        renderScanLines();
        syncOrder(o);
        showComplete(o);
        break;
      case 'not-in-order':
        flash('err'); soundErr(); vibrate([80, 60, 80]);
        setMiniLog('⛔ ' + coffeeName(sku) + ' NO va en esta orden');
        break;
      case 'line-full':
        flash('warn'); soundWarn(); vibrate([60, 40, 60]);
        setMiniLog('⚠️ ' + coffeeName(sku) + ' ya está completo en esta orden');
        break;
      case 'overfill':
        flash('warn'); soundWarn(); vibrate([60, 40, 60]);
        setMiniLog('⚠️ Bolsa de ' + E.fmtLbs(lbs) + ' lb no cabe: solo faltan ' +
          E.fmtLbs(r.remaining) + ' lb de ' + coffeeName(sku));
        break;
    }
  }

  function feedbackOk(sku, lbs, r) {
    flash('ok');
    if (r && r.status === 'line-complete') { soundOk(); setTimeout(soundOk, 120); }
    else soundOk();
    vibrate(35);
    var msg = '✔ +' + E.fmtLbs(lbs) + ' lb ' + coffeeName(sku);
    if (r && r.remaining > 0) msg += ' · faltan ' + E.fmtLbs(r.remaining) + ' lb';
    if (r && r.status === 'line-complete') msg += ' · ¡línea completa!';
    setMiniLog(msg);
    $('btn-undo').disabled = false;
  }

  function logScan(sku, lbs, orderId, source) {
    var entry = { ts: Date.now(), sku: sku, lbs: lbs, orderId: orderId, source: source || 'scan' };
    scans.push(entry);
    saveScans();
    if (window.BCSync) {
      BCSync.push('scan', {
        ts: new Date(entry.ts).toISOString(),
        orderId: orderId,
        sku: sku,
        coffee: coffeeName(sku),
        lbs: lbs,
        source: entry.source
      });
    }
  }

  function syncOrder(o) {
    if (!window.BCSync || !o.job) return;
    var t = E.jobTotals(o.job);
    BCSync.push('order', {
      orderId: o.id,
      box: E.suggestBox(t.needLbs, settings.boxRules, o.box),
      note: o.note || null,
      totalLbs: t.doneLbs,
      bags: t.bags,
      startedAt: o.job.startedAt ? new Date(o.job.startedAt).toISOString() : null,
      completedAt: o.job.completedAt ? new Date(o.job.completedAt).toISOString() : null,
      lines: o.job.lines.map(function (l) {
        return {
          sku: l.sku, coffee: l.name, needLbs: l.needLbs, doneLbs: l.doneLbs,
          bags: l.bags.map(function (b) { return b.lbs; })
        };
      })
    });
  }

  function setMiniLog(msg) {
    $('scan-log-mini').textContent = msg;
  }

  function undoLast() {
    var u = scanSession.undoStack.pop();
    if (!u) return;
    for (var i = scans.length - 1; i >= 0; i--) {
      var s = scans[i];
      if (s.sku === u.sku && s.lbs === u.lbs && s.orderId === u.orderId) { scans.splice(i, 1); break; }
    }
    saveScans();
    if (u.orderId) {
      var o = getOrder(u.orderId);
      if (o && o.job) {
        E.removeBag(o.job, u.sku, u.lbs);
        if (o.status === 'lista') { o.status = 'en-proceso'; o.job.completedAt = null; }
        saveOrders();
      }
    } else {
      var t = scanSession.freeTally[u.sku];
      if (t) { t.lbs = E.round2(t.lbs - u.lbs); t.bags--; if (t.bags <= 0) delete scanSession.freeTally[u.sku]; }
    }
    setMiniLog('↩ Deshecho: ' + E.fmtLbs(u.lbs) + ' lb ' + coffeeName(u.sku));
    $('btn-undo').disabled = scanSession.undoStack.length === 0;
    renderScanLines();
  }
  $('btn-undo').addEventListener('click', undoLast);

  // ---------- vista de escaneo ----------

  function renderScanView() {
    var active = !!scanSession.mode;
    $('scan-idle').hidden = active;
    $('scan-active').hidden = !active;
    $('lookup-card').hidden = true;
    if (!active) { renderPendingChips(); return; }
    if (scanSession.mode === 'free') {
      $('scan-title').textContent = 'Escaneo libre';
      $('scan-sub').textContent = 'Cada bolsa suma al inventario';
    } else {
      var o = getOrder(scanSession.orderId);
      $('scan-title').textContent = 'Orden ' + (o ? o.id : '');
      $('scan-sub').textContent = o ? orderSummaryText(o) : '';
    }
    $('btn-undo').disabled = scanSession.undoStack.length === 0;
    setMiniLog('');
    renderScanLines();
  }

  function setRing(pct) {
    var C = 119.4;
    $('ring-fg').style.strokeDashoffset = String(C - (C * Math.min(100, pct) / 100));
    $('scan-progress-pct').textContent = Math.round(pct) + '%';
  }

  var CHECK_SVG = '<svg viewBox="0 0 24 24"><path d="m5 12.5 4.5 4.5L19 7.5" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>';

  function renderScanLines() {
    var host = $('scan-lines');
    if (scanSession.mode === 'free') {
      var skus = Object.keys(scanSession.freeTally);
      if (!skus.length) {
        host.innerHTML = '<p class="empty-note">Apunta la cámara al QR de cada bolsa.<br>Aquí verás el conteo en vivo.</p>';
      } else {
        host.innerHTML = skus.map(function (sku) {
          var t = scanSession.freeTally[sku];
          return '<div class="line done">' +
            avatarHtml(sku) +
            '<div class="line-main"><div class="line-name">' + esc(coffeeName(sku)) + '</div>' +
            '<div class="line-bags">' + t.bags + ' bolsa' + (t.bags === 1 ? '' : 's') + '</div></div>' +
            '<div class="line-progress">' + E.fmtLbs(t.lbs) + ' lb</div>' +
            '</div>';
        }).join('');
      }
      setRing(0);
      $('scan-progress-pct').textContent = '';
      return;
    }
    var o = getOrder(scanSession.orderId);
    if (!o || !o.job) { host.innerHTML = ''; return; }
    host.innerHTML = o.job.lines.map(function (l) {
      var done = l.doneLbs >= l.needLbs - 1e-9;
      var pct = l.needLbs ? Math.min(100, (l.doneLbs / l.needLbs) * 100) : 0;
      var bags = l.bags.length
        ? l.bags.map(function (b) { return E.fmtLbs(b.lbs) + 'lb'; }).join(' + ')
        : 'sin bolsas aún';
      return '<div class="line' + (done ? ' done' : '') + '">' +
        (done ? '<span class="check-bubble">' + CHECK_SVG + '</span>' : '') +
        avatarHtml(l.sku) +
        '<div class="line-main"><div class="line-name">' + esc(l.name) + '</div>' +
        '<div class="line-bags">' + esc(bags) + '</div></div>' +
        '<div class="line-progress">' + E.fmtLbs(l.doneLbs) + ' / ' + E.fmtLbs(l.needLbs) +
        '<small>lb</small></div>' +
        '<div class="line-track"><div class="line-fill" style="width:' + pct + '%"></div></div>' +
        '</div>';
    }).join('');
    var t = E.jobTotals(o.job);
    setRing(t.needLbs ? (t.doneLbs / t.needLbs) * 100 : 0);
  }

  function renderPendingChips() {
    var host = $('pending-orders');
    var pend = orders.filter(function (o) { return o.status !== 'lista'; });
    $('pending-label').hidden = !orders.length;
    if (!pend.length) {
      host.innerHTML = orders.length
        ? '<p class="empty-note">🎉 Todas las órdenes del día están listas.</p>'
        : '<p class="empty-note">No hay órdenes importadas.<br>Ve a la pestaña Órdenes para pegarlas o subir el archivo.</p>';
      return;
    }
    host.innerHTML = pend.map(function (o) {
      var stack = o.items.slice(0, 4).map(function (it) { return avatarHtml(it.sku, 'sm'); }).join('');
      return '<button class="order-chip status-' + o.status + '" data-id="' + esc(o.id) + '">' +
        '<span class="avatar-stack">' + stack + '</span>' +
        '<span class="oc-main"><span class="oc-id">Orden ' + esc(o.id) + '</span><br>' +
        '<span class="oc-sub">' + esc(orderSummaryText(o)) + '</span></span>' +
        '<span class="oc-status">' + (o.status === 'en-proceso' ? 'EN PROCESO' : 'PENDIENTE') + '</span>' +
        '</button>';
    }).join('');
    host.querySelectorAll('.order-chip').forEach(function (b) {
      b.addEventListener('click', function () { startOrder(b.dataset.id); });
    });
  }

  $('btn-start-order').addEventListener('click', function () {
    var id = $('order-input').value.trim();
    if (!id) { toast('Escribe el número de orden.'); return; }
    $('order-input').value = '';
    startOrder(id);
  });
  $('order-input').addEventListener('keydown', function (e) {
    if (e.key === 'Enter') $('btn-start-order').click();
  });
  $('btn-free-scan').addEventListener('click', startFree);
  $('btn-exit-scan').addEventListener('click', exitScan);

  // ---------- orden completa ----------

  var BOX_SVG = '<svg width="22" height="22" viewBox="0 0 24 24"><path d="m12 3 8 4.2v9.6L12 21l-8-4.2V7.2L12 3Z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/><path d="M4.4 7.5 12 11.5l7.6-4M12 11.5V20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/></svg>';

  function showComplete(o) {
    soundComplete();
    vibrate([60, 60, 60, 60, 120]);
    var t = E.jobTotals(o.job);
    var box = E.suggestBox(t.needLbs, settings.boxRules, o.box);
    $('complete-title').textContent = '¡Orden ' + o.id + ' lista!';
    $('complete-box').innerHTML = box ? BOX_SVG + ' ' + esc(box) : '';
    $('complete-note').textContent = o.note ? '📝 ' + o.note : '';
    $('complete-total').textContent = t.doneLbs + ' lb en ' + t.bags + ' bolsas';
    var next = orders.find(function (x) { return x.status !== 'lista'; });
    $('btn-next-order').hidden = !next;
    if (next) $('btn-next-order').textContent = 'Siguiente: orden ' + next.id;
    $('complete-overlay').hidden = false;
    scanSession.paused = true;
  }
  $('btn-next-order').addEventListener('click', function () {
    $('complete-overlay').hidden = true;
    scanSession.paused = false;
    var next = orders.find(function (x) { return x.status !== 'lista'; });
    if (next) startOrder(next.id); else exitScan();
  });
  $('btn-close-complete').addEventListener('click', function () {
    $('complete-overlay').hidden = true;
    scanSession.paused = false;
    exitScan();
  });

  // ---------- hojas (sheets) ----------

  var sheetToken = 0;

  function openSheet(html) {
    sheetToken++;
    $('sheet').innerHTML = html;
    $('sheet-backdrop').hidden = false;
    scanSession.paused = true;
    return sheetToken;
  }
  function closeSheet() {
    sheetToken++;
    $('sheet-backdrop').hidden = true;
    $('sheet').innerHTML = '';
    scanSession.paused = false;
  }
  $('sheet-backdrop').addEventListener('click', function (e) {
    if (e.target === this) closeSheet();
  });

  function lbsChipsHtml(idPrefix) {
    return '<div class="big-lbs" id="' + idPrefix + '-chips">' +
      '<button data-lbs="1">1 lb</button>' +
      '<button data-lbs="2">2 lb</button>' +
      '<button data-lbs="5">5 lb</button>' +
      '</div>' +
      '<div class="form-inline"><input id="' + idPrefix + '-custom" type="number" step="0.25" min="0.25" ' +
      'placeholder="Otras libras"><button id="' + idPrefix + '-custom-ok" class="btn-tonal">Usar</button></div>';
  }

  // OCR: intenta leer el número impreso y avisa a la hoja abierta
  function runOcrAssist(loc, token, onResult) {
    if (!settings.ocr || !window.BCOcr || !BCOcr.isAvailable() || !scanner || !loc) {
      onResult(null, token); return;
    }
    var frame = scanner.grabFrame();
    if (!frame) { onResult(null, token); return; }
    BCOcr.readLbsNear(frame, loc, 3500).then(function (res) {
      onResult(res, token);
    });
  }

  function ocrStatusHtml() {
    return '<div class="ocr-status" id="ocr-status"><span class="spin"></span> Leyendo el número impreso…</div>';
  }

  // QR viejo con café conocido pero libras variables → preguntar libras (1 toque)
  // Si el OCR alcanza a leer el número impreso, cuenta solo.
  function openLbsSheet(sku, raw, loc) {
    var canOcr = settings.ocr && window.BCOcr && BCOcr.isAvailable() && scanner && loc;
    var token = openSheet(
      '<h3>' + esc(coffeeName(sku)) + ' — ¿de cuántas libras es la bolsa?</h3>' +
      (canOcr ? ocrStatusHtml() : '') +
      lbsChipsHtml('lbs') +
      '<button id="lbs-cancel" class="btn-tonal wide">Cancelar</button>'
    );
    function pick(lbs, viaOcr) {
      closeSheet();
      applyBag(sku, lbs, viaOcr ? 'ocr' : 'scan');
      if (viaOcr) toast('Número leído del empaque: ' + E.fmtLbs(lbs) + ' lb');
    }
    $('sheet').querySelectorAll('.big-lbs button').forEach(function (b) {
      b.addEventListener('click', function () { pick(parseFloat(b.dataset.lbs)); });
    });
    $('lbs-custom-ok').addEventListener('click', function () {
      var v = parseFloat($('lbs-custom').value);
      if (v > 0) pick(v);
    });
    $('lbs-cancel').addEventListener('click', closeSheet);
    if (canOcr) {
      runOcrAssist(loc, token, function (res, tk) {
        if (tk !== sheetToken) return; // la hoja ya se cerró o cambió
        var st = $('ocr-status');
        if (res && res.lbs) {
          pick(res.lbs, true);
        } else if (st) {
          st.innerHTML = 'No pude leer el número — elige con un toque:';
        }
      });
    }
  }

  // QR desconocido → aprenderlo una sola vez (el OCR sugiere las libras si puede)
  function openLegacySheet(raw, loc) {
    var options = catalog.map(function (c) {
      return '<option value="' + esc(c.sku) + '">' + esc(c.name) + '</option>';
    }).join('');
    var canOcr = settings.ocr && window.BCOcr && BCOcr.isAvailable() && scanner && loc;
    var token = openSheet(
      '<h3>Etiqueta antigua / desconocida</h3>' +
      '<div class="sheet-raw">' + esc(raw.length > 120 ? raw.slice(0, 120) + '…' : raw) + '</div>' +
      '<label>¿Qué café es?<select id="legacy-coffee">' + options + '</select></label>' +
      '<label style="margin-top:12px">¿De cuántas libras?</label>' +
      (canOcr ? ocrStatusHtml() : '') +
      lbsChipsHtml('legacy') +
      '<label class="toggle"><input type="checkbox" id="legacy-varies"> Este QR se usa en varios tamaños ' +
      '(preguntar libras cada vez)</label>' +
      '<button id="legacy-cancel" class="btn-tonal wide">Cancelar (no contar)</button>' +
      '<p class="hint">Se recordará para siempre: la próxima vez cuenta automático.</p>'
    );
    function finish(lbs) {
      var sku = $('legacy-coffee').value;
      var varies = $('legacy-varies').checked;
      legacyMap[raw] = { sku: sku, lbs: varies ? null : lbs };
      saveLegacy();
      closeSheet();
      if (scanSession.mode) applyBag(sku, lbs, 'scan');
      toast('QR aprendido: ' + coffeeName(sku) + (varies ? ' (libras variables)' : ' ' + E.fmtLbs(lbs) + ' lb'));
    }
    $('sheet').querySelectorAll('.big-lbs button').forEach(function (b) {
      b.addEventListener('click', function () { finish(parseFloat(b.dataset.lbs)); });
    });
    $('legacy-custom-ok').addEventListener('click', function () {
      var v = parseFloat($('legacy-custom').value);
      if (v > 0) finish(v);
    });
    $('legacy-cancel').addEventListener('click', closeSheet);
    if (canOcr) {
      runOcrAssist(loc, token, function (res, tk) {
        if (tk !== sheetToken) return;
        var st = $('ocr-status');
        if (res && res.lbs) {
          if (st) st.innerHTML = 'Número impreso leído: <strong>' + E.fmtLbs(res.lbs) + ' lb</strong> ✓';
          var btn = $('sheet').querySelector('.big-lbs button[data-lbs="' + res.lbs + '"]');
          if (btn) btn.classList.add('suggested');
          else { var inp = $('legacy-custom'); if (inp) inp.value = res.lbs; }
          // si trae el número impreso, seguramente el mismo QR se usa en varios tamaños:
          // marcarlo hace que la cámara lea QR + número en cada bolsa (transición)
          var vch = $('legacy-varies');
          if (vch && !vch.checked) vch.checked = true;
        } else if (st) {
          st.remove();
        }
      });
    }
  }

  // agregar bolsa manual (QR dañado)
  $('btn-manual').addEventListener('click', function () {
    if (scanSession.mode === 'order') {
      var o = getOrder(scanSession.orderId);
      if (!o || !o.job) return;
      var lines = o.job.lines.filter(function (l) { return l.doneLbs < l.needLbs - 1e-9; });
      if (!lines.length) { toast('La orden ya está completa.'); return; }
      openSheet(
        '<h3>Agregar bolsa manual</h3><p class="hint">Para bolsas con QR dañado o ilegible.</p>' +
        '<div class="sheet-list">' + lines.map(function (l) {
          return '<button data-sku="' + esc(l.sku) + '">' + avatarHtml(l.sku, 'sm') +
            '<span>' + esc(l.name) +
            '<small>faltan ' + E.fmtLbs(l.needLbs - l.doneLbs) + ' lb</small></span></button>';
        }).join('') + '</div>'
      );
      $('sheet').querySelectorAll('.sheet-list button').forEach(function (b) {
        b.addEventListener('click', function () {
          var sku = b.dataset.sku;
          openSheet('<h3>' + esc(coffeeName(sku)) + ' — ¿bolsa de cuántas libras?</h3>' + lbsChipsHtml('man') +
            '<button id="man-cancel" class="btn-tonal wide">Cancelar</button>');
          $('sheet').querySelectorAll('.big-lbs button').forEach(function (bb) {
            bb.addEventListener('click', function () { closeSheet(); applyBag(sku, parseFloat(bb.dataset.lbs), 'manual'); });
          });
          $('man-custom-ok').addEventListener('click', function () {
            var v = parseFloat($('man-custom').value);
            if (v > 0) { closeSheet(); applyBag(sku, v, 'manual'); }
          });
          $('man-cancel').addEventListener('click', closeSheet);
        });
      });
    } else if (scanSession.mode === 'free') {
      var options = catalog.map(function (c) {
        return '<option value="' + esc(c.sku) + '">' + esc(c.name) + '</option>';
      }).join('');
      openSheet(
        '<h3>Agregar bolsa manual</h3>' +
        '<label>Café<select id="man-coffee">' + options + '</select></label>' +
        '<label style="margin-top:12px">Libras</label>' + lbsChipsHtml('man') +
        '<button id="man-cancel" class="btn-tonal wide">Cancelar</button>'
      );
      $('sheet').querySelectorAll('.big-lbs button').forEach(function (bb) {
        bb.addEventListener('click', function () {
          var sku = $('man-coffee').value;
          closeSheet(); applyBag(sku, parseFloat(bb.dataset.lbs), 'manual');
        });
      });
      $('man-custom-ok').addEventListener('click', function () {
        var v = parseFloat($('man-custom').value);
        if (v > 0) { var sku = $('man-coffee').value; closeSheet(); applyBag(sku, v, 'manual'); }
      });
      $('man-cancel').addEventListener('click', closeSheet);
    }
  });

  // ================= órdenes =================

  var importParsed = null;
  var X_SVG = '<svg class="ic"><use href="#i-x"/></svg>';

  function renderOrders() {
    var host = $('orders-list');
    var sum = $('orders-summary');
    if (!orders.length) {
      sum.innerHTML = '';
      host.innerHTML = '<p class="empty-note">Sin órdenes.<br>Pega el texto de las órdenes del día abajo, o súbelo como archivo.</p>';
      $('import-box').open = true;
      return;
    }
    var listas = orders.filter(function (o) { return o.status === 'lista'; }).length;
    var lbsTotal = 0;
    orders.forEach(function (o) {
      o.items.forEach(function (it) { lbsTotal = E.round2(lbsTotal + it.lbsEach * it.qty); });
    });
    sum.innerHTML =
      '<div class="card"><div class="card-num">' + orders.length + '</div><div class="card-label">órdenes</div></div>' +
      '<div class="card"><div class="card-num">' + listas + '</div><div class="card-label">listas</div></div>' +
      '<div class="card"><div class="card-num">' + E.fmtLbs(lbsTotal) + '</div><div class="card-label">lbs del día</div></div>';
    var sorted = orders.slice().sort(function (a, b) {
      var w = { 'en-proceso': 0, 'pendiente': 1, 'lista': 2 };
      return (w[a.status] - w[b.status]) || (a.createdAt - b.createdAt);
    });
    host.innerHTML = sorted.map(function (o) {
      var badge = o.status === 'lista' ? 'LISTA' : o.status === 'en-proceso' ? 'EN PROCESO' : 'PENDIENTE';
      var stack = o.items.slice(0, 4).map(function (it) { return avatarHtml(it.sku, 'sm'); }).join('');
      var boxHtml = o.box ? ' <svg class="ic"><use href="#i-box"/></svg> ' + esc(o.box) : '';
      return '<div class="order-row status-' + o.status + '" data-id="' + esc(o.id) + '">' +
        '<span class="avatar-stack">' + stack + '</span>' +
        '<div class="or-main">' +
        '<div class="or-id">Orden ' + esc(o.id) + boxHtml + '</div>' +
        '<div class="or-items">' + esc(orderSummaryText(o)) + (o.note ? ' · 📝 ' + esc(o.note) : '') + '</div>' +
        '</div>' +
        '<span class="or-badge">' + badge + '</span>' +
        '<button class="or-del" title="Borrar">' + X_SVG + '</button>' +
        '</div>';
    }).join('');
    host.querySelectorAll('.order-row').forEach(function (row) {
      row.addEventListener('click', function (e) {
        if (e.target.closest('.or-del')) {
          if (confirm('¿Borrar la orden ' + row.dataset.id + '?')) {
            orders = orders.filter(function (o) { return o.id !== row.dataset.id; });
            saveOrders(); renderOrders();
          }
          return;
        }
        showView('scan');
        startOrder(row.dataset.id);
      });
    });
  }

  function renderImportPreview() {
    var text = $('orders-text').value;
    var host = $('import-preview');
    if (!text.trim()) { host.innerHTML = ''; importParsed = null; $('btn-import').disabled = true; return; }
    importParsed = E.parseOrdersText(text, catalog);
    var html = '';
    importParsed.orders.forEach(function (o) {
      html += '<div class="preview-order"><span class="po-id">Orden ' + esc(o.id) + '</span> — ' +
        esc(o.items.map(function (it) {
          return it.qty + '× ' + E.fmtLbs(it.lbsEach) + 'lb ' + it.name;
        }).join(', ')) +
        (o.box ? ' · caja: ' + esc(o.box) : '') + '</div>';
    });
    if (importParsed.newCoffees.length) {
      html += '<div class="preview-new">Cafés nuevos que se agregarán: ' +
        esc(importParsed.newCoffees.map(function (c) { return c.name; }).join(', ')) + '</div>';
    }
    importParsed.warnings.forEach(function (w) {
      html += '<div class="preview-warn">⚠ ' + esc(w) + '</div>';
    });
    if (!importParsed.orders.length) html += '<div class="preview-warn">No reconocí ninguna orden todavía.</div>';
    host.innerHTML = html;
    $('btn-import').disabled = !importParsed.orders.length;
    $('btn-import').textContent = importParsed.orders.length
      ? 'Importar ' + importParsed.orders.length + ' órdenes' : 'Importar';
  }
  $('orders-text').addEventListener('input', function () {
    clearTimeout(renderImportPreview._t);
    renderImportPreview._t = setTimeout(renderImportPreview, 250);
  });
  $('orders-file').addEventListener('change', function () {
    var f = this.files[0];
    if (!f) return;
    var reader = new FileReader();
    reader.onload = function () {
      $('orders-text').value = String(reader.result);
      renderImportPreview();
    };
    reader.readAsText(f);
    this.value = '';
  });
  $('btn-import').addEventListener('click', function () {
    if (!importParsed || !importParsed.orders.length) return;
    importParsed.newCoffees.forEach(function (c) { catalog.push(c); });
    if (importParsed.newCoffees.length) saveCatalog();
    var replaced = 0, skipped = [];
    importParsed.orders.forEach(function (po) {
      var existing = getOrder(po.id);
      if (existing) {
        // una orden ya empezada o lista no se pisa: se perdería el progreso
        if (existing.status !== 'pendiente') { skipped.push(po.id); return; }
        orders = orders.filter(function (o) { return o.id !== po.id; });
        replaced++;
      }
      orders.push({
        id: po.id, items: po.items, box: po.box, note: po.note,
        status: 'pendiente', job: null, createdAt: Date.now()
      });
    });
    saveOrders();
    if (skipped.length) {
      toast('No reemplacé ' + skipped.length + ' órdenes ya empezadas/listas (' +
        skipped.join(', ') + '). Bórralas primero si quieres reimportarlas.', 4200);
    }
    $('orders-text').value = '';
    $('import-preview').innerHTML = '';
    $('btn-import').disabled = true;
    $('btn-import').textContent = 'Importar';
    $('import-box').open = false;
    importParsed = null;
    renderOrders();
    toast('Órdenes importadas' + (replaced ? ' (' + replaced + ' reemplazadas)' : '') + ' ✔');
  });
  $('btn-clear-done').addEventListener('click', function () {
    orders = orders.filter(function (o) { return o.status !== 'lista'; });
    saveOrders(); renderOrders();
  });
  $('btn-clear-orders').addEventListener('click', function () {
    if (confirm('¿Borrar TODAS las órdenes? (los escaneos registrados no se pierden)')) {
      orders = []; saveOrders(); renderOrders();
    }
  });

  // ================= etiquetas =================

  var labelLbs = 1;

  function renderLabelCoffees() {
    var sel = $('label-coffee');
    var prev = sel.value;
    sel.innerHTML = catalog.map(function (c) {
      return '<option value="' + esc(c.sku) + '">' + esc(c.name) + '</option>';
    }).join('');
    if (prev) sel.value = prev;
  }
  $('label-lbs-chips').addEventListener('click', function (e) {
    var b = e.target.closest('button[data-lbs]');
    if (!b) return;
    e.preventDefault();
    labelLbs = parseFloat(b.dataset.lbs);
    $('label-lbs-custom').value = '';
    this.querySelectorAll('.chip').forEach(function (c) { c.classList.toggle('active', c === b); });
  });
  $('label-lbs-custom').addEventListener('input', function () {
    var v = parseFloat(this.value);
    if (v > 0) {
      labelLbs = v;
      $('label-lbs-chips').querySelectorAll('.chip').forEach(function (c) { c.classList.remove('active'); });
    }
  });
  $('btn-gen-labels').addEventListener('click', function () {
    var sku = $('label-coffee').value;
    if (!sku) { toast('Agrega cafés al catálogo primero.'); return; }
    var count = Math.max(1, Math.min(120, parseInt($('label-count').value, 10) || 12));
    var size = $('label-size').value;
    var payload = E.makeQRPayload(sku, labelLbs);
    var qr = qrcode(0, 'Q');
    qr.addData(payload);
    qr.make();
    var svg = qr.createSvgTag(4, 2);
    var name = coffeeName(sku);
    var one = '<div class="qr-label size-' + size + '">' + svg +
      '<div class="ql-lbs">' + E.fmtLbs(labelLbs) + ' LB</div>' +
      '<div class="ql-name">' + esc(name) + '</div></div>';
    var html = '';
    for (var i = 0; i < count; i++) html += one;
    $('labels-grid').innerHTML = html;
    var widths = { s: '2.5cm', m: '3.5cm', l: '5cm' };
    document.documentElement.style.setProperty('--print-label-w', widths[size] || '3.5cm');
    $('btn-print-labels').disabled = false;
    toast(count + ' etiquetas de ' + name + ' ' + E.fmtLbs(labelLbs) + ' lb · QR: ' + payload);
  });
  $('btn-print-labels').addEventListener('click', function () {
    document.body.classList.add('printing-labels');
    window.print();
    setTimeout(function () { document.body.classList.remove('printing-labels'); }, 500);
  });

  // ================= reportes =================

  var reportRange = 'today';

  function rangeBounds(kind) {
    var now = Date.now();
    if (kind === 'today') return E.dayRange(now);
    if (kind === 'month') return E.monthRange(now, 0);
    if (kind === 'prev-month') return E.monthRange(now, -1);
    return { from: 0, to: Infinity };
  }

  function renderReports() {
    var b = rangeBounds(reportRange);
    var sum = E.summarizeScans(scans, b.from, b.to);
    $('report-cards').innerHTML =
      '<div class="card"><div class="card-num">' + E.fmtLbs(sum.totalLbs) + '</div><div class="card-label">libras</div></div>' +
      '<div class="card"><div class="card-num">' + sum.totalBags + '</div><div class="card-label">bolsas</div></div>' +
      '<div class="card"><div class="card-num">' + sum.orderCount + '</div><div class="card-label">órdenes</div></div>';
    if (!sum.perSku.length) {
      $('report-table').innerHTML = '<p class="empty-note">Sin escaneos en este periodo.</p>';
    } else {
      var rows = sum.perSku.map(function (p) {
        var sizes = Object.keys(p.sizes).sort(function (a, b2) { return parseFloat(a) - parseFloat(b2); })
          .map(function (k) { return k + 'lb×' + p.sizes[k]; }).join(' · ');
        return '<tr><td><span class="cell-prod">' + avatarHtml(p.sku, 'sm') + esc(coffeeName(p.sku)) + '</span></td>' +
          '<td class="num">' + E.fmtLbs(p.totalLbs) + '</td>' +
          '<td class="num">' + p.bags + '</td>' +
          '<td>' + esc(sizes) + '</td></tr>';
      }).join('');
      $('report-table').innerHTML = '<div class="table-wrap"><table>' +
        '<tr><th>Café</th><th class="num">Libras</th><th class="num">Bolsas</th><th>Por tamaño</th></tr>' +
        rows + '</table></div>';
    }
    renderWoo();
  }

  document.querySelectorAll('#report-range .chip').forEach(function (b) {
    b.addEventListener('click', function () {
      reportRange = b.dataset.range;
      document.querySelectorAll('#report-range .chip').forEach(function (c) { c.classList.toggle('active', c === b); });
      renderReports();
    });
  });

  $('btn-export-detail').addEventListener('click', function () {
    var b = rangeBounds(reportRange);
    var rows = [['fecha', 'hora', 'orden', 'cafe', 'lbs', 'fuente']];
    scans.forEach(function (s) {
      if (s.ts < b.from || s.ts >= b.to) return;
      var d = new Date(s.ts);
      rows.push([
        d.toLocaleDateString('es-MX'), d.toLocaleTimeString('es-MX'),
        s.orderId || '', coffeeName(s.sku), s.lbs, s.source
      ]);
    });
    download('burman-detalle-' + reportRange + '.csv', E.csvStringify(rows));
  });
  $('btn-export-summary').addEventListener('click', function () {
    var b = rangeBounds(reportRange);
    var sum = E.summarizeScans(scans, b.from, b.to);
    var allSizes = {};
    sum.perSku.forEach(function (p) { Object.keys(p.sizes).forEach(function (k) { allSizes[k] = 1; }); });
    var sizeKeys = Object.keys(allSizes).sort(function (a, b2) { return parseFloat(a) - parseFloat(b2); });
    var head = ['cafe', 'libras', 'bolsas'].concat(sizeKeys.map(function (k) { return 'bolsas_' + k + 'lb'; }));
    var rows = [head];
    sum.perSku.forEach(function (p) {
      rows.push([coffeeName(p.sku), p.totalLbs, p.bags].concat(sizeKeys.map(function (k) { return p.sizes[k] || 0; })));
    });
    rows.push(['TOTAL', sum.totalLbs, sum.totalBags].concat(sizeKeys.map(function () { return ''; })));
    download('burman-resumen-' + reportRange + '.csv', E.csvStringify(rows));
  });

  // ---------- WooCommerce ----------

  var wooSelectedMonth = null;

  $('woo-file').addEventListener('change', function () {
    var f = this.files[0];
    if (!f) return;
    var reader = new FileReader();
    var fname = f.name;
    reader.onload = function () {
      var res = E.parseWooCSV(String(reader.result));
      if (!res.items.length) {
        $('woo-status').textContent = '⚠ ' + (res.warnings[0] || 'No pude leer el archivo.');
        return;
      }
      // agrupar por mes según la fecha del pedido; sin fecha → mes actual
      var byMonth = {};
      var images = {};
      res.items.forEach(function (it) {
        var ts = E.parseWooDate(it.dateStr);
        var mk = ts ? E.monthKey(ts) : E.monthKey(Date.now());
        if (!byMonth[mk]) byMonth[mk] = new Map();
        if (!byMonth[mk].has(it.product)) byMonth[mk].set(it.product, { product: it.product, qty: 0 });
        byMonth[mk].get(it.product).qty += it.qty;
        if (it.image && !images[E.norm(it.product)]) images[E.norm(it.product)] = it.image;
      });
      var months = Object.keys(byMonth);
      months.forEach(function (mk) {
        wooData[mk] = {
          items: Array.from(byMonth[mk].values()),
          fileName: fname,
          importedAt: Date.now()
        };
      });
      saveWooData();
      // guardar imágenes de producto para el catálogo (si el CSV las trae)
      wooImages = Object.assign(wooImages, images);
      saveWooImages();
      wooSelectedMonth = months.sort().reverse()[0];
      $('woo-status').textContent = '✔ Importado ' + fname + ' → ' + months.join(', ') +
        (res.warnings.length ? ' · ⚠ ' + res.warnings.join(' ') : '');
      renderWoo();
    };
    reader.readAsText(f);
    this.value = '';
  });

  function applyWooImage(productNorm, sku) {
    var img = wooImages[productNorm];
    if (!img) return;
    var c = getCoffee(sku);
    if (c && !c.image) { c.image = img; saveCatalog(); }
  }

  function renderWoo() {
    var months = Object.keys(wooData).sort().reverse();
    var host = $('woo-months');
    if (!months.length) {
      host.innerHTML = '';
      $('woo-unmatched').innerHTML = '';
      $('woo-compare').innerHTML = '';
      $('btn-export-compare').hidden = true;
      return;
    }
    if (!wooSelectedMonth || months.indexOf(wooSelectedMonth) === -1) wooSelectedMonth = months[0];
    host.innerHTML = months.map(function (mk) {
      return '<button class="chip' + (mk === wooSelectedMonth ? ' active' : '') + '" data-mk="' + mk + '">' + mk + '</button>';
    }).join('');
    host.querySelectorAll('.chip').forEach(function (b) {
      b.addEventListener('click', function () { wooSelectedMonth = b.dataset.mk; renderWoo(); });
    });

    var data = wooData[wooSelectedMonth];
    var agg = E.aggregateWoo(data.items, catalog, wooMap);
    // guardar mapeos automáticos para no volver a adivinar
    var autoKeys = Object.keys(agg.autoMapped);
    if (autoKeys.length) {
      autoKeys.forEach(function (k) {
        wooMap[k] = agg.autoMapped[k];
        applyWooImage(k, agg.autoMapped[k].sku);
      });
      saveWooMap();
    }

    // productos sin resolver
    var un = $('woo-unmatched');
    if (agg.unmatched.length) {
      un.innerHTML = '<p class="preview-warn">' + agg.unmatched.length +
        ' productos de la tienda no se pudieron identificar. Asigna café y libras (se recuerda para siempre):</p>' +
        agg.unmatched.map(function (u) {
          var options = catalog.map(function (c) {
            return '<option value="' + esc(c.sku) + '"' + (u.guessSku === c.sku ? ' selected' : '') + '>' +
              esc(c.name) + '</option>';
          }).join('');
          return '<div class="preview-order" data-product="' + esc(u.product) + '">' +
            '<div><strong>' + esc(u.product) + '</strong> <small>(' + u.qty + ' vendidos)</small></div>' +
            '<div class="form-inline" style="margin-top:6px">' +
            '<select class="um-coffee">' + options + '</select>' +
            '<input class="um-lbs" type="number" step="0.25" min="0.25" placeholder="lbs" style="width:90px"' +
            (u.guessLbs ? ' value="' + u.guessLbs + '"' : '') + '>' +
            '<button class="btn-primary um-save">OK</button>' +
            '</div></div>';
        }).join('');
      un.querySelectorAll('.um-save').forEach(function (btn) {
        btn.addEventListener('click', function () {
          var wrap = btn.closest('.preview-order');
          var product = wrap.dataset.product;
          var sku = wrap.querySelector('.um-coffee').value;
          var lbs = parseFloat(wrap.querySelector('.um-lbs').value);
          if (!(lbs > 0)) { toast('Escribe las libras por unidad.'); return; }
          wooMap[E.norm(product)] = { sku: sku, lbsEach: lbs };
          applyWooImage(E.norm(product), sku);
          saveWooMap();
          renderWoo();
        });
      });
    } else un.innerHTML = '';

    // comparación del mes: escaneado vs tienda
    var parts = wooSelectedMonth.split('-');
    var from = new Date(parseInt(parts[0], 10), parseInt(parts[1], 10) - 1, 1).getTime();
    var to = new Date(parseInt(parts[0], 10), parseInt(parts[1], 10), 1).getTime();
    var scanSum = E.summarizeScans(scans, from, to);
    var cmp = E.compareTotals(scanSum.perSku, agg.perSku);
    if (!cmp.length) {
      $('woo-compare').innerHTML = '<p class="empty-note">Sin datos para comparar en ' + wooSelectedMonth + '.</p>';
      $('btn-export-compare').hidden = true;
      return;
    }
    var totScan = 0, totWoo = 0;
    var rows = cmp.map(function (r) {
      totScan = E.round2(totScan + r.scanLbs); totWoo = E.round2(totWoo + r.wooLbs);
      var cls = r.diff === 0 ? 'diff-zero' : (r.diff > 0 ? 'diff-pos' : 'diff-neg');
      var sign = r.diff > 0 ? '+' : '';
      return '<tr><td><span class="cell-prod">' + avatarHtml(r.sku, 'sm') + esc(coffeeName(r.sku)) + '</span></td>' +
        '<td class="num">' + E.fmtLbs(r.scanLbs) + '</td>' +
        '<td class="num">' + E.fmtLbs(r.wooLbs) + '</td>' +
        '<td class="num ' + cls + '">' + sign + E.fmtLbs(r.diff) + '</td></tr>';
    }).join('');
    var totCls = (totScan - totWoo) === 0 ? 'diff-zero' : ((totScan - totWoo) > 0 ? 'diff-pos' : 'diff-neg');
    $('woo-compare').innerHTML = '<div class="table-wrap"><table>' +
      '<tr><th>Café</th><th class="num">Escaneado lb</th><th class="num">Tienda lb</th><th class="num">Dif.</th></tr>' +
      rows +
      '<tr><td><strong>TOTAL</strong></td><td class="num"><strong>' + E.fmtLbs(totScan) + '</strong></td>' +
      '<td class="num"><strong>' + E.fmtLbs(totWoo) + '</strong></td>' +
      '<td class="num ' + totCls + '"><strong>' + E.fmtLbs(E.round2(totScan - totWoo)) + '</strong></td></tr>' +
      '</table></div>' +
      '<p class="hint">Dif. positiva = se escaneó más de lo vendido en la tienda; ' +
      'negativa = falta por escanear o hubo venta fuera del escáner.</p>';
    $('btn-export-compare').hidden = false;
    $('btn-export-compare').onclick = function () {
      var out = [['cafe', 'escaneado_lbs', 'tienda_lbs', 'diferencia']];
      cmp.forEach(function (r) { out.push([coffeeName(r.sku), r.scanLbs, r.wooLbs, r.diff]); });
      out.push(['TOTAL', totScan, totWoo, E.round2(totScan - totWoo)]);
      download('burman-comparacion-' + wooSelectedMonth + '.csv', E.csvStringify(out));
    };
  }

  // ================= ajustes =================

  async function fetchStoreImages() {
    var base = (settings.storeUrl || '').trim().replace(/\/+$/, '');
    if (!base) { toast('Escribe la URL de la tienda.'); return; }
    var btn = $('btn-fetch-images');
    btn.disabled = true; btn.textContent = 'Buscando en la tienda…';
    var found = 0, matched = 0;
    try {
      for (var page = 1; page <= 5; page++) {
        var res = await fetch(base + '/wp-json/wc/store/v1/products?per_page=100&page=' + page, { mode: 'cors' });
        if (!res.ok) { if (page === 1) throw new Error('HTTP ' + res.status); break; }
        var prods = await res.json();
        if (!Array.isArray(prods) || !prods.length) break;
        prods.forEach(function (pr) {
          var img = pr.images && pr.images[0] && (pr.images[0].thumbnail || pr.images[0].src);
          if (!pr.name || !img) return;
          found++;
          wooImages[E.norm(pr.name)] = img;
          var sz = E.extractSize(pr.name);
          var namePart = sz ? pr.name.slice(0, sz.index) + ' ' + pr.name.slice(sz.index + sz.match.length) : pr.name;
          var c = E.findCoffee(catalog, E.cleanProductName(namePart));
          if (c && !c.image) { c.image = img; matched++; }
        });
        if (prods.length < 100) break;
      }
      saveCatalog();
      saveWooImages();
      renderSettings();
      toast(matched ? '✔ ' + matched + ' cafés con imagen de la tienda (' + found + ' productos leídos)'
        : found ? 'Leí ' + found + ' productos pero ninguno coincidió. Agrega alias o asigna la foto a mano.'
          : 'La tienda no devolvió productos.', 3200);
    } catch (err) {
      toast('No pude leer la tienda (' + (err && err.message ? err.message : err) +
        '). Puedes asignar la foto tocando la imagen del café.', 3800);
    }
    btn.disabled = false; btn.textContent = 'Traer imágenes de la tienda';
  }
  $('btn-fetch-images').addEventListener('click', fetchStoreImages);
  $('store-url').addEventListener('change', function () {
    settings.storeUrl = this.value.trim(); saveSettings();
  });

  var PENCIL_SVG = '<svg class="ic" viewBox="0 0 24 24"><path d="m14.5 5.5 4 4L8 20H4v-4L14.5 5.5ZM12.5 7.5l4 4" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>';

  function renderSettings() {
    // catálogo
    var host = $('catalog-list');
    host.innerHTML = catalog.map(function (c, i) {
      return '<div class="catalog-row" data-i="' + i + '">' +
        '<button class="row-btn cr-img" style="padding:0;border-radius:14px" title="Imagen">' + avatarHtml(c.sku) + '</button>' +
        '<div class="cr-main"><div class="cr-name">' + esc(c.name) + '</div>' +
        '<div class="cr-sku">' + esc(c.sku) +
        (c.aliases && c.aliases.length ? ' · alias: ' + esc(c.aliases.join(', ')) : '') + '</div></div>' +
        '<button class="row-btn cr-alias" title="Alias">' + PENCIL_SVG + '</button>' +
        '<button class="row-btn cr-del" title="Borrar">' + X_SVG + '</button>' +
        '</div>';
    }).join('');
    host.querySelectorAll('.catalog-row').forEach(function (row) {
      var i = parseInt(row.dataset.i, 10);
      row.querySelector('.cr-del').addEventListener('click', function () {
        if (confirm('¿Borrar "' + catalog[i].name + '" del catálogo?')) {
          catalog.splice(i, 1); saveCatalog(); renderSettings();
        }
      });
      row.querySelector('.cr-alias').addEventListener('click', function () {
        var c = catalog[i];
        var v = prompt('Alias de "' + c.name + '" separados por coma\n(otros nombres con los que aparece en órdenes o en la tienda):',
          (c.aliases || []).join(', '));
        if (v == null) return;
        c.aliases = v.split(',').map(function (s) { return s.trim(); }).filter(Boolean);
        saveCatalog(); renderSettings();
      });
      row.querySelector('.cr-img').addEventListener('click', function () {
        var c = catalog[i];
        var v = prompt('URL de la imagen del producto para "' + c.name + '"\n(cópiala de la tienda; vacío = quitar):',
          c.image || '');
        if (v == null) return;
        c.image = v.trim() || undefined;
        saveCatalog(); renderSettings();
      });
    });

    // QRs aprendidos
    var lh = $('legacy-list');
    var keys = Object.keys(legacyMap);
    lh.innerHTML = keys.length ? keys.map(function (k) {
      var m = legacyMap[k];
      return '<div class="legacy-row" data-k="' + esc(k) + '">' +
        '<span class="lr-raw" title="' + esc(k) + '">' + esc(k) + '</span>' +
        '<span class="lr-map">' + esc(coffeeName(m.sku)) + ' · ' + (m.lbs ? E.fmtLbs(m.lbs) + ' lb' : 'pregunta lbs') + '</span>' +
        '<button class="row-btn lg-del">' + X_SVG + '</button></div>';
    }).join('') : '<p class="hint">Todavía no se ha aprendido ningún QR antiguo.</p>';
    lh.querySelectorAll('.lg-del').forEach(function (b) {
      b.addEventListener('click', function () {
        delete legacyMap[b.closest('.legacy-row').dataset.k];
        saveLegacy(); renderSettings();
      });
    });

    // reglas de caja
    renderBoxRules();

    // tienda
    $('store-url').value = settings.storeUrl || '';

    // sincronización
    $('sync-enabled').checked = !!settings.sync.enabled;
    $('sync-url').value = settings.sync.url || '';
    $('sync-secret').value = settings.sync.secret || '';
    renderSyncStatus();

    // toggles
    $('set-sound').checked = settings.sound;
    $('set-vibrate').checked = settings.vibrate;
    $('set-ocr').checked = settings.ocr !== false;
    $('set-cooldown').value = settings.cooldownMs;
    $('cooldown-val').textContent = settings.cooldownMs + ' ms';
  }

  function renderSyncStatus() {
    if (!window.BCSync) return;
    var st = BCSync.status();
    var parts = [];
    if (!settings.sync.enabled) parts.push('Sincronización apagada.');
    else {
      parts.push(st.pending ? st.pending + ' eventos en cola.' : 'Cola vacía — todo enviado.');
      if (st.lastError) parts.push('Último error: ' + st.lastError);
    }
    $('sync-status').textContent = parts.join(' ');
  }

  function renderBoxRules() {
    var host = $('box-rules');
    host.innerHTML = settings.boxRules.map(function (r, i) {
      return '<div class="rule-row" data-i="' + i + '">' +
        '<span class="hint">hasta</span>' +
        '<input type="number" class="rule-max" value="' + r.maxLbs + '" min="0.5" step="0.5"><span class="hint">lb →</span>' +
        '<input type="text" class="rule-box" value="' + esc(r.box) + '">' +
        '<button class="row-btn rule-del">' + X_SVG + '</button></div>';
    }).join('');
    host.querySelectorAll('.rule-row').forEach(function (row) {
      var i = parseInt(row.dataset.i, 10);
      row.querySelector('.rule-max').addEventListener('change', function () {
        settings.boxRules[i].maxLbs = parseFloat(this.value) || settings.boxRules[i].maxLbs;
        saveSettings();
      });
      row.querySelector('.rule-box').addEventListener('change', function () {
        settings.boxRules[i].box = this.value;
        saveSettings();
      });
      row.querySelector('.rule-del').addEventListener('click', function () {
        settings.boxRules.splice(i, 1); saveSettings(); renderBoxRules();
      });
    });
  }
  $('btn-add-rule').addEventListener('click', function () {
    settings.boxRules.push({ maxLbs: 10, box: 'Caja' });
    saveSettings(); renderBoxRules();
  });

  $('btn-add-coffee').addEventListener('click', function () {
    var name = $('new-coffee-name').value.trim();
    if (!name) return;
    var sku = E.slug(name);
    if (catalog.some(function (c) { return c.sku === sku; })) { toast('Ya existe ese café.'); return; }
    catalog.push({ sku: sku, name: name, aliases: [] });
    saveCatalog();
    $('new-coffee-name').value = '';
    renderSettings();
    toast(name + ' agregado ✔');
  });

  $('set-sound').addEventListener('change', function () { settings.sound = this.checked; saveSettings(); });
  $('set-vibrate').addEventListener('change', function () { settings.vibrate = this.checked; saveSettings(); });
  $('set-ocr').addEventListener('change', function () { settings.ocr = this.checked; saveSettings(); });
  $('set-cooldown').addEventListener('input', function () {
    settings.cooldownMs = parseInt(this.value, 10);
    $('cooldown-val').textContent = settings.cooldownMs + ' ms';
    saveSettings();
  });

  // sincronización
  $('sync-enabled').addEventListener('change', function () {
    settings.sync.enabled = this.checked; saveSettings(); renderSyncStatus();
  });
  $('sync-url').addEventListener('change', function () {
    settings.sync.url = this.value.trim(); saveSettings(); renderSyncStatus();
  });
  $('sync-secret').addEventListener('change', function () {
    settings.sync.secret = this.value.trim(); saveSettings();
  });
  $('btn-sync-test').addEventListener('click', function () {
    settings.sync.url = $('sync-url').value.trim();
    saveSettings();
    if (!window.BCSync) return;
    BCSync.test().then(function () {
      toast('✔ Conexión OK — llegó al webhook');
    }).catch(function (err) {
      toast('No se pudo: ' + (err && err.message ? err.message : err), 3200);
    });
  });
  $('btn-sync-flush').addEventListener('click', function () {
    if (window.BCSync) BCSync.flush().then(renderSyncStatus);
  });
  if (window.BCSync) BCSync.onChange(function () {
    if (currentView === 'settings') renderSyncStatus();
  });

  // datos y respaldo
  $('btn-backup').addEventListener('click', function () {
    var data = {};
    DB.KEYS.forEach(function (k) { data[k] = DB.get(k, null); });
    data._exportedAt = new Date().toISOString();
    download('burman-respaldo-' + new Date().toISOString().slice(0, 10) + '.json',
      JSON.stringify(data, null, 2), 'application/json');
  });
  $('backup-file').addEventListener('change', function () {
    var f = this.files[0];
    if (!f) return;
    var reader = new FileReader();
    reader.onload = function () {
      try {
        var data = JSON.parse(String(reader.result));
        if (!data.catalog && !data.scans) throw new Error('formato');
        DB.KEYS.forEach(function (k) { if (data[k] != null) DB.set(k, data[k]); });
        toast('Respaldo importado. Recargando…');
        setTimeout(function () { location.reload(); }, 800);
      } catch (e) { toast('Ese archivo no parece un respaldo válido.'); }
    };
    reader.readAsText(f);
    this.value = '';
  });
  $('btn-wipe').addEventListener('click', function () {
    if (!confirm('Esto borra TODO: catálogo, órdenes, escaneos, mapeos. ¿Seguro?')) return;
    if (!confirm('Última confirmación: ¿borrar todos los datos?')) return;
    DB.KEYS.forEach(function (k) { localStorage.removeItem('bc.' + k); });
    localStorage.removeItem('bc.syncQueue');
    location.reload();
  });

  // ================= arranque =================

  saveCatalog(); // asegura semilla inicial
  renderScanView();
  renderLabelCoffees();
  updateCamera();
  if (window.BCSync) BCSync.start();

  if ('serviceWorker' in navigator &&
      (location.protocol === 'https:' || location.hostname === 'localhost' || location.hostname === '127.0.0.1')) {
    navigator.serviceWorker.register('sw.js').catch(function () {});
  }

  // exponer para pruebas de integración
  window.BCApp = {
    handlePayload: handlePayload,
    lookupDecode: lookupDecode,
    startOrder: startOrder,
    startFree: startFree,
    exitScan: exitScan,
    showView: showView,
    getState: function () { return { orders: orders, scans: scans, catalog: catalog, session: scanSession, settings: settings }; }
  };
})();
