/* Pruebas del motor. Ejecutar con: node tests/engine.test.js */
'use strict';
const E = require('../js/engine.js');

let pass = 0, fail = 0;
function eq(actual, expected, msg) {
  const a = JSON.stringify(actual), b = JSON.stringify(expected);
  if (a === b) { pass++; }
  else { fail++; console.error('FALLO: ' + msg + '\n  esperado: ' + b + '\n  recibido: ' + a); }
}
function ok(cond, msg) {
  if (cond) pass++;
  else { fail++; console.error('FALLO: ' + msg); }
}

const CATALOG = [
  { sku: 'COLOMBIA', name: 'Colombia', aliases: ['colombian supremo'] },
  { sku: 'BRASIL', name: 'Brasil', aliases: ['brazil'] },
  { sku: 'PERU', name: 'Perú', aliases: [] },
  { sku: 'ETIOPIA', name: 'Etiopía', aliases: ['ethiopia'] },
  { sku: 'GUATEMALA', name: 'Guatemala', aliases: [] },
  { sku: 'COSTA-RICA', name: 'Costa Rica', aliases: [] }
];

// ---------- QR ----------
eq(E.parseQR('BC|COLOMBIA|2'), { type: 'bc', sku: 'COLOMBIA', lbs: 2 }, 'QR básico');
eq(E.parseQR('bc|peru|5'), { type: 'bc', sku: 'PERU', lbs: 5 }, 'QR minúsculas');
eq(E.parseQR(' BC | COSTA-RICA | 2.5 lb '), { type: 'bc', sku: 'COSTA-RICA', lbs: 2.5 }, 'QR con espacios y unidad');
eq(E.parseQR('BC:ETIOPIA:1/2'), { type: 'bc', sku: 'ETIOPIA', lbs: 0.5 }, 'QR con dos puntos y fracción');
eq(E.parseQR('https://burmancoffee.com/product/colombia').type, 'unknown', 'QR viejo = unknown');
eq(E.parseQR('').type, 'unknown', 'QR vacío');
eq(E.parseQR(E.makeQRPayload('Colombia', 2)), { type: 'bc', sku: 'COLOMBIA', lbs: 2 }, 'ida y vuelta payload');

// ---------- catálogo ----------
ok(E.findCoffee(CATALOG, 'perú').sku === 'PERU', 'acentos ignorados');
ok(E.findCoffee(CATALOG, 'Brazil').sku === 'BRASIL', 'alias');
ok(E.findCoffee(CATALOG, 'Colombian Supremo Whole Bean').sku === 'COLOMBIA', 'parcial por alias');
ok(E.findCoffee(CATALOG, 'costa rica tarrazu').sku === 'COSTA-RICA', 'parcial por nombre');
ok(E.findCoffee(CATALOG, 'Kenia') === null, 'no existe');

// ---------- item lines ----------
eq(E.parseItemLine('2 lb Colombia'), { qty: 1, lbsEach: 2, name: 'Colombia' }, 'item: 2 lb Colombia');
eq(E.parseItemLine('2lbs de Brasil'), { qty: 1, lbsEach: 2, name: 'Brasil' }, 'item: 2lbs de Brasil');
eq(E.parseItemLine('Colombia 2lb'), { qty: 1, lbsEach: 2, name: 'Colombia' }, 'item: Colombia 2lb');
eq(E.parseItemLine('Colombia - 2 lbs x 3'), { qty: 3, lbsEach: 2, name: 'Colombia' }, 'item: nombre - lbs x qty');
eq(E.parseItemLine('2x Guatemala 1lb'), { qty: 2, lbsEach: 1, name: 'Guatemala' }, 'item: 2x Guatemala 1lb');
eq(E.parseItemLine('3 x 1 lb de Peru'), { qty: 3, lbsEach: 1, name: 'Peru' }, 'item: 3 x 1 lb de Peru');
eq(E.parseItemLine('2 Colombia'), { qty: 1, lbsEach: 2, name: 'Colombia' }, 'item: 2 Colombia');
eq(E.parseItemLine('Colombia 2'), { qty: 1, lbsEach: 2, name: 'Colombia' }, 'item: Colombia 2');
eq(E.parseItemLine('1/2 lb Etiopia'), { qty: 1, lbsEach: 0.5, name: 'Etiopia' }, 'item: fracción');
eq(E.parseItemLine('- 5 lb Colombia'), { qty: 1, lbsEach: 5, name: 'Colombia' }, 'item: con viñeta');

// ---------- órdenes texto libre ----------
const TXT = [
  'Orden 1001',
  '2 lb Colombia',
  '2 lb Brasil',
  '2 lb Peru',
  'Caja: Mediana',
  '',
  'Pedido #1002 cliente frecuente',
  '1 lb Etiopia',
  '5 lb Colombia',
  'Nota: entregar temprano',
  '',
  '1003',
  '2x Guatemala 1lb',
  'Kenia 2lb'
].join('\n');

const parsed = E.parseOrdersText(TXT, CATALOG);
eq(parsed.orders.length, 3, 'tres órdenes');
eq(parsed.orders[0].id, '1001', 'id 1001');
eq(parsed.orders[0].box, 'Mediana', 'caja de 1001');
eq(parsed.orders[0].items.length, 3, '1001 tiene 3 items');
ok(parsed.orders[0].items.every(i => i.matched), '1001 todos en catálogo');
eq(parsed.orders[1].id, '1002', 'id 1002');
ok(parsed.orders[1].note && parsed.orders[1].note.includes('entregar temprano'), 'nota de 1002');
eq(parsed.orders[2].id, '1003', 'id numérico solo');
eq(parsed.orders[2].items[0].totalLbs, 2, '2x1lb = 2 lbs totales');
eq(parsed.newCoffees.length, 1, 'Kenia propuesto como café nuevo');
eq(parsed.newCoffees[0].sku, 'KENIA', 'sku generado para Kenia');

// ---------- órdenes CSV ----------
const CSV = [
  'orden,cafe,lbs,cantidad,caja',
  '2001,Colombia,2,1,Chica',
  '2001,Brasil,1,2,Chica',
  '2002,"Etiopía",5,1,'
].join('\n');
const parsedCsv = E.parseOrdersText(CSV, CATALOG);
eq(parsedCsv.orders.length, 2, 'CSV: dos órdenes');
eq(parsedCsv.orders[0].items[1].totalLbs, 2, 'CSV: qty 2 x 1lb');
eq(parsedCsv.orders[0].box, 'Chica', 'CSV: caja');
eq(parsedCsv.orders[1].items[0].sku, 'ETIOPIA', 'CSV: acentos en nombre');

// CSV con lbs dentro del nombre del producto
const CSV2 = [
  'order,product,qty',
  '3001,Colombia Supremo - 2 lb,1',
  '3001,Brasil 1lb,3'
].join('\n');
const parsedCsv2 = E.parseOrdersText(CSV2, CATALOG);
eq(parsedCsv2.orders[0].items[0].lbsEach, 2, 'CSV2: lbs desde nombre');
eq(parsedCsv2.orders[0].items[1].totalLbs, 3, 'CSV2: 3 x 1lb');

// ---------- trabajo de empaque ----------
const job = E.buildJob(parsed.orders[0]); // 2 Colombia, 2 Brasil, 2 Peru
eq(job.lines.length, 3, 'job con 3 líneas');

// mezclar 1+1 para completar 2 lbs
let r = E.applyScan(job, 'COLOMBIA', 1, 1);
eq(r.status, 'ok', 'primera bolsa de 1 lb');
eq(r.remaining, 1, 'falta 1 lb');
r = E.applyScan(job, 'COLOMBIA', 1, 2);
eq(r.status, 'line-complete', '1+1 completa la línea de 2');
r = E.applyScan(job, 'COLOMBIA', 1, 3);
eq(r.status, 'line-full', 'línea llena rechaza más');
r = E.applyScan(job, 'ETIOPIA', 2, 4);
eq(r.status, 'not-in-order', 'café que no está en la orden');
r = E.applyScan(job, 'BRASIL', 5, 5);
eq(r.status, 'overfill', 'bolsa de 5 no cabe en línea de 2');
r = E.applyScan(job, 'BRASIL', 2, 6);
eq(r.status, 'line-complete', 'bolsa exacta de 2');
r = E.applyScan(job, 'PERU', 2, 7);
eq(r.status, 'order-complete', 'última línea completa la orden');
eq(E.jobTotals(job), { needLbs: 6, doneLbs: 6, bags: 4 }, 'totales del job');

// deshacer
ok(E.removeBag(job, 'PERU', 2), 'deshacer quita la bolsa');
eq(job.lines.find(l => l.sku === 'PERU').doneLbs, 0, 'línea Perú vuelve a 0');
ok(!E.removeBag(job, 'PERU', 5), 'no hay bolsa de 5 que quitar');

// ---------- caja sugerida ----------
const RULES = [
  { maxLbs: 2, box: 'Chica' },
  { maxLbs: 6, box: 'Mediana' },
  { maxLbs: 14, box: 'Grande' }
];
eq(E.suggestBox(2, RULES), 'Chica', 'caja chica');
eq(E.suggestBox(6, RULES), 'Mediana', 'caja mediana');
eq(E.suggestBox(30, RULES), 'Grande', 'más que la regla mayor usa la última');
eq(E.suggestBox(4, RULES, 'Especial'), 'Especial', 'override del archivo gana');

// ---------- resumen de escaneos ----------
const scans = [
  { ts: 100, sku: 'COLOMBIA', lbs: 1, orderId: '1001', source: 'scan' },
  { ts: 110, sku: 'COLOMBIA', lbs: 1, orderId: '1001', source: 'scan' },
  { ts: 120, sku: 'COLOMBIA', lbs: 5, orderId: null, source: 'scan' },
  { ts: 130, sku: 'BRASIL', lbs: 2, orderId: '1002', source: 'manual' },
  { ts: 999999, sku: 'PERU', lbs: 2, orderId: null, source: 'scan' }
];
const sum = E.summarizeScans(scans, 0, 1000);
eq(sum.totalLbs, 9, 'resumen: total lbs en rango');
eq(sum.totalBags, 4, 'resumen: total bolsas');
eq(sum.perSku[0].sku, 'COLOMBIA', 'resumen: Colombia primero');
eq(sum.perSku[0].sizes, { '1': 2, '5': 1 }, 'resumen: desglose por tamaño');
eq(sum.orderCount, 2, 'resumen: órdenes tocadas');

// ---------- WooCommerce ----------
const WOO = [
  'Order Number,Order Date,Item Name,Quantity',
  '9001,2026-08-02,Colombia Supremo - 2 lb,2',
  '9002,2026-08-03,Brazil Cerrado 1 lb,1',
  '9003,2026-08-05,Cold Brew Blend 12 oz,1',
  '9004,2026-08-06,"Peru, Organic - 5 lb",1'
].join('\n');
const woo = E.parseWooCSV(WOO);
eq(woo.items.length, 4, 'woo: 4 renglones');
eq(woo.items[3].product, 'Peru, Organic - 5 lb', 'woo: comillas con coma');

const agg = E.aggregateWoo(woo.items, CATALOG, {});
ok(agg.perSku.find(p => p.sku === 'COLOMBIA').totalLbs === 4, 'woo: 2x2lb Colombia');
ok(agg.perSku.find(p => p.sku === 'BRASIL').totalLbs === 1, 'woo: alias Brazil');
ok(agg.perSku.find(p => p.sku === 'PERU').totalLbs === 5, 'woo: Peru 5lb');
eq(agg.unmatched.length, 1, 'woo: Cold Brew sin resolver');
eq(agg.unmatched[0].guessLbs, 0.75, 'woo: 12 oz = 0.75 lb sugerido');

// con mapeo aprendido se resuelve
const agg2 = E.aggregateWoo(woo.items, CATALOG, { [E.norm('Cold Brew Blend 12 oz')]: { sku: 'BRASIL', lbsEach: 0.75 } });
eq(agg2.unmatched.length, 0, 'woo: mapeo aprendido resuelve');
ok(agg2.perSku.find(p => p.sku === 'BRASIL').totalLbs === 1.75, 'woo: mapeo suma al café');

// comparación
const cmp = E.compareTotals(
  [{ sku: 'COLOMBIA', totalLbs: 10 }, { sku: 'BRASIL', totalLbs: 2 }],
  [{ sku: 'COLOMBIA', totalLbs: 8 }, { sku: 'PERU', totalLbs: 5 }]
);
eq(cmp.find(rw => rw.sku === 'COLOMBIA').diff, 2, 'cmp: diferencia Colombia');
eq(cmp.find(rw => rw.sku === 'PERU').diff, -5, 'cmp: Perú solo en woo');
eq(cmp.find(rw => rw.sku === 'BRASIL').diff, 2, 'cmp: Brasil solo escaneado');

// ---------- fechas ----------
eq(E.monthKey(new Date(2026, 7, 17).getTime()), '2026-08', 'monthKey');
ok(E.parseWooDate('2026-08-02') !== null, 'fecha ISO');
ok(E.monthKey(E.parseWooDate('8/2/2026')) === '2026-08', 'fecha US m/d/yyyy');

// ---------- CSV util ----------
eq(E.csvParse('a;b;c\n1;2;3'), [['a', 'b', 'c'], ['1', '2', '3']], 'csv con punto y coma');
eq(E.csvParse('a,b\n"x,y",2'), [['a', 'b'], ['x,y', '2']], 'csv con comillas');
ok(E.csvStringify([['a', 'b,c']]) === 'a,"b,c"', 'stringify escapa comas');

console.log('\nPruebas: ' + pass + ' OK, ' + fail + ' fallos');
process.exit(fail ? 1 : 0);
