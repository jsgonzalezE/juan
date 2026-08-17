#!/usr/bin/env node
/*
 * Servidor local de Burman Inventario para la red de la bodega.
 * Sin dependencias: solo Node.js.
 *
 *   node server/serve.js
 *
 * - Si existen server/certs/cert.pem y key.pem → sirve HTTPS en el puerto 8443
 *   (necesario para que la cámara funcione en los teléfonos) y además HTTP en
 *   8080 que redirige a HTTPS.
 * - Si no hay certificados → sirve solo HTTP en 8080 (la cámara NO funcionará
 *   desde los teléfonos; ver server/INSTALACION.md para generar el certificado).
 */
'use strict';
const http = require('http');
const https = require('https');
const fs = require('fs');
const path = require('path');
const os = require('os');

const ROOT = path.resolve(__dirname, '..');
const CERT = path.join(__dirname, 'certs', 'cert.pem');
const KEY = path.join(__dirname, 'certs', 'key.pem');
const HTTP_PORT = parseInt(process.env.PUERTO_HTTP || '8080', 10);
const HTTPS_PORT = parseInt(process.env.PUERTO_HTTPS || '8443', 10);

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.webmanifest': 'application/manifest+json',
  '.json': 'application/json',
  '.txt': 'text/plain; charset=utf-8',
  '.gz': 'application/gzip',
  '.wasm': 'application/wasm',
  '.ico': 'image/x-icon',
  '.crt': 'application/x-x509-ca-cert',
  '.pem': 'application/x-pem-file'
};

function handler(req, res) {
  try {
    let p = decodeURIComponent((req.url || '/').split('?')[0]);
    if (p === '/') p = '/index.html';
    // el certificado de la CA se sirve para poder instalarlo fácil en los teléfonos
    if (p === '/burman-ca.crt') {
      const ca = path.join(__dirname, 'certs', 'burman-ca.crt');
      if (fs.existsSync(ca)) {
        res.writeHead(200, { 'Content-Type': 'application/x-x509-ca-cert' });
        res.end(fs.readFileSync(ca));
        return;
      }
    }
    const file = path.join(ROOT, p);
    if (!file.startsWith(ROOT) || file.includes(path.sep + 'server' + path.sep + 'certs')) {
      res.writeHead(403); res.end('No'); return;
    }
    if (!fs.existsSync(file) || fs.statSync(file).isDirectory()) {
      res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
      res.end('No encontrado'); return;
    }
    res.writeHead(200, {
      'Content-Type': MIME[path.extname(file).toLowerCase()] || 'application/octet-stream',
      'Cache-Control': 'no-cache'
    });
    fs.createReadStream(file).pipe(res);
  } catch (e) {
    res.writeHead(500); res.end('Error');
  }
}

function lanIPs() {
  const out = [];
  const ifaces = os.networkInterfaces();
  for (const name of Object.keys(ifaces)) {
    for (const inf of ifaces[name] || []) {
      if (inf.family === 'IPv4' && !inf.internal) out.push(inf.address);
    }
  }
  return out.length ? out : ['localhost'];
}

const hasCerts = fs.existsSync(CERT) && fs.existsSync(KEY);
const ips = lanIPs();

console.log('');
console.log('  ☕ Burman Inventario — servidor local');
console.log('  ────────────────────────────────────');

function onPortBusy(port, fatal) {
  return function (err) {
    if (err && err.code === 'EADDRINUSE') {
      console.log('');
      console.log('  ✘ El puerto ' + port + ' ya está en uso.');
      console.log('    ¿Ya hay otra ventana del servidor abierta? Ciérrala y vuelve a intentar,');
      console.log('    o usa otro puerto: PUERTO_HTTP=8081 PUERTO_HTTPS=8444 node server/serve.js');
      if (fatal) process.exit(1);
    } else {
      console.log('  ✘ Error del servidor: ' + (err && err.message ? err.message : err));
      if (fatal) process.exit(1);
    }
  };
}

if (hasCerts) {
  https.createServer({ cert: fs.readFileSync(CERT), key: fs.readFileSync(KEY) }, handler)
    .on('error', onPortBusy(HTTPS_PORT, true))
    .listen(HTTPS_PORT, '0.0.0.0', () => {
      console.log('  ✔ HTTPS activo (la cámara funciona):');
      ips.forEach(ip => console.log('      https://' + ip + ':' + HTTPS_PORT + '/'));
      console.log('');
      console.log('  Certificado para los teléfonos (instalar una vez):');
      ips.forEach(ip => console.log('      http://' + ip + ':' + HTTP_PORT + '/burman-ca.crt'));
    });
  // HTTP redirige a HTTPS (y sirve el certificado de la CA sin redirigir);
  // si su puerto está ocupado, HTTPS sigue funcionando igual
  http.createServer((req, res) => {
    if ((req.url || '').startsWith('/burman-ca.crt')) { handler(req, res); return; }
    const host = String(req.headers.host || ips[0]).split(':')[0];
    res.writeHead(302, { Location: 'https://' + host + ':' + HTTPS_PORT + (req.url || '/') });
    res.end();
  }).on('error', onPortBusy(HTTP_PORT, false)).listen(HTTP_PORT, '0.0.0.0');
} else {
  http.createServer(handler)
    .on('error', onPortBusy(HTTP_PORT, true))
    .listen(HTTP_PORT, '0.0.0.0', () => {
      console.log('  ✔ HTTP activo en:');
      ips.forEach(ip => console.log('      http://' + ip + ':' + HTTP_PORT + '/'));
      console.log('');
      console.log('  ⚠ SIN certificado: la cámara NO funcionará desde los teléfonos.');
      console.log('    Genera uno con server/generar-certificado.sh (ver server/INSTALACION.md).');
    });
}
console.log('');
console.log('  Deja esta ventana abierta. Ctrl+C para detener.');
console.log('');
