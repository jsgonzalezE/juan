/*
 * Burman Inventario — motor de lógica (funciones puras, sin DOM).
 * Se carga en el navegador como window.BCEngine y en Node para las pruebas.
 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.BCEngine = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  // ---------------- utilidades de texto ----------------

  function norm(s) {
    return String(s == null ? '' : s)
      .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
      .toLowerCase().replace(/\s+/g, ' ').trim();
  }

  function slug(s) {
    var out = norm(s).toUpperCase().replace(/[^A-Z0-9]+/g, '-').replace(/^-+|-+$/g, '');
    return (out || 'CAFE').slice(0, 24);
  }

  function num(s) {
    var v = parseFloat(String(s).replace(',', '.'));
    return isNaN(v) ? null : v;
  }

  // acepta "2", "2.5", "2,5" y fracciones "1/2"
  function parseLbs(s) {
    var frac = /^(\d+)\s*\/\s*(\d+)$/.exec(String(s).trim());
    if (frac) {
      var d = parseInt(frac[2], 10);
      return d ? round2(parseInt(frac[1], 10) / d) : null;
    }
    return num(s);
  }

  function round2(v) { return Math.round(v * 100) / 100; }

  function fmtLbs(v) {
    var r = round2(v);
    return (r % 1 === 0) ? String(r) : r.toFixed(2).replace(/0$/, '');
  }

  // ---------------- formato QR de etiquetas ----------------
  // Etiqueta nueva: "BC|SKU|LBS"  (ej. "BC|COLOMBIA|2")
  // El peso viaja dentro del QR: el escáner no necesita leer el número impreso.

  function makeQRPayload(sku, lbs) {
    return 'BC|' + slug(sku) + '|' + fmtLbs(lbs);
  }

  function parseQR(text) {
    var m = /^\s*BC\s*[|:;]\s*([A-Za-z0-9 _.\-]+?)\s*[|:;]\s*(\d+(?:[.,]\d+)?|\d+\s*\/\s*\d+)\s*(?:lb|lbs|libras?)?\s*$/i
      .exec(String(text == null ? '' : text));
    if (m) {
      var lbs = parseLbs(m[2]);
      if (lbs && lbs > 0) return { type: 'bc', sku: slug(m[1]), lbs: lbs };
    }
    return { type: 'unknown', raw: String(text == null ? '' : text) };
  }

  // ---------------- catálogo ----------------

  function findCoffee(catalog, text) {
    var t = norm(text);
    if (!t) return null;
    var i, j, c;
    for (i = 0; i < catalog.length; i++) {
      c = catalog[i];
      if (norm(c.sku) === t || norm(c.name) === t) return c;
    }
    for (i = 0; i < catalog.length; i++) {
      c = catalog[i];
      var al = c.aliases || [];
      for (j = 0; j < al.length; j++) if (norm(al[j]) === t) return c;
    }
    // coincidencia parcial: el nombre más largo contenido gana
    var best = null;
    for (i = 0; i < catalog.length; i++) {
      c = catalog[i];
      var names = [c.name, c.sku].concat(c.aliases || []);
      for (j = 0; j < names.length; j++) {
        var nn = norm(names[j]);
        if (nn.length >= 4 && (t.indexOf(nn) !== -1 || nn.indexOf(t) !== -1)) {
          if (!best || nn.length > best.len) best = { c: c, len: nn.length };
        }
      }
    }
    return best ? best.c : null;
  }

  // ---------------- tamaño (lbs) dentro de un texto ----------------

  function extractSize(text) {
    var s = String(text == null ? '' : text);
    var m = /(\d+\s*\/\s*\d+|\d+(?:[.,]\d+)?)\s*(?:lb|lbs|libras?)\b/i.exec(s);
    if (m) return { lbs: parseLbs(m[1]), match: m[0], index: m.index };
    m = /(\d+(?:[.,]\d+)?)\s*oz\b/i.exec(s);
    if (m) return { lbs: round2(num(m[1]) / 16), match: m[0], index: m.index };
    m = /(\d+(?:[.,]\d+)?)\s*kg\b/i.exec(s);
    if (m) return { lbs: round2(num(m[1]) * 2.20462), match: m[0], index: m.index };
    m = /(\d+(?:[.,]\d+)?)\s*(?:g|gr|gramos)\b/i.exec(s);
    if (m) return { lbs: round2(num(m[1]) / 453.592), match: m[0], index: m.index };
    return null;
  }

  // ---------------- CSV ----------------

  function sniffDelim(line) {
    var cands = [',', ';', '\t'], best = ',', bestN = 0;
    for (var i = 0; i < cands.length; i++) {
      var n = line.split(cands[i]).length - 1;
      if (n > bestN) { bestN = n; best = cands[i]; }
    }
    return best;
  }

  function csvParse(text, delim) {
    var rows = [], row = [], cell = '', inQ = false;
    var s = String(text == null ? '' : text).replace(/^\uFEFF/, '');
    if (!delim) {
      var firstLine = s.split(/\r?\n/)[0] || '';
      delim = sniffDelim(firstLine);
    }
    for (var i = 0; i < s.length; i++) {
      var ch = s[i];
      if (inQ) {
        if (ch === '"') {
          if (s[i + 1] === '"') { cell += '"'; i++; }
          else inQ = false;
        } else cell += ch;
      } else if (ch === '"') {
        inQ = true;
      } else if (ch === delim) {
        row.push(cell); cell = '';
      } else if (ch === '\n' || ch === '\r') {
        if (ch === '\r' && s[i + 1] === '\n') i++;
        row.push(cell); cell = '';
        rows.push(row); row = [];
      } else cell += ch;
    }
    if (cell !== '' || row.length) { row.push(cell); rows.push(row); }
    // descartar filas totalmente vacías
    return rows.filter(function (r) { return r.some(function (c) { return String(c).trim() !== ''; }); });
  }

  function csvStringify(rows) {
    return rows.map(function (r) {
      return r.map(function (c) {
        var v = String(c == null ? '' : c);
        return /[",\n\r;]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v;
      }).join(',');
    }).join('\r\n');
  }

  function findCol(header, keywords) {
    var h = header.map(norm);
    // primero coincidencia exacta, luego "contiene"
    for (var k = 0; k < keywords.length; k++) {
      for (var i = 0; i < h.length; i++) if (h[i] === keywords[k]) return i;
    }
    for (var k2 = 0; k2 < keywords.length; k2++) {
      for (var i2 = 0; i2 < h.length; i2++) if (h[i2] && h[i2].indexOf(keywords[k2]) !== -1) return i2;
    }
    return -1;
  }

  // ---------------- parseo de órdenes (texto libre o CSV) ----------------

  var HEADER_RE = /^(?:orden|order|pedido|po|factura)\s*[:#\-]?\s*#?\s*([A-Za-z0-9][A-Za-z0-9\-_]*)\b\s*(.*)$/i;
  var NUM_HEADER_RE = /^#\s*(\d+)\s*$|^(\d{3,})\s*$/;
  var BOX_RE = /^(?:caja|box)\s*[:\-]?\s*(.+)$/i;
  var NOTE_RE = /^(?:nota|note|notas|comentario)s?\s*[:\-]?\s*(.+)$/i;

  function cleanName(s) {
    return String(s == null ? '' : s)
      .replace(/^(?:de|del)\s+/i, '')
      .replace(/^[\s\-–:,.]+|[\s\-–:,.]+$/g, '')
      .replace(/\s+/g, ' ').trim();
  }

  function parseItemLine(line) {
    var l = String(line).replace(/^[\-*•>]+\s*/, '').trim();
    if (!l) return null;
    var m;
    var NUMF = '(\\d+\\s*\\/\\s*\\d+|\\d+(?:[.,]\\d+)?)';
    // "2x 1lb Colombia" | "2 x 1 lb de Colombia"
    m = new RegExp('^(\\d+)\\s*[x×]\\s*' + NUMF + '\\s*(?:lb|lbs|libras?)\\.?\\s+(?:de\\s+)?(.+)$', 'i').exec(l);
    if (m) return { qty: parseInt(m[1], 10), lbsEach: parseLbs(m[2]), name: cleanName(m[3]) };
    // "2x Colombia 1lb"
    m = new RegExp('^(\\d+)\\s*[x×]\\s*(.+?)\\s+' + NUMF + '\\s*(?:lb|lbs|libras?)\\.?$', 'i').exec(l);
    if (m) return { qty: parseInt(m[1], 10), lbsEach: parseLbs(m[3]), name: cleanName(m[2]) };
    // "2 lb Colombia" | "2lbs de Colombia" | "1/2 lb Etiopia"
    m = new RegExp('^' + NUMF + '\\s*(?:lb|lbs|libras?)\\.?\\s+(?:de\\s+)?(.+)$', 'i').exec(l);
    if (m) return { qty: 1, lbsEach: parseLbs(m[1]), name: cleanName(m[2]) };
    // "Colombia 2lb" | "Colombia - 2 lbs x 3"
    m = new RegExp('^(.+?)\\s*[-–:,]?\\s*' + NUMF + '\\s*(?:lb|lbs|libras?)\\.?(?:\\s*[x×]\\s*(\\d+))?$', 'i').exec(l);
    if (m) return { qty: m[3] ? parseInt(m[3], 10) : 1, lbsEach: parseLbs(m[2]), name: cleanName(m[1]) };
    // "2 Colombia" (número al inicio = libras)
    m = /^(\d+(?:[.,]\d+)?)\s+(?:de\s+)?(.+)$/.exec(l);
    if (m && num(m[1]) <= 50) return { qty: 1, lbsEach: num(m[1]), name: cleanName(m[2]) };
    // "Colombia 2" (número al final = libras)
    m = /^(.+?)\s+(\d+(?:[.,]\d+)?)$/.exec(l);
    if (m && num(m[2]) <= 50) return { qty: 1, lbsEach: num(m[2]), name: cleanName(m[1]) };
    return null;
  }

  function looksLikeOrdersCSV(text) {
    var first = (String(text).split(/\r?\n/).find(function (l) { return l.trim() !== ''; }) || '');
    var h = norm(first);
    var hasDelim = /[,;\t]/.test(first);
    var hasOrder = /(orden|order|pedido|numero)/.test(h);
    var hasProd = /(cafe|coffee|producto|product|item|articulo|nombre|name)/.test(h);
    return hasDelim && hasOrder && hasProd;
  }

  function parseOrdersCSV(text) {
    var rows = csvParse(text);
    var warnings = [];
    if (rows.length < 2) return { orders: [], warnings: ['El CSV no tiene filas de datos.'] };
    var header = rows[0];
    var cOrder = findCol(header, ['orden', 'order id', 'order_id', 'order number', 'numero de pedido', 'order', 'pedido', 'numero', 'no', 'id']);
    var cProd = findCol(header, ['cafe', 'coffee', 'producto', 'product name', 'item name', 'product', 'item', 'articulo', 'nombre', 'name']);
    var cLbs = findCol(header, ['lbs', 'lb', 'libras', 'peso', 'weight', 'tamano', 'size']);
    var cQty = findCol(header, ['cantidad', 'cant', 'qty', 'quantity', 'unidades']);
    var cBox = findCol(header, ['caja', 'box']);
    var cNote = findCol(header, ['nota', 'note', 'comentario']);
    if (cOrder < 0 || cProd < 0) return { orders: [], warnings: ['No encontré las columnas de orden y producto en el CSV.'] };

    var byId = new Map();
    for (var i = 1; i < rows.length; i++) {
      var r = rows[i];
      var id = String(r[cOrder] == null ? '' : r[cOrder]).trim();
      var prod = String(r[cProd] == null ? '' : r[cProd]).trim();
      if (!id || !prod) { warnings.push('Fila ' + (i + 1) + ' ignorada (sin orden o producto).'); continue; }
      if (!byId.has(id)) byId.set(id, { id: id, items: [], box: null, note: null });
      var o = byId.get(id);
      var qty = cQty >= 0 ? (parseInt(r[cQty], 10) || 1) : 1;
      var lbs = cLbs >= 0 ? parseLbs(r[cLbs]) : null;
      var name = prod;
      if (lbs == null) {
        var sz = extractSize(prod);
        if (sz) {
          lbs = sz.lbs;
          name = cleanName(prod.slice(0, sz.index) + ' ' + prod.slice(sz.index + sz.match.length));
        }
      }
      if (lbs == null || !(lbs > 0)) { warnings.push('Fila ' + (i + 1) + ': no pude leer las libras de "' + prod + '".'); continue; }
      o.items.push({ name: name || prod, lbsEach: lbs, qty: qty });
      if (cBox >= 0 && r[cBox] && String(r[cBox]).trim()) o.box = String(r[cBox]).trim();
      if (cNote >= 0 && r[cNote] && String(r[cNote]).trim()) o.note = String(r[cNote]).trim();
    }
    return { orders: Array.from(byId.values()), warnings: warnings };
  }

  function parseOrdersLines(text) {
    var lines = String(text == null ? '' : text).split(/\r?\n/);
    var orders = [], warnings = [], current = null;
    function push() { if (current && current.items.length) orders.push(current); else if (current) warnings.push('La orden ' + current.id + ' no tiene artículos.'); }
    for (var i = 0; i < lines.length; i++) {
      var line = lines[i].trim();
      if (!line) continue;
      var m = BOX_RE.exec(line);
      if (m && current) { current.box = m[1].trim(); continue; }
      m = NOTE_RE.exec(line);
      if (m && current) { current.note = (current.note ? current.note + ' · ' : '') + m[1].trim(); continue; }
      m = HEADER_RE.exec(line);
      if (m) {
        push();
        current = { id: m[1], items: [], box: null, note: (m[2] || '').replace(/^[\s\-–:,]+/, '').trim() || null };
        continue;
      }
      m = NUM_HEADER_RE.exec(line);
      if (m) {
        push();
        current = { id: m[1] || m[2], items: [], box: null, note: null };
        continue;
      }
      var item = parseItemLine(line);
      if (item && item.lbsEach > 0 && item.name) {
        if (!current) { current = { id: 'S/N', items: [], box: null, note: null }; }
        current.items.push(item);
      } else {
        warnings.push('Línea ' + (i + 1) + ' ignorada: "' + line + '"');
      }
    }
    push();
    return { orders: orders, warnings: warnings };
  }

  /**
   * Analiza el texto de órdenes (formato libre o CSV) y resuelve cafés
   * contra el catálogo. Los cafés que no existen se proponen como nuevos.
   */
  function parseOrdersText(text, catalog) {
    var base = looksLikeOrdersCSV(text) ? parseOrdersCSV(text) : parseOrdersLines(text);
    var newCoffees = [], newBySku = new Map();
    for (var i = 0; i < base.orders.length; i++) {
      var o = base.orders[i];
      for (var j = 0; j < o.items.length; j++) {
        var it = o.items[j];
        var c = findCoffee(catalog, it.name);
        if (!c && newBySku.size) {
          // también contra los nuevos ya propuestos en este mismo archivo
          c = findCoffee(Array.from(newBySku.values()), it.name);
        }
        if (c) {
          it.sku = c.sku; it.name = c.name; it.matched = true;
        } else {
          var sku = slug(it.name);
          it.sku = sku; it.matched = false;
          if (!newBySku.has(sku)) {
            var nc = { sku: sku, name: it.name, aliases: [] };
            newBySku.set(sku, nc); newCoffees.push(nc);
          } else {
            it.name = newBySku.get(sku).name;
          }
        }
        it.totalLbs = round2(it.lbsEach * it.qty);
      }
    }
    return { orders: base.orders, warnings: base.warnings, newCoffees: newCoffees };
  }

  // ---------------- trabajo de empaque ----------------

  function buildJob(order) {
    var map = new Map();
    for (var i = 0; i < order.items.length; i++) {
      var it = order.items[i];
      if (!map.has(it.sku)) map.set(it.sku, { sku: it.sku, name: it.name, needLbs: 0, doneLbs: 0, bags: [] });
      var l = map.get(it.sku);
      l.needLbs = round2(l.needLbs + it.lbsEach * it.qty);
    }
    return {
      orderId: order.id,
      box: order.box || null,
      note: order.note || null,
      lines: Array.from(map.values()),
      startedAt: null,
      completedAt: null
    };
  }

  var EPS = 1e-9;

  /**
   * Aplica un escaneo (sku + lbs de la bolsa) al trabajo.
   * Estados: ok | line-complete | order-complete | not-in-order | line-full | overfill
   * Las bolsas de 1 y 2 lb se mezclan libremente: solo cuentan las libras.
   */
  function applyScan(job, sku, lbs, ts) {
    var line = null;
    for (var i = 0; i < job.lines.length; i++) if (job.lines[i].sku === sku) { line = job.lines[i]; break; }
    if (!line) return { status: 'not-in-order' };
    var remaining = round2(line.needLbs - line.doneLbs);
    if (remaining <= EPS) return { status: 'line-full', line: line, remaining: 0 };
    if (lbs > remaining + EPS) return { status: 'overfill', line: line, remaining: remaining };
    line.doneLbs = round2(line.doneLbs + lbs);
    line.bags.push({ lbs: lbs, ts: ts || 0 });
    var orderDone = job.lines.every(function (l) { return l.doneLbs >= l.needLbs - EPS; });
    var lineDone = line.doneLbs >= line.needLbs - EPS;
    return {
      status: orderDone ? 'order-complete' : (lineDone ? 'line-complete' : 'ok'),
      line: line,
      remaining: round2(line.needLbs - line.doneLbs)
    };
  }

  /** Quita la última bolsa registrada con ese peso en esa línea (para Deshacer). */
  function removeBag(job, sku, lbs) {
    for (var i = 0; i < job.lines.length; i++) {
      var line = job.lines[i];
      if (line.sku !== sku) continue;
      for (var j = line.bags.length - 1; j >= 0; j--) {
        if (Math.abs(line.bags[j].lbs - lbs) < EPS) {
          line.bags.splice(j, 1);
          line.doneLbs = round2(line.doneLbs - lbs);
          if (line.doneLbs < 0) line.doneLbs = 0;
          return true;
        }
      }
    }
    return false;
  }

  function jobTotals(job) {
    var need = 0, done = 0, bags = 0;
    for (var i = 0; i < job.lines.length; i++) {
      need += job.lines[i].needLbs; done += job.lines[i].doneLbs; bags += job.lines[i].bags.length;
    }
    return { needLbs: round2(need), doneLbs: round2(done), bags: bags };
  }

  function suggestBox(totalLbs, rules, override) {
    if (override) return override;
    if (!rules || !rules.length) return null;
    var sorted = rules.slice().sort(function (a, b) { return a.maxLbs - b.maxLbs; });
    for (var i = 0; i < sorted.length; i++) {
      if (totalLbs <= sorted[i].maxLbs + EPS) return sorted[i].box;
    }
    return sorted[sorted.length - 1].box;
  }

  // ---------------- resumen de escaneos ----------------

  /** scans: [{ts, sku, lbs, orderId, source}] — resumen por café con desglose por tamaño de bolsa. */
  function summarizeScans(scans, fromTs, toTs) {
    var per = new Map();
    var totalLbs = 0, totalBags = 0;
    var orders = new Set();
    for (var i = 0; i < scans.length; i++) {
      var s = scans[i];
      if (s.ts < fromTs || s.ts >= toTs) continue;
      if (!per.has(s.sku)) per.set(s.sku, { sku: s.sku, totalLbs: 0, bags: 0, sizes: {} });
      var p = per.get(s.sku);
      p.totalLbs = round2(p.totalLbs + s.lbs);
      p.bags++;
      var key = fmtLbs(s.lbs);
      p.sizes[key] = (p.sizes[key] || 0) + 1;
      totalLbs = round2(totalLbs + s.lbs);
      totalBags++;
      if (s.orderId) orders.add(s.orderId);
    }
    var list = Array.from(per.values()).sort(function (a, b) { return b.totalLbs - a.totalLbs; });
    return { perSku: list, totalLbs: totalLbs, totalBags: totalBags, orderCount: orders.size };
  }

  // ---------------- WooCommerce ----------------

  function parseWooCSV(text) {
    var rows = csvParse(text);
    var warnings = [];
    if (rows.length < 2) return { items: [], warnings: ['El CSV no tiene filas de datos.'] };
    var header = rows[0];
    var cProd = findCol(header, ['item name', 'product name', 'nombre del producto', 'producto', 'product', 'item', 'nombre del articulo', 'lineitem name']);
    var cQty = findCol(header, ['quantity', 'qty', 'cantidad', 'item quantity', 'lineitem quantity']);
    var cOrder = findCol(header, ['order id', 'order number', 'numero de pedido', 'pedido', 'orden', 'order']);
    var cDate = findCol(header, ['order date', 'paid date', 'completed date', 'fecha', 'date']);
    var cItems = findCol(header, ['line items', 'items', 'products', 'productos', 'articulos']);
    var cImg = findCol(header, ['image url', 'imagen', 'image', 'thumbnail', 'foto']);

    var items = [];
    function add(product, qty, orderId, dateStr, image) {
      product = String(product == null ? '' : product).trim();
      if (!product) return;
      items.push({
        product: product, qty: qty > 0 ? qty : 1,
        orderId: orderId || null, dateStr: dateStr || null, image: image || null
      });
    }

    for (var i = 1; i < rows.length; i++) {
      var r = rows[i];
      var orderId = cOrder >= 0 ? String(r[cOrder] == null ? '' : r[cOrder]).trim() : null;
      var dateStr = cDate >= 0 ? String(r[cDate] == null ? '' : r[cDate]).trim() : null;
      var image = cImg >= 0 ? String(r[cImg] == null ? '' : r[cImg]).trim() : null;
      if (cProd >= 0) {
        var qty = cQty >= 0 ? (parseFloat(r[cQty]) || 1) : 1;
        add(r[cProd], qty, orderId, dateStr, image);
      } else if (cItems >= 0) {
        // celda agregada: "2 x Colombia 2lb | Brasil 1lb x 3" (separadores | ; o salto de línea)
        var cell = String(r[cItems] == null ? '' : r[cItems]);
        var parts = cell.split(/[|;\n]+/);
        if (parts.length === 1) parts = cell.split(/,(?=\s*\d+\s*[x×])/);
        for (var p = 0; p < parts.length; p++) {
          var e = parts[p].trim();
          if (!e) continue;
          var m = /^(\d+)\s*[x×]\s*(.+)$/.exec(e);
          if (m) { add(m[2], parseInt(m[1], 10), orderId, dateStr); continue; }
          m = /^(.+?)\s*[x×]\s*(\d+)$/.exec(e);
          if (m) { add(m[1], parseInt(m[2], 10), orderId, dateStr); continue; }
          add(e, 1, orderId, dateStr);
        }
      } else {
        return { items: [], warnings: ['No encontré la columna de producto en el CSV de WooCommerce.'] };
      }
    }
    if (!items.length) warnings.push('No se encontraron artículos en el archivo.');
    return { items: items, warnings: warnings };
  }

  function cleanProductName(s) {
    return cleanName(String(s == null ? '' : s)
      .replace(/\((?:[^)]*)\)/g, ' ')
      .replace(/\b(whole bean|ground|grano entero|molido|coffee|cafe|café)\b/gi, ' ')
      .replace(/\s+/g, ' '));
  }

  /**
   * Agrega los renglones de Woo por café usando el mapa aprendido (wooMap).
   * Devuelve totales por sku, mapeos automáticos nuevos y productos sin resolver.
   */
  function aggregateWoo(items, catalog, wooMap) {
    wooMap = wooMap || {};
    var perSku = new Map();
    var autoMapped = {};
    var unmatched = new Map();

    function addTo(sku, lbsEach, qty) {
      if (!perSku.has(sku)) perSku.set(sku, { sku: sku, totalLbs: 0, bags: 0, sizes: {} });
      var p = perSku.get(sku);
      p.totalLbs = round2(p.totalLbs + lbsEach * qty);
      p.bags += qty;
      var key = fmtLbs(lbsEach);
      p.sizes[key] = (p.sizes[key] || 0) + qty;
    }

    for (var i = 0; i < items.length; i++) {
      var it = items[i];
      var key = norm(it.product);
      var mapping = wooMap[key] || autoMapped[key];
      if (mapping) { addTo(mapping.sku, mapping.lbsEach, it.qty); continue; }
      var size = extractSize(it.product);
      var namePart = size
        ? it.product.slice(0, size.index) + ' ' + it.product.slice(size.index + size.match.length)
        : it.product;
      var c = findCoffee(catalog, cleanProductName(namePart));
      if (c && size && size.lbs > 0) {
        autoMapped[key] = { sku: c.sku, lbsEach: size.lbs };
        addTo(c.sku, size.lbs, it.qty);
      } else {
        if (!unmatched.has(key)) {
          unmatched.set(key, {
            product: it.product, qty: 0,
            guessSku: c ? c.sku : null,
            guessLbs: size && size.lbs > 0 ? size.lbs : null
          });
        }
        unmatched.get(key).qty += it.qty;
      }
    }
    return {
      perSku: Array.from(perSku.values()).sort(function (a, b) { return b.totalLbs - a.totalLbs; }),
      autoMapped: autoMapped,
      unmatched: Array.from(unmatched.values())
    };
  }

  /** Comparación fin de mes: escaneado vs WooCommerce. */
  function compareTotals(scanPer, wooPer) {
    var map = new Map();
    function row(sku) {
      if (!map.has(sku)) map.set(sku, { sku: sku, scanLbs: 0, wooLbs: 0 });
      return map.get(sku);
    }
    (scanPer || []).forEach(function (p) { row(p.sku).scanLbs = p.totalLbs; });
    (wooPer || []).forEach(function (p) { row(p.sku).wooLbs = p.totalLbs; });
    var rows = Array.from(map.values());
    rows.forEach(function (r) { r.diff = round2(r.scanLbs - r.wooLbs); });
    rows.sort(function (a, b) { return Math.abs(b.diff) - Math.abs(a.diff) || b.scanLbs - a.scanLbs; });
    return rows;
  }

  // ---------------- fechas ----------------

  function monthKey(ts) {
    var d = new Date(ts);
    return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0');
  }

  function dayRange(now) {
    var d = new Date(now); d.setHours(0, 0, 0, 0);
    return { from: d.getTime(), to: d.getTime() + 86400000 };
  }

  function monthRange(now, offset) {
    var d = new Date(now);
    var from = new Date(d.getFullYear(), d.getMonth() + (offset || 0), 1);
    var to = new Date(d.getFullYear(), d.getMonth() + (offset || 0) + 1, 1);
    return { from: from.getTime(), to: to.getTime() };
  }

  function parseWooDate(s) {
    if (!s) return null;
    var t = Date.parse(s);
    if (!isNaN(t)) return t;
    var m = /^(\d{1,2})[\/-](\d{1,2})[\/-](\d{2,4})/.exec(String(s).trim());
    if (m) {
      var y = parseInt(m[3], 10); if (y < 100) y += 2000;
      return new Date(y, parseInt(m[1], 10) - 1, parseInt(m[2], 10)).getTime();
    }
    return null;
  }

  return {
    norm: norm, slug: slug, round2: round2, fmtLbs: fmtLbs, parseLbs: parseLbs,
    makeQRPayload: makeQRPayload, parseQR: parseQR,
    findCoffee: findCoffee, extractSize: extractSize,
    csvParse: csvParse, csvStringify: csvStringify,
    parseOrdersText: parseOrdersText, parseItemLine: parseItemLine,
    buildJob: buildJob, applyScan: applyScan, removeBag: removeBag,
    jobTotals: jobTotals, suggestBox: suggestBox,
    summarizeScans: summarizeScans,
    parseWooCSV: parseWooCSV, aggregateWoo: aggregateWoo, compareTotals: compareTotals,
    cleanProductName: cleanProductName,
    monthKey: monthKey, dayRange: dayRange, monthRange: monthRange, parseWooDate: parseWooDate
  };
});
