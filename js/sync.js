/*
 * Sincronización con el CRM vía webhook.
 * Cada evento (bolsa escaneada, orden completada, resumen) se encola y se envía
 * como POST JSON al endpoint configurado en Ajustes. La cola sobrevive reinicios
 * y reintenta con espera creciente si no hay señal o el servidor falla.
 * Compatible con Zapier / Make / n8n / endpoint propio del CRM.
 */
(function (root) {
  'use strict';

  var QKEY = 'bc.syncQueue';
  var MAX_QUEUE = 800;
  var timer = null;
  var sending = false;
  var listeners = [];

  function loadQueue() {
    try { return JSON.parse(localStorage.getItem(QKEY)) || []; } catch (e) { return []; }
  }
  function saveQueue(q) { localStorage.setItem(QKEY, JSON.stringify(q)); }

  function getConfig() {
    try {
      var s = JSON.parse(localStorage.getItem('bc.settings')) || {};
      return s.sync || {};
    } catch (e) { return {}; }
  }

  function notify() {
    var st = status();
    listeners.forEach(function (fn) { try { fn(st); } catch (e) {} });
  }

  function status() {
    var q = loadQueue();
    return { pending: q.length, lastError: status._lastError || null, lastSentAt: status._lastSentAt || null };
  }

  /** Encola un evento. type: 'scan' | 'order' | 'summary' | 'test' */
  function push(type, payload) {
    var cfg = getConfig();
    if (!cfg.enabled || !cfg.url) return false;
    var q = loadQueue();
    q.push({
      id: Date.now() + '-' + Math.random().toString(36).slice(2, 8),
      type: type,
      payload: payload,
      queuedAt: new Date().toISOString(),
      tries: 0,
      nextAt: 0
    });
    if (q.length > MAX_QUEUE) q = q.slice(q.length - MAX_QUEUE);
    saveQueue(q);
    notify();
    kick();
    return true;
  }

  function backoffMs(tries) {
    return Math.min(30000 * Math.pow(2, Math.max(0, tries - 1)), 3600000);
  }

  function sendOne(cfg, item) {
    var body = JSON.stringify({
      source: 'burman-inventario',
      event: item.type,
      id: item.id,
      queuedAt: item.queuedAt,
      sentAt: new Date().toISOString(),
      data: item.payload
    });
    var headers = { 'Content-Type': 'application/json' };
    if (cfg.secret) headers['X-Burman-Key'] = cfg.secret;
    return fetch(cfg.url, { method: 'POST', headers: headers, body: body, mode: 'cors' })
      .then(function (res) {
        if (!res.ok) throw new Error('HTTP ' + res.status);
        return true;
      })
      .catch(function (err) {
        // si el endpoint no maneja CORS, entregar en modo opaco (sin confirmación)
        if (err instanceof TypeError) {
          return fetch(cfg.url, {
            method: 'POST',
            headers: { 'Content-Type': 'text/plain' },
            body: body,
            mode: 'no-cors'
          }).then(function () { return true; });
        }
        throw err;
      });
  }

  function flush() {
    if (sending) return Promise.resolve();
    var cfg = getConfig();
    if (!cfg.enabled || !cfg.url) return Promise.resolve();
    var q = loadQueue();
    var now = Date.now();
    var ready = q.filter(function (it) { return it.nextAt <= now; });
    if (!ready.length) return Promise.resolve();
    sending = true;
    var chain = Promise.resolve();
    ready.slice(0, 20).forEach(function (item) {
      chain = chain.then(function () {
        return sendOne(cfg, item).then(function () {
          var cur = loadQueue().filter(function (it) { return it.id !== item.id; });
          saveQueue(cur);
          status._lastSentAt = Date.now();
          status._lastError = null;
        }).catch(function (err) {
          var cur = loadQueue();
          for (var i = 0; i < cur.length; i++) {
            if (cur[i].id === item.id) {
              cur[i].tries++;
              cur[i].nextAt = Date.now() + backoffMs(cur[i].tries);
            }
          }
          saveQueue(cur);
          status._lastError = String(err && err.message ? err.message : err);
        });
      });
    });
    return chain.then(function () { sending = false; notify(); },
      function () { sending = false; notify(); });
  }

  function kick() {
    setTimeout(function () { flush(); }, 50);
  }

  function start() {
    if (timer) return;
    timer = setInterval(flush, 15000);
    root.addEventListener('online', kick);
    kick();
  }

  /** Envía un evento de prueba de inmediato (para el botón "Probar" en Ajustes). */
  function test() {
    var cfg = getConfig();
    if (!cfg.url) return Promise.reject(new Error('Configura la URL primero.'));
    return sendOne(cfg, {
      id: 'test-' + Date.now(),
      type: 'test',
      queuedAt: new Date().toISOString(),
      payload: { message: 'Hola desde Burman Inventario 👋' }
    });
  }

  function onChange(fn) { listeners.push(fn); }

  root.BCSync = { push: push, flush: flush, start: start, test: test, status: status, onChange: onChange };
})(typeof window !== 'undefined' ? window : this);
