// Instant coffee, the whole line: a pilot plant on one floor plate that roasts, grinds, extracts,
// concentrates, freezes, granulates, freeze-dries and packs one batch of green coffee.
// node build.mjs [--light] [--audit] [--video [--frame=WxH]]
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import * as k from "../../.claude/skills/anatomy/kit/iso-kit.mjs";
import * as G from "../../.claude/skills/anatomy/kit/lathe.mjs";
import { tubePieces, tubeSvg } from "../../.claude/skills/anatomy/kit/tube.mjs";
import * as A from "../../.claude/skills/anatomy/kit/audit.mjs";
import { kitScript } from "../../.claude/skills/anatomy/scripts/inline-kit.mjs";
import * as M from "./model.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const THEME = process.argv.includes("--light") ? "light" : "dark";
const VIDEO = process.argv.includes("--video");
const FRAME = (process.argv.find((a) => a.startsWith("--frame=")) ?? "--frame=1920x1080").slice(8).split("x").map(Number);

const W = VIDEO && FRAME[1] > FRAME[0] ? 450 : 640;
const H = 440;
const PLATE = { x: -232, y: -132, w: 464, d: 264, r: 10 };
const PLATE_H = 12;
const FOOT_H = 5;
const YB = -75; // back row
const YF = 72; // front row

// Station centres
const SI = [-196, YB]; // green coffee silo
const RO = [-118, YB]; // roaster drum (axis along x, from x -140 to -96)
const CL = [-74, YB]; // cooling tray
const E1X = -46; // bucket elevator to the grinder
const GR = [-18, YB]; // grinder
const E2 = [4, -85]; // bucket elevator to the column
const EX = [80, YB]; // extraction column
const BO = [80, -107]; // boiler
const KE = [170, YB]; // vacuum kettle
const CO = [212, -87]; // condenser
const FZ = { x0: 87, x1: 183, tunnel: [112, 164], nozzleX: 176 }; // belt freezer
const GN = [64, YF]; // granulator
const DR = { x0: -80, x1: -10 }; // freeze dryer cabinet
const CD = [-102, 102]; // ice condenser
const E3X = -100; // elevator to the filler
const FL = [-164, YF]; // filler hopper
const JARS = [-186, -164, -142];

const P = k.fitProjection(
  [...k.boxCorners(PLATE, -PLATE_H - FOOT_H, 0), [SI[0], SI[1], 146], [EX[0], EX[1], 131], [KE[0], KE[1], 102], [RO[0], RO[1], 82], [-164, YF, 90], [-100, 100, 70], [E2[0], E2[1], 120]],
  W,
  H,
  { pad: 20, azimuth: 38, elevation: 30 },
);
const V = G.viewOf(P);
const KS = G.scaleOf(P);
const at = (p) => k.iso(p, P);
const S = (paths, style) => k.solidSvg(paths, style);
const Ln = (d, style) => k.lineSvg(d, style);
const Dots = (points, style) => k.dotsSvg(points, style);
const Faded = (list, style) => k.fadedSvg(list, style);
const path3 = (points, closed = false) => k.pathOf(points.map(at), closed);
const f2 = (v) => Math.round(v * 100) / 100;
const UP = [0, 0, 1];
const vert = (cx, cy) => G.frameOf([cx, cy, 0], UP, [1, 0, 0], [0, 1, 0]);
const alongX = (o) => G.frameOf(o, [1, 0, 0], [0, 1, 0], [0, 0, 1]);
const alongY = (o) => G.frameOf(o, [0, 1, 0], [1, 0, 0], [0, 0, 1]);

const R = A.recorder(P);
const { nameFor } = R;
const record = R.solid;
function put(name, ref, svg, shapes = [], { bias = 0, ...rest } = {}) {
  return R.put({ name, at: ref, bias, svg, shapes, piece: "line", ...rest });
}

// ---------- helpers: solids ----------
function box(name, [x0, y0, z0], [x1, y1, z1], style = {}, { r = 0.6, steps = 2, bevel = 0, extra = "", inner = "", bias = 0, owner } = {}) {
  const plan = { x: x0, y: y0, w: x1 - x0, d: y1 - y0, r };
  const id = nameFor(name);
  const shape = record(A.slab(plan, z0, z1 - z0, { name: id, owner }, steps));
  put(id, [(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2], S(k.slabOf(plan, z0, z1 - z0, P, steps, bevel), { tone: "mid", ...style, inner }) + extra, [shape], { bias });
  return { plan, shape, id };
}
function turned(name, F, profile, style = {}, { extra = "", inner = "", bias = 0, smooth, steps, rims, bevel = 0, owner } = {}) {
  const opts = { bevel, ...(smooth !== undefined ? { smooth } : {}), ...(steps ? { steps } : {}), ...(rims ? { rims } : {}) };
  const paths = G.solidOf(profile, F, P, opts);
  const mid = (profile[0][0] + profile[profile.length - 1][0]) / 2;
  const id = nameFor(name);
  const shape = record(A.solid(F, profile, { name: id, owner }));
  put(id, G.add3(F.o, G.mul3(F.a, mid)), S(paths, { tone: "mid", ...style, inner }) + extra, [shape], { bias });
  return shape;
}
function disc(name, F, s0, s1, r, style = {}, options = {}) {
  return turned(name, F, [[s0, r], [s1, r]], style, options);
}
function ringOf(name, F, s0, s1, rIn, rOut, style = {}, { extra = "", inner = "", bias = 0, bevel = 0 } = {}) {
  const id = nameFor(name);
  const paths = G.disc(s0, s1, rOut, F, P, { bevel });
  const shape = record(A.ring(F, s0, s1, rIn, rOut, { name: id }));
  put(id, G.add3(F.o, G.mul3(F.a, (s0 + s1) / 2)), S(paths, { tone: "mid", ...style, inner }) + extra, [shape], { bias });
  return shape;
}
function ball(name, c, r, style = {}, { bias = 0, owner } = {}) {
  const id = nameFor(name);
  const shape = record(A.ball(c, r, { name: id, owner }));
  put(id, c, S(G.sphereOf(c, r, P, { steps: 36 }), { tone: "hi", ...style }), [shape], { bias });
  return shape;
}
function boss(name, centre, outward, r, length, { tone = "hi", bias = 0.1, ring = true, owner } = {}) {
  const F = G.frameAlong(centre, outward);
  const id = nameFor(name);
  put(id, G.add3(centre, G.mul3(F.a, length / 2)), S(G.disc(0, length, r, F, P), { tone }) + (ring && G.dot3(F.a, V) > 0.15 ? Ln(G.circleOf(F, length, r * 0.55, P, 16), { tone: "faint" }) : ""), [record(A.disc(F, 0, length, r, { name: id, owner }))], { bias });
  return G.add3(centre, G.mul3(F.a, length));
}
function flangeAt(name, centre, axis, r, thick, { bolts = 0, tone = "hi", bias = 0, owner } = {}) {
  const F = G.frameAlong(centre, axis);
  const id = nameFor(name);
  const towards = G.dot3(F.a, V) > 0 ? thick / 2 : -thick / 2;
  const dots = Math.abs(G.dot3(F.a, V)) > 0.12 && bolts ? Dots(G.dotsOf(F, towards, r * 0.74, bolts, P, { all: true }), { size: 0.4, tone: "mid" }) : "";
  put(id, centre, S(G.disc(-thick / 2, thick / 2, r, F, P), { tone }) + dots, [record(A.disc(F, -thick / 2, thick / 2, r, { name: id, owner }))], { bias });
}
// Prisms of any convex polygon along a frame axis (from the arcade example), for sloped parts.
const signed = (poly) => poly.reduce((a, [x, y], i) => {
  const [x2, y2] = poly[(i + 1) % poly.length];
  return a + x * y2 - x2 * y;
}, 0);
const screenOriented = (pts) => (signed(pts) < 0 ? [...pts].reverse() : pts);
function runsOf(flags, want) {
  const count = flags.length;
  const runs = [];
  const start = flags.findIndex((flag, index) => flag !== flags[(index + count - 1) % count]);
  if (start < 0) return flags[0] === want ? [Array.from({ length: count + 1 }, (_, index) => index % count)] : [];
  let run = null;
  for (let step = 0; step < count; step++) {
    const index = (start + step) % count;
    if (flags[index] === want) {
      if (!run) run = [index];
      run.push((index + 1) % count);
    } else if (run) {
      runs.push(run);
      run = null;
    }
  }
  if (run) runs.push(run);
  return runs;
}
function prismPaths(F, poly, s0, s1) {
  const ring = signed(poly) > 0 ? poly : [...poly].reverse();
  const n = ring.length;
  const W3 = (s, [x, y]) => [F.o[0] + F.a[0] * s + F.u[0] * x + F.v[0] * y, F.o[1] + F.a[1] * s + F.u[1] * x + F.v[1] * y, F.o[2] + F.a[2] * s + F.u[2] * x + F.v[2] * y];
  const capNear = G.dot3(F.a, V) > 0;
  const [nearS, farS] = capNear ? [s1, s0] : [s0, s1];
  const near = ring.map((p) => at(W3(nearS, p)));
  const far = ring.map((p) => at(W3(farS, p)));
  const normals = ring.map(([x0, y0], i) => {
    const [x1, y1] = ring[(i + 1) % n];
    return G.unit3(G.add3(G.mul3(F.u, y1 - y0), G.mul3(F.v, -(x1 - x0))));
  });
  const facing = normals.map((m) => G.dot3(m, V) > 1e-9);
  const outline = [];
  const crease = [];
  for (const run of runsOf(facing, false)) outline.push(k.pathOf(run.map((i) => near[i])));
  for (const run of runsOf(facing, true)) {
    crease.push(k.pathOf(run.map((i) => near[i])));
    outline.push(k.pathOf(run.map((i) => far[i])));
  }
  for (let i = 0; i < n; i++) if (facing[(i + n - 1) % n] !== facing[i]) outline.push(k.pathOf([near[i], far[i]]));
  const parts = [k.pathOf(screenOriented(near), true), k.pathOf(screenOriented(far), true)];
  const buckets = [[], [], [], [], []];
  for (let i = 0; i < n; i++) {
    if (!facing[i]) continue;
    const quad = screenOriented([near[i], near[(i + 1) % n], far[(i + 1) % n], far[i]]);
    parts.push(k.pathOf(quad, true));
    buckets[G.toneOf(normals[i], P)].push(k.pathOf(quad, true));
  }
  const capTone = G.toneOf(capNear ? F.a : G.mul3(F.a, -1), P);
  buckets[capTone].push(k.pathOf(screenOriented(near), true));
  return { fill: parts.join(""), outline: outline.join(""), crease: crease.join(""), top: buckets[4].join(""), shades: buckets.slice(0, 4).map((b) => b.join("")) };
}
function prism(name, F, poly, s0, s1, style = {}, { extra = "", inner = "", bias = 0, ref } = {}) {
  const id = nameFor(name);
  const shape = record(A.prism(F, poly, s0, s1, { name: id }));
  const cx = poly.reduce((a, p) => a + p[0], 0) / poly.length;
  const cy = poly.reduce((a, p) => a + p[1], 0) / poly.length;
  const centre = G.add3(G.add3(G.add3(F.o, G.mul3(F.a, (s0 + s1) / 2)), G.mul3(F.u, cx)), G.mul3(F.v, cy));
  put(id, ref ?? centre, S(prismPaths(F, poly, s0, s1), { tone: "mid", ...style, inner }) + extra, [shape], { bias });
  return shape;
}

// ---------- helpers: pipes ----------
const ROUTES = {};
function pipe(name, control, r, { bend = 2.6, tone = "hi", flanges = [true, true], flangeR = 1.55, bands = [], bias = 0, maxLength = 18, spacing, touch, breaks = [], gaps: extra = [], flow = true, rims } = {}) {
  const line = G.fillet(control, Math.max(r * bend, 3), 12, { P, tube: r });
  const total = G.pathLength(line);
  const collars = [];
  [[0, -1], [total, 1]].forEach(([along, sign], index) => {
    if (!flanges[index]) return;
    const thick = Math.max(0.9, r * 0.55);
    const tangent = G.tangentAlong(line, along);
    collars.push({ kind: "flange", centre: G.add3(G.pointAlong(line, along), G.mul3(tangent, (-sign * thick) / 2)), tangent, radius: r * flangeR, thick, gap: sign < 0 ? [0, thick] : [total - thick, total] });
  });
  for (const share of bands) {
    const along = total * share;
    const thick = Math.max(0.8, r * 0.7);
    collars.push({ kind: "band", centre: G.pointAlong(line, along), tangent: G.tangentAlong(line, along), radius: r * 1.18, thick, gap: [along - thick / 2, along + thick / 2] });
  }
  const gaps = [...collars.map((c) => c.gap), ...extra];
  const id = nameFor(name);
  R.route(id, line, r, { owner: id, touch, gaps, breaks, rims: rims ?? flanges.map((on) => (on ? r * flangeR : r)), piece: "line" });
  tubePieces(line, r, P, { maxLength, spacing: spacing ?? Math.max(0.8, Math.min(2.4, r * 0.18)), gaps, breaks }).forEach((piece, index) => {
    const mark = flow ? Ln(k.pathOf(piece.points.map(at)), { tone: "hi", flow: true, className: "ic-flow" }) : "";
    put(`${id}:${index}`, piece.mid, tubeSvg(piece, { tone }) + mark, [A.tube(piece.points, piece.radii)], { bias, route: id, chunk: index, attrs: ` data-route="${id}" data-chunk="${index}"` });
  });
  for (const c of collars) flangeAt(`${id}.${c.kind}`, c.centre, c.tangent, c.radius, c.thick, { bolts: c.kind === "flange" && r > 2.5 ? 6 : 0, tone: c.kind === "flange" ? tone : "mid", owner: id, bias });
  line.owner = id;
  ROUTES[id] = line;
  return line;
}
// A duct between two flat ports through an elbow ball on each: one straight run, no bends to pinch.
function elbowDuct(name, faceA, normalA, faceRA, faceB, normalB, faceRB, r, { ballR = r * 1.45, tone = "hi", flow = true, owners = [`${name}.fittingA`, `${name}.fittingB`] } = {}) {
  const cA = G.add3(faceA, G.mul3(normalA, Math.sqrt(ballR ** 2 - faceRA ** 2)));
  const cB = G.add3(faceB, G.mul3(normalB, Math.sqrt(ballR ** 2 - faceRB ** 2)));
  ball(`${name}.elbow`, cA, ballR, { tone }, { owner: owners[0] });
  ball(`${name}.elbow`, cB, ballR, { tone }, { owner: owners[1] });
  const axis = G.unit3(G.sub3(cB, cA));
  const reach = Math.sqrt(ballR ** 2 - r ** 2);
  return pipe(name, [G.add3(cA, G.mul3(axis, reach)), G.sub3(cB, G.mul3(axis, reach))], r, { flanges: [false, false], rims: [r, r], tone, flow });
}

// ---------- helpers: glass, levels, dials, knobs ----------
const SHINE_ANGLE = (95 * Math.PI) / 180;
function glassCyl(name, cx, cy, r, z0, z1, { wall = 0.7, bias = 0.3, extra = "", tone = "lo", solid = false } = {}) {
  const F = vert(cx, cy);
  const paths = k.cylinder(cx, cy, r, z0, z1 - z0, P, 64);
  const sx = cx + (r - 0.01) * Math.cos(SHINE_ANGLE);
  const sy = cy + (r - 0.01) * Math.sin(SHINE_ANGLE);
  const svg = [Ln(paths.outline, { tone }), Ln(k.sideArc(cx, cy, r, z0, P, 48), { tone }), Ln(k.ring(cx, cy, r, z1, P, 64), { tone }), Ln(k.rise([sx, sy], z0, z1, P), { tone: "faint" }), extra].join("");
  const id = nameFor(name);
  const shape = record(solid ? A.cylinder(cx, cy, r, z0, z1 - z0, { name: id }) : A.ring(F, z0, z1, r - wall, r, { name: id }));
  put(id, [cx, cy, (z0 + z1) / 2], svg, [shape], { bias });
  return shape;
}
function glassLathe(name, F, outer, { wall = 0.7, bias = 0.3, extra = "", ref, tone = "lo" } = {}) {
  const closed = [[outer[0][0], 0], ...outer, [outer[outer.length - 1][0], 0]];
  const out = G.outlineOf(closed, F, P, { rims: "all" });
  const inner = [...outer].reverse().map(([s, r]) => [s, Math.max(0.2, r - wall)]);
  const meridian = [...outer.map(([s, r]) => [s, r]), ...inner];
  const id = nameFor(name);
  const mid = (outer[0][0] + outer[outer.length - 1][0]) / 2;
  put(id, ref ?? G.add3(F.o, G.mul3(F.a, mid)), Ln(out.outline, { tone }) + extra, [record(A.lathe(F, meridian, { name: id }))], { bias });
}
const LEVELS = [];
function level(name, cx, cy, r, z0, zMax, cls, key, { tone = "lo", bias = 0.1, extra = "" } = {}) {
  const svg = `<g data-part="${name}" class="iso-solid ${cls}">${S(k.cylinder(cx, cy, r, z0, zMax - z0, P, 48), { tone, crease: "none" })}</g>${extra}`;
  const id = nameFor(name);
  put(id, [cx, cy, (z0 + zMax) / 2], svg, [record(A.cylinder(cx, cy, r, z0, zMax - z0, { name: id }))], { bias });
  LEVELS.push({ part: name, cx, cy, r, z: [z0, zMax], tone, key });
}
const DIALS = [];
function dial(name, cx, cy, z, Rr, key, { count = 40, every = 5, from = (-135 * Math.PI) / 180, span = (270 * Math.PI) / 180, bias = 0.2 } = {}) {
  const top = z + 3;
  const ticks = k.radialTicks(cx, cy, Rr - 1.6, count, every, top, [0.7, 1.3], P, from, span);
  const a0 = from;
  const needle = k.lineOnTop([cx - Math.sin(a0) * 1.2, cy + Math.cos(a0) * 1.2], [cx + Math.sin(a0) * (Rr - 1.9), cy - Math.cos(a0) * (Rr - 1.9)], top + 0.2, P);
  const svg = [
    S(k.cylinder(cx, cy, Rr, z, 3, P, 48, 0.4), { tone: "hi", crease: "lo" }),
    Ln(k.knurl(cx, cy, Rr, top - 1.2, top, 44, P, 0.3), { tone: "lo" }),
    Ln(k.sideArc(cx, cy, Rr, top - 1.2, P, 32), { tone: "faint" }),
    Ln(k.ring(cx, cy, Rr - 1, top, P, 48), { tone: "lo" }),
    Ln(ticks.minor, { tone: "lo" }),
    Ln(ticks.major, { tone: "mid" }),
    `<path data-part="${name}" class="iso-line" data-tone="hi" data-free="" d="${needle}" style="stroke-width:0.9px"/>`,
    Ln(k.ring(cx, cy, 0.8, top, P, 12), { tone: "mid" }),
  ].join("");
  const id = nameFor(name);
  put(id, [cx, cy, z + 1.5], svg, [record(A.cylinder(cx, cy, Rr, z, 3, { name: id }))], { bias });
  DIALS.push({ name, cx, cy, top, R: Rr, from, span, key });
}
function knob(name, centre, outward, r, length, { pointer = true } = {}) {
  const F = G.frameAlong(centre, outward);
  const tip = G.add3(centre, G.mul3(F.a, length));
  const side = G.unit3(G.cross3(F.a, UP));
  const pointerLine = pointer ? Ln(path3([G.add3(tip, G.mul3(F.a, 0.05)), G.add3(G.add3(tip, G.mul3(F.a, 0.05)), G.mul3(G.unit3(G.add3(side, G.mul3(UP, 0.6))), r * 0.85))]), { tone: "hi", free: "end" }) : "";
  const id = nameFor(name);
  put(id, G.add3(centre, G.mul3(F.a, length / 2)), S(G.disc(0, length, r, F, P, { bevel: 0.3 }), { tone: "hi" }) + Faded(G.ribsOf(F, 0, length, r, 22, P, { fade: [0.1, 0.55], seams: true }), { tone: "lo" }) + pointerLine, [record(A.disc(F, 0, length, r, { name: id }))], { bias: 0.2 });
}
// A motor: a can with a seam and a domed end, standing on a face along `axis`.
function motor(name, F, s0, s1, r, { tone = "hi" } = {}) {
  return turned(name, F, [[s0, r], [s1 - r * 0.25, r], [s1 - r * 0.1, r * 0.82, 1], [s1, r * 0.5]], { tone }, { inner: Ln(G.arcOf(F, s0 + (s1 - s0) * 0.25, r, P), { tone: "faint" }) });
}
// A vertical post with a foot, in up to three segments (gaps where collars sit).
function post(name, x, y, segments, r = 2.4, { foot = true } = {}) {
  const F = vert(x, y);
  if (foot) disc(`${name}.foot`, F, 0, 1.2, r * 1.5, { tone: "lo" });
  for (const [z0, z1] of segments) disc(name, F, z0, z1, r, { tone: "mid" }, { steps: 20 });
  return F;
}
// A live stream of coffee: dots that travel along a 3D polyline while `key` is on.
const STREAMS = [];
function stream(name, path, key, { count = 18, size = 0.55, speed = 1, tone = "lit", jitter = 0.6 } = {}) {
  STREAMS.push({ part: name, path, key, count, size, speed, tone, jitter });
}
const SPINNERS = [];

// ---------- the floor ----------
const back = [];
back.push(`<path class="iso-halo" d="${k.haloOf(PLATE, -PLATE_H - FOOT_H, PLATE_H, P)}"/>`);
const byDepth = (points) => [...points].sort((a, b) => k.depthOf([a[0], a[1], 0], P) - k.depthOf([b[0], b[1], 0], P));
const FEET = [...k.corners(PLATE, 22), [0, PLATE.y + 22], [0, PLATE.y + PLATE.d - 22]];
for (const [x, y] of byDepth(FEET)) {
  back.push(S(k.cylinder(x, y, 7, -PLATE_H - FOOT_H, 1.6, P, 28), { tone: "lo" }));
  back.push(S(k.cylinder(x, y, 5.4, -PLATE_H - FOOT_H + 1.6, FOOT_H - 1.6, P, 28), { tone: "mid" }));
}
back.push(S(k.slabOf(PLATE, -PLATE_H, PLATE_H, P, 8, 1.6), { tone: "mid", inner: Ln(k.sideSeam(PLATE, -4, P, 8), { tone: "faint" }) }));
back.push(Ln(k.planOutline(k.insetPlan(PLATE, 5), 0, P), { tone: "lo" }));
back.push(Ln(k.lineOnTop([PLATE.x + 5, 0], [PLATE.x + PLATE.w - 5, 0], 0, P), { tone: "faint" }));
const plateScrews = k.corners(PLATE, 10);
back.push(Ln(plateScrews.map(([x, y]) => k.ring(x, y, 2.2, 0, P, 16)).join(""), { tone: "lo" }));
back.push(Dots(plateScrews.map(([x, y]) => at([x, y, 0])), { size: 0.5 }));
record(A.slab(PLATE, -PLATE_H, PLATE_H, { name: "stand.plate", ground: true }, 8));
const STRIP = { x: -214, y: PLATE.y + PLATE.d - 12, w: 428, d: 6, r: 1 };
back.push(S(k.slabOf(STRIP, 0, 0.6, P, 3), { tone: "lo", crease: "none" }));
const ticks = k.topTicks(STRIP.x + 4, STRIP.x + STRIP.w - 4, 4, 5, STRIP.y, 0.6, [1.8, 3.4], P);
back.push(Ln(ticks.minor, { tone: "lo" }), Ln(ticks.major, { tone: "mid" }));
const LABEL = { x: -228, y: 100, w: 28, d: 11, r: 1.2 };
back.push(S(k.slabOf(LABEL, 0, 0.8, P, 3), { tone: "lo", crease: "none" }));
back.push(Ln(k.planOutline(k.insetPlan(LABEL, 1.4), 0.8, P, 3), { tone: "faint" }));
back.push(Ln([18, 12, 15].map((w, i) => k.lineOnTop([LABEL.x + 4, LABEL.y + 2.8 + i * 2.7], [LABEL.x + 4 + w, LABEL.y + 2.8 + i * 2.7], 0.8, P)).join(""), { tone: "lo", free: true }));
back.push(Dots([at([LABEL.x + LABEL.w - 2.4, LABEL.y + 2.2, 0.8]), at([LABEL.x + LABEL.w - 2.4, LABEL.y + LABEL.d - 2.2, 0.8])], { size: 0.45 }));
record(A.slab(STRIP, 0, 0.6, { name: "stand.strip", ground: true }, 3));
record(A.slab(LABEL, 0, 0.8, { name: "stand.label", ground: true }, 3));

// ---------- station 1: silo, trough, roaster, cooler ----------
{
  const F = vert(SI[0], SI[1]);
  for (const a of [45, 135, 225, 315]) {
    const x = SI[0] + 18 * Math.cos((a * Math.PI) / 180);
    const y = SI[1] + 18 * Math.sin((a * Math.PI) / 180);
    post("silo.leg", x, y, [[1.2, 90]], 1.6);
  }
  ringOf("silo.ring", F, 90, 93, 15, 19.5, { tone: "mid" }, { bevel: 0.3, extra: Dots(G.dotsOf(F, 93, 17.5, 8, P, { all: true }), { size: 0.42, tone: "mid" }) });
  turned("silo.cone", F, [[73, 4], [93, 14.6]], { tone: "hi" }, { inner: Ln(G.arcOf(F, 83, 9.3, P, { slope: 10.6 / 20 }), { tone: "faint" }) });
  turned("silo.shell", F, [[93, 16], [130, 16]], { tone: "hi" }, { inner: Ln(G.arcOf(F, 105, 16, P) + G.arcOf(F, 118, 16, P), { tone: "faint" }) });
  turned("silo.lid", F, [[130, 16.6], [132, 16.6], [132, 16], [134, 13.4, 1], [136.5, 8.5, 1], [138, 4]], { tone: "hi" });
  disc("silo.vent", F, 138, 144, 2.2, { tone: "mid" });
  box("silo.gate", [SI[0] - 4, SI[1] - 4, 66], [SI[0] + 4, SI[1] + 4, 73], { tone: "mid" }, { r: 0.6, extra: Ln(path3([[SI[0] + 4, SI[1] - 1, 69.5], [SI[0] + 7, SI[1] - 1, 71.5]]), { tone: "hi", free: "end" }) });
  // a vibrating trough carries the beans to the roaster's inlet hopper
  box("silo.trough", [SI[0] + 4, SI[1] - 4, 58], [-138, SI[1] + 4, 61], { tone: "lo" });
  box("silo.trough.wall", [SI[0] + 4, SI[1] - 4, 61], [-138, SI[1] - 2.6, 63.5], { tone: "mid" });
  box("silo.trough.wall", [SI[0] + 4, SI[1] + 2.6, 61], [-138, SI[1] + 4, 63.5], { tone: "mid" });
  post("silo.trough.post", -154, SI[1], [[1.2, 58]], 1.5);
  stream("beans-in", [[SI[0], SI[1], 66], [SI[0], SI[1], 61.5], [-139, SI[1], 61.5], [-132, SI[1], 55]], "beansIn", { count: 16, size: 0.5 });

  // the roaster: a drum along x on two cradles, a burner under it, a chimney, a door with a window
  const DRUM_O = [-140, RO[1], 30];
  const FD = alongX(DRUM_O);
  box("roaster.base", [-138, RO[1] - 13, 0], [-98, RO[1] + 13, 2], { tone: "lo" }, { r: 1, steps: 3, extra: Dots(k.corners({ x: -138, y: RO[1] - 13, w: 40, d: 26, r: 1 }, 2.5).map(([x, y]) => at([x, y, 2])), { size: 0.4 }) });
  box("roaster.cradle", [-130, RO[1] - 3, 2], [-126, RO[1] + 3, 15], { tone: "mid" });
  box("roaster.cradle", [-110, RO[1] - 3, 2], [-106, RO[1] + 3, 15], { tone: "mid" });
  box("roaster.burner", [-124, RO[1] - 4, 2], [-112, RO[1] + 4, 10], { tone: "mid" }, { r: 0.8, bevel: 0.3, inner: Ln(k.sideSeam({ x: -124, y: RO[1] - 4, w: 12, d: 8, r: 0.8 }, 6, P, 2), { tone: "faint" }) });
  knob("roaster.gas", [-118, RO[1] + 4, 6], [0, 1, 0], 1.6, 2);
  motor("roaster.motor", G.frameAlong(DRUM_O, [-1, 0, 0]), 0, 9, 6);
  disc("roaster.flange", FD, 0, 3, 16, { tone: "mid" });
  turned("roaster.drum", FD, [[3, 15], [41, 15]], { tone: "hi" }, { inner: Ln(G.arcOf(FD, 12, 15, P) + G.arcOf(FD, 32, 15, P), { tone: "faint" }) });
  disc("roaster.flange", FD, 41, 44, 16, { tone: "mid" }, { extra: Dots(G.dotsOf(FD, 44, 14.2, 10, P, { all: true }), { size: 0.42, tone: "mid" }) });
  disc("roaster.door", FD, 44, 46, 13, { tone: "hi" }, { bevel: 0.4, extra: Ln(G.circleOf(FD, 46, 6, P, 32) + G.circleOf(FD, 46, 5.2, P, 32), { tone: "lo" }) });
  box("roaster.handle", [-94, RO[1] - 9, 32], [-92.5, RO[1] - 6, 38], { tone: "mid" });
  box("roaster.hinge", [-94.5, RO[1] + 10, 24], [-93, RO[1] + 12, 36], { tone: "lo" });
  turned("roaster.hopper", vert(-132, RO[1]), [[45.4, 3], [55, 7]], { tone: "mid" });
  disc("roaster.chimney", vert(-116, RO[1]), 45.4, 80, 3.5, { tone: "mid" }, { inner: Ln(G.arcOf(vert(-116, RO[1]), 60, 3.5, P) + G.arcOf(vert(-116, RO[1]), 72, 3.5, P), { tone: "faint" }) });
  turned("roaster.chimney.cap", vert(-116, RO[1]), [[80, 4.4], [81.5, 4.4], [82.5, 3, 1], [83, 1.5]], { tone: "mid" });
  box("roaster.chute", [-94, RO[1] - 3, 16], [-84, RO[1] + 3, 22], { tone: "lo" });
  dial("roast", -104, RO[1] - 9, 2, 4, "roastShare", { count: 36, every: 6 });
  // the vane lines ride on the drum's skin: recorded as a thin shell just outside it, so they are drawn after the drum
  SPINNERS.push({ part: "drum-vanes", kind: "vanes", o: DRUM_O, a: [1, 0, 0], u: [0, 1, 0], v: [0, 0, 1], s0: 5, s1: 39, r: 15.2, n: 6, key: "drumTurning", rate: 1.6 });
  put("roaster.vanes", [-118, RO[1], 30], `<g data-part="drum-vanes"></g>`, [record(A.disc(FD, 5, 39, 15.4, { name: "roaster.vanes", owner: "roaster.drum" }))], { bias: 0.3 });

  // the cooling tray: a perforated tray with a stirring arm, beans spiral to the exit chute
  const FC = vert(CL[0], CL[1]);
  disc("cooler.pedestal", FC, 0, 8, 5, { tone: "mid" });
  disc("cooler.tray", FC, 8, 11, 15, { tone: "lo" }, { extra: Dots(Array.from({ length: 60 }, (_, i) => { const a = i * 2.399963; const rr = 12.5 * Math.sqrt((i + 0.5) / 60); return at([CL[0] + rr * Math.cos(a), CL[1] + rr * Math.sin(a), 11]); }), { size: 0.3, tone: "lo" }) });
  ringOf("cooler.rim", FC, 11, 15, 14, 15.5, { tone: "mid" });
  disc("cooler.hub", FC, 11, 17, 2, { tone: "mid" });
  motor("cooler.motor", FC, 17, 24, 3);
  put("cooler.arm", [CL[0], CL[1], 12], `<g data-part="cooler-arm"></g>`, [record(A.disc(FC, 11.6, 12.6, 13.5, { name: "cooler.arm", owner: "cooler.hub" }))], { bias: 0.2 });
  SPINNERS.push({ part: "cooler-arm", kind: "arm", c: [CL[0], CL[1], 12.2], r0: 2.5, r1: 13.5, n: 2, key: "beansOut", rate: 2.2 });
  box("cooler.chute", [-58.4, CL[1] - 3, 11], [-50, CL[1] + 3, 15], { tone: "lo" });
  const spiral = Array.from({ length: 26 }, (_, i) => { const t = i / 25; const a = Math.PI * 4 * t + Math.PI; const rr = 13 - 9 * t; return [CL[0] + rr * Math.cos(a), CL[1] + rr * Math.sin(a), 11.6]; });
  stream("beans-out", [[-93, RO[1], 24], [-85, RO[1], 22.6], [-78, RO[1], 11.6], ...spiral, [-59, CL[1], 15.6], [-50, CL[1], 15.6]], "beansOut", { count: 30, size: 0.5, speed: 0.6 });
}

// ---------- station 2: elevator, grinder, elevator and screw to the column ----------
{
  box("lift1.body", [E1X - 4, YB - 6, 0], [E1X + 4, YB + 6, 66], { tone: "mid" }, { bevel: 0.3, inner: Ln(k.sideSeam({ x: E1X - 4, y: YB - 6, w: 8, d: 12, r: 0.6 }, 33, P, 2), { tone: "faint" }) });
  box("lift1.head", [E1X - 4, YB - 5, 66], [-14, YB + 5, 74], { tone: "mid" }, { bevel: 0.3 });
  motor("lift1.motor", vert(E1X, YB), 74, 81, 3.5);
  disc("lift1.spout", vert(GR[0], GR[1]), 63, 66, 2.5, { tone: "lo" });
  stream("grind-in", [[GR[0], GR[1], 63], [GR[0], GR[1], 56]], "grindIn", { count: 8, size: 0.5 });
  // the grinder: a roller mill with a hopper, two roll ends you can see turn, a motor, a funnel below
  for (const [dx, dy] of [[-11, -9], [11, -9], [-11, 9], [11, 9]]) post("mill.leg", GR[0] + dx, GR[1] + dy, [[1.2, 22]], 1.8);
  const MILL = { x: GR[0] - 14, y: GR[1] - 12, w: 28, d: 24, r: 1 };
  box("mill.housing", [MILL.x, MILL.y, 22], [MILL.x + MILL.w, MILL.y + MILL.d, 50], { tone: "mid" }, { r: 1, steps: 3, bevel: 0.5, inner: Ln(k.sideSeam(MILL, 36, P, 3), { tone: "faint" }), extra: Dots(k.corners(MILL, 2.5).map(([x, y]) => at([x, y, 50])), { size: 0.42 }) });
  turned("mill.hopper", vert(GR[0], GR[1]), [[50, 4], [62, 11]], { tone: "hi" }, { inner: Ln(G.arcOf(vert(GR[0], GR[1]), 58, 8.7, P, { slope: 7 / 12 }), { tone: "faint" }) });
  for (const [i, x] of [GR[0] - 7, GR[0] + 7].entries()) {
    const FR = alongY([x, MILL.y + MILL.d, 36]);
    disc("mill.roll", FR, 0, 1.6, 6, { tone: "hi" }, { extra: `<g data-part="roll-${i}"></g>` + Ln(G.circleOf(FR, 1.6, 1.4, P, 16), { tone: "lo" }) });
    SPINNERS.push({ part: `roll-${i}`, kind: "spokes", c: [x, MILL.y + MILL.d + 1.65, 36], u: [1, 0, 0], v: [0, 0, 1], r0: 1.8, r1: 5.2, n: 6, key: "rollersTurning", rate: i ? -3 : 3 });
  }
  motor("mill.motor", G.frameAlong([MILL.x, GR[1], 36], [-1, 0, 0]), 0, 10, 5.5);
  turned("mill.funnel", vert(GR[0], GR[1]), [[14, 3], [22, 8]], { tone: "mid" });
  box("mill.chute", [GR[0] - 4, E2[1] + 3, 8], [E2[0] - 4, GR[1] + 1, 13], { tone: "lo" });
  stream("grounds-out", [[GR[0], GR[1], 14], [GR[0], GR[1], 10.6], [E2[0] - 5, GR[1], 10.6]], "groundsOut", { count: 12, size: 0.42 });
  // elevator 2 lifts the grounds to a screw conveyor over the column's charge hopper
  box("lift2.body", [E2[0] - 4, E2[1] - 5, 0], [E2[0] + 4, E2[1] + 5, 100], { tone: "mid" }, { bevel: 0.3, inner: Ln(k.sideSeam({ x: E2[0] - 4, y: E2[1] - 5, w: 8, d: 10, r: 0.6 }, 50, P, 2), { tone: "faint" }) });
  box("lift2.head", [E2[0] - 8, E2[1] - 5, 100], [E2[0] + 8, E2[1] + 5, 112], { tone: "mid" }, { bevel: 0.3 });
  motor("lift2.motor", vert(E2[0], E2[1]), 112, 119, 3.5);
  const SCREW = alongX([E2[0] + 8, E2[1], 106]);
  turned("screw.tube", SCREW, [[0, 4.5], [72, 4.5]], { tone: "hi" }, { inner: Ln([18, 36, 54].map((s) => G.arcOf(SCREW, s, 4.5, P)).join(""), { tone: "faint" }) });
  disc("screw.cap", SCREW, 72, 74, 5, { tone: "mid" });
  disc("screw.spout", vert(EX[0], E2[1]), 97.5, 101.5, 2, { tone: "lo" });
  stream("grounds-down", [[EX[0], E2[1], 97.5], [EX[0], E2[1], 92]], "groundsOut", { count: 8, size: 0.42 });
}

// ---------- station 3: extraction column, boiler, pump ----------
const EXB = { x: EX[0] - 20, y: EX[1] - 20, w: 40, d: 40, r: 2 };
const EXF = vert(EX[0], EX[1]);
let EX_OUT;
let EX_IN;
{
  box("ex.base", [EXB.x, EXB.y, 0], [EXB.x + EXB.w, EXB.y + EXB.d, 12], { tone: "mid" }, { r: 2, steps: 4, bevel: 0.6, inner: Ln(k.sideSeam(EXB, 3, P, 4), { tone: "faint" }), extra: Dots(k.corners(EXB, 3).map(([x, y]) => at([x, y, 12])), { size: 0.45 }) });
  const c = [EX[0], EXB.y + EXB.d, 6];
  const face = boss("ex.drain.boss", c, [0, 1, 0], 2.2, 2.5, { tone: "mid" });
  const SF = G.frameAlong(face, [0, 1, 0]);
  disc("ex.drain.stem", SF, 0, 3.5, 0.9, { tone: "mid" });
  disc("ex.drain.wheel", SF, 3.5, 4.9, 3.4, { tone: "hi" }, { extra: Faded(G.ribsOf(SF, 3.5, 4.9, 3.4, 24, P, { fade: [0.1, 0.55], seams: true }), { tone: "lo" }) + Ln(G.circleOf(SF, 4.9, 1.2, P, 16), { tone: "lo" }) });
  EX_OUT = boss("ex.out.boss", [EXB.x + EXB.w, EX[1] + 8, 5], [1, 0, 0], 3, 2.5);
  dial("therm", EX[0] + 14.5, EX[1] + 14.5, 12, 4.5, "heat");
  level("sump", EX[0], EX[1], 10.3, 12.3, 19, "ic-coffee", "sump", { tone: "lo" });
  disc("ex.plate", EXF, 19, 20, 10.3, { tone: "mid" });
  level("bed", EX[0], EX[1], 10.3, 20, 46, "ic-bed", "bed", { tone: "lo" });
  level("water", EX[0], EX[1], 10.3, 46, 72, "ic-water", "water", { tone: "faint" });
  glassCyl("ex.glass", EX[0], EX[1], 11, 12, 84);
  for (const a of [-22, 98, 158, 218]) {
    const x = EX[0] + 13.5 * Math.cos((a * Math.PI) / 180);
    const y = EX[1] + 13.5 * Math.sin((a * Math.PI) / 180);
    const F = vert(x, y);
    disc("ex.nut", F, 12, 14, 1.8, { tone: "mid" }, { steps: 6 });
    disc("ex.rod", F, 14, 84, 1, { tone: "mid" }, { steps: 16 });
    disc("ex.nut.top", F, 90, 92, 1.8, { tone: "mid" }, { steps: 6 });
  }
  disc("ex.head", EXF, 84, 90, 20, { tone: "hi" }, { bevel: 0.6, inner: Ln(G.arcOf(EXF, 86, 20, P), { tone: "faint" }) });
  EX_IN = boss("ex.in.boss", [EX[0], EX[1], 90], UP, 3.2, 6);
  turned("ex.hopper", vert(EX[0], E2[1]), [[90, 2.5], [97, 4.5]], { tone: "mid" });
  // the boiler behind the column
  const BOF = vert(BO[0], BO[1]);
  disc("boiler.foot", BOF, 0, 1.6, 9.8, { tone: "lo" });
  turned("boiler.shell", BOF, [[1.6, 9], [28, 9]], { tone: "hi" }, { inner: Ln(G.arcOf(BOF, 8, 9, P) + G.arcOf(BOF, 20, 9, P), { tone: "faint" }) });
  turned("boiler.lid", BOF, [[28, 9.6], [29.6, 9.6], [29.6, 9], [31, 8.2, 1], [32.4, 6, 1], [33, 3.4]], { tone: "hi" });
  const BO_OUT = boss("boiler.out.boss", [BO[0], BO[1], 33], UP, 3.2, 3);
  box("boiler.element", [BO[0] + 8.8, BO[1] - 2, 4], [BO[0] + 15, BO[1] + 2, 12], { tone: "mid" }, { r: 0.8, steps: 2, extra: Dots([at([BO[0] + 15, BO[1] - 1.2, 10]), at([BO[0] + 15, BO[1] + 1.2, 10])], { size: 0.4 }) });
  pipe("water", [BO_OUT, [BO[0], BO[1], 129], [EX[0], EX[1], 129], EX_IN], 1.9, { bands: [0.5] });
}
function pump(name, x0, y0, { inlet = [-1, 0, 0], outlet = [1, 0, 0] } = {}) {
  box(`${name}.block`, [x0, y0, 0], [x0 + 12, y0 + 12, 9], { tone: "mid" }, { r: 1, steps: 3, bevel: 0.4, extra: Dots([at([x0 + 2, y0 + 2, 9]), at([x0 + 10, y0 + 10, 9]), at([x0 + 10, y0 + 2, 9])], { size: 0.4 }) });
  motor(`${name}.motor`, vert(x0 + 6, y0 + 6), 9, 18, 3.8);
  const side = (d) => [x0 + 6 + d[0] * 6, y0 + 6 + d[1] * 6, 5];
  return { inlet: boss(`${name}.in.boss`, side(inlet), inlet, 3, 2.5), outlet: boss(`${name}.out.boss`, side(outlet), outlet, 3, 2.5) };
}
const P1 = pump("pump1", 118, EX[1] + 2);
pipe("extract-a", [EX_OUT, P1.inlet], 1.9);

// ---------- station 4: vacuum kettle, condenser, vacuum pump, feed pump ----------
const KEB = { x: KE[0] - 20, y: KE[1] - 20, w: 40, d: 40, r: 2 };
const KEF = vert(KE[0], KE[1]);
let KE_OUT;
{
  box("ke.base", [KEB.x, KEB.y, 0], [KEB.x + KEB.w, KEB.y + KEB.d, 10], { tone: "mid" }, { r: 2, steps: 4, bevel: 0.6, inner: Ln(k.sideSeam(KEB, 2.5, P, 4), { tone: "faint" }), extra: Dots(k.corners(KEB, 3).map(([x, y]) => at([x, y, 10])), { size: 0.45 }) });
  const KE_IN = boss("ke.in.boss", [KEB.x, KE[1] + 8, 5], [-1, 0, 0], 3, 2.5);
  KE_OUT = boss("ke.out.boss", [KE[0] + 6, KEB.y + KEB.d, 5], [0, 1, 0], 3, 2.5);
  knob("ke.heat.knob", [KE[0] - 10, KEB.y + KEB.d, 5], [0, 1, 0], 2.2, 2.5);
  pipe("extract-b", [P1.outlet, KE_IN], 1.9);
  turned("ke.shell", KEF, [[10, 16], [30, 16]], { tone: "hi" }, { inner: Ln(G.arcOf(KEF, 12, 16, P), { tone: "faint" }) });
  disc("ke.jacket", KEF, 30, 33.5, 17.4, { tone: "mid" });
  turned("ke.shell", KEF, [[33.5, 16], [52, 16]], { tone: "hi" }, { inner: Ln(G.arcOf(KEF, 50, 16, P), { tone: "faint" }) });
  disc("ke.flange", KEF, 52, 55, 17.6, { tone: "hi" }, { extra: Dots(G.dotsOf(KEF, 55, 16.8, 10, P, { all: true }), { size: 0.42, tone: "mid" }) });
  const dome = [];
  for (let i = 0; i <= 8; i++) {
    const z = 55 + (15.2 * i) / 8;
    dome.push([z, Math.sqrt(Math.max(25, 256 - (z - 55) ** 2)), i > 0 && i < 8 ? 1 : 0]);
  }
  dome[dome.length - 1] = [70.2, 5];
  glassLathe("ke.dome", KEF, dome, { ref: [KE[0], KE[1], 61] });
  disc("ke.neck", KEF, 70.2, 74, 5.5, { tone: "mid" });
  const KE_VAP = boss("ke.vap.boss", [KE[0], KE[1], 74], UP, 4.5, 3);
  const U = k.towardViewer(P);
  const SG = [KE[0] + 22 * U[0], KE[1] + 22 * U[1]];
  for (const z of [17, 47]) boss("ke.sight.boss", [KE[0] + 16 * U[0], KE[1] + 16 * U[1], z], [U[0], U[1], 0], 1.1, 3.8, { tone: "mid", ring: false });
  level("kettle", SG[0], SG[1], 1.5, 15, 49, "ic-coffee", "kettleFill", { tone: "lo", extra: `<g class="iso-dots ic-mist" data-part="bubbles"></g>` });
  glassCyl("ke.sight", SG[0], SG[1], 2.2, 14, 50, { wall: 0.55 });
  // condenser standing on its receiver
  const COF = vert(CO[0], CO[1]);
  level("condensate", CO[0], CO[1], 7.2, 0.6, 17, "ic-water", "condensate", { tone: "faint" });
  glassCyl("co.receiver", CO[0], CO[1], 8, 0, 18, { wall: 0.7 });
  ringOf("co.neck", COF, 18, 21, 5.5, 8.4, { tone: "mid" });
  turned("co.shell", COF, [[21, 6], [44, 6]], { tone: "hi" }, { inner: Ln(G.arcOf(COF, 24, 6, P), { tone: "faint" }) });
  turned("co.shell", COF, [[44, 6], [66, 6]], { tone: "hi" }, { inner: Ln(G.arcOf(COF, 44.4, 6, P) + G.arcOf(COF, 63, 6, P), { tone: "faint" }) });
  for (const z of [26, 60]) boss("co.coolant", [CO[0] + 6 * Math.cos(2.2), CO[1] + 6 * Math.sin(2.2), z], [Math.cos(2.2), Math.sin(2.2), 0], 1.4, 3, { tone: "mid", ring: false });
  disc("co.lid", COF, 66, 69, 10.5, { tone: "hi" }, { bevel: 0.4, extra: Dots(G.dotsOf(COF, 69, 9.4, 8, P, { all: true, phase: 0.2 }), { size: 0.4, tone: "mid" }) });
  const CO_VAP = boss("co.vap.boss", [CO[0], CO[1], 69], UP, 4.5, 3);
  const VAC_AT = [CO[0] + 5.7, CO[1] - 5.7];
  const CO_VAC = boss("co.vac.boss", [VAC_AT[0], VAC_AT[1], 69], UP, 2, 3);
  pipe("vapour", [KE_VAP, [KE[0], KE[1], 100], [CO[0], CO[1], 100], CO_VAP], 2.8, { bands: [0.55] });
  const VP = { x: 196, y: -128, w: 26, d: 16, r: 1.5 };
  box("vac.box", [VP.x, VP.y, 0], [VP.x + VP.w, VP.y + VP.d, 12], { tone: "mid" }, { r: 1.5, steps: 3, bevel: 0.5, inner: Ln(k.sideSeam(VP, 3, P, 3), { tone: "faint" }), extra: Dots(k.corners(VP, 2.5).map(([x, y]) => at([x, y, 12])), { size: 0.4 }) });
  dial("vac", VP.x + 7, VP.y + 8, 12, 4.5, "vacuum");
  const VP_IN = boss("vac.in.boss", [VP.x + 13.5, VP.y + 8, 12], UP, 2, 2.5);
  motor("vac.motor", vert(VP.x + 20.5, VP.y + 8), 12, 22, 3.8);
  pipe("vacuum", [CO_VAC, [VAC_AT[0], VAC_AT[1], 84], [VP.x + 13.5, VP.y + 8, 84], VP_IN], 1.2, { flow: false });
}
const P2 = pump("pump2", KE[0], KEB.y + KEB.d + 16, { inlet: [0, -1, 0], outlet: [0, 1, 0] });
pipe("kettle-out", [KE_OUT, P2.inlet], 1.9);

// ---------- station 5: belt freezer ----------
const FZB = { y0: YF - 10, y1: YF + 10 };
const SLAB = { xPour: 176, xEnd: 90, xTunnel: 164, y: [YF - 6, YF + 6], z: 26, h: 1 };
let FZ_NOZ;
{
  for (const x of [94, 136, 176]) for (const y of [YF - 8.75, YF + 8.75]) post("fz.leg", x, y, [[1.2, 20]], 1.2);
  box("fz.rail", [84, FZB.y0, 20], [186, YF - 7.5, 28], { tone: "mid" });
  box("fz.rail", [84, YF + 7.5, 20], [186, FZB.y1, 28], { tone: "mid" });
  box("fz.bed", [90, YF - 7.5, 20], [180, YF + 7.5, 24], { tone: "lo" });
  box("fz.belt", [90, YF - 7, 24], [180, YF + 7, 26], { tone: "lo" }, { extra: Ln(Array.from({ length: 17 }, (_, i) => k.lineOnTop([94 + i * 5.2, YF - 6.5], [94 + i * 5.2, YF + 6.5], 26, P)).join(""), { tone: "faint" }) });
  for (const x of [87, 183]) disc("fz.roller", alongY([x, YF - 7.5, 23]), 0, 15, 3, { tone: "mid" });
  // the frozen slab grows along the belt while the concentrate pours, then is fed off the end (drawn live)
  put("slab", [133, YF, 26.5], `<g data-part="slab-wet" class="iso-solid ic-brew"></g><g data-part="slab-ice" class="iso-solid ic-ice"></g>`, [record(A.slab({ x: SLAB.xEnd, y: SLAB.y[0], w: SLAB.xPour - SLAB.xEnd, d: SLAB.y[1] - SLAB.y[0], r: 0.3 }, SLAB.z, SLAB.h, { name: "slab" }, 2))], { bias: 0.2 });
  // the tunnel: a cold hood over the middle of the belt, a chiller with fins and a fan on top
  const HOOD = { x: 112, y: FZB.y0, w: 52, d: 20, r: 2 };
  const win = [[118, FZB.y1 + 0.02, 33], [158, FZB.y1 + 0.02, 33], [158, FZB.y1 + 0.02, 46], [118, FZB.y1 + 0.02, 46]];
  box("fz.hood", [HOOD.x, HOOD.y, 28], [HOOD.x + HOOD.w, HOOD.y + HOOD.d, 52], { tone: "mid" }, { r: 2, steps: 3, bevel: 0.5, inner: Ln(k.sideSeam(HOOD, 30.5, P, 3), { tone: "faint" }), extra: Ln(path3(win, true) + path3([[120, FZB.y1 + 0.02, 44], [126, FZB.y1 + 0.02, 44]]), { tone: "lo", free: true }) });
  const CH = { x: 118, y: YF - 8, w: 40, d: 16, r: 1.5 };
  box("fz.chiller", [CH.x, CH.y, 52], [CH.x + CH.w, CH.y + CH.d, 62], { tone: "mid" }, { r: 1.5, steps: 3, bevel: 0.4, extra: Ln(Array.from({ length: 9 }, (_, i) => path3([[CH.x + 4 + i * 4, CH.y + CH.d + 0.02, 54], [CH.x + 4 + i * 4, CH.y + CH.d + 0.02, 60]])).join(""), { tone: "lo", free: true }) });
  ringOf("fz.fan.ring", vert(148, YF), 62, 64.5, 5.2, 6.5, { tone: "mid" });
  disc("fz.fan.hub", vert(148, YF), 62, 64, 1.6, { tone: "hi" }, { extra: `<g data-part="fz-fan"></g>` });
  SPINNERS.push({ part: "fz-fan", kind: "spokes", c: [148, YF, 64.1], u: [1, 0, 0], v: [0, 1, 0], r0: 1.8, r1: 5, n: 5, key: "beltShare", rate: 5 });
  dial("belt", 128, YF, 62, 4.5, "beltShare");
  // the pour arm over the belt's start: the concentrate line lands on top, a nozzle points down at the belt
  post("fz.post", 176, YF + 16, [[1.2, 32]], 2);
  box("fz.arm", [173, YF - 1, 32], [179, YF + 18, 36], { tone: "mid" });
  FZ_NOZ = boss("fz.noz.boss", [176, YF + 2, 36], UP, 3, 3);
  boss("fz.nozzle", [176, YF + 2, 32], [0, 0, -1], 2.2, 2.5, { tone: "mid", ring: false });
  stream("pour", [[176, YF + 2, 29.5], [176, YF + 2, 26.8]], "pouring", { count: 6, size: 0.55, speed: 1.6, jitter: 0.3 });
  stream("frost", [[113, YF - 9, 29], [104, YF - 12, 40], [96, YF - 10, 50]], "beltShare", { count: 10, size: 0.42, speed: 0.5, tone: "mist", jitter: 2 });
}
pipe("concentrate", [P2.outlet, [176, 50, 5], [176, 50, 54], [176, YF + 2, 54], FZ_NOZ], 1.9, { bands: [0.3, 0.62] });

// ---------- station 6: granulator and the climbing conveyor ----------
const GNB = { x: GN[0] - 12, y: GN[1] - 11, w: 24, d: 22, r: 1 };
const C5 = { A: [48, YF, 10], B: [-8, YF, 56] };
{
  for (const [dx, dy] of [[-9, -8], [9, -8], [-9, 8], [9, 8]]) post("gn.leg", GN[0] + dx, GN[1] + dy, [[1.2, 8]], 1.8);
  box("gn.housing", [GNB.x, GNB.y, 8], [GNB.x + GNB.w, GNB.y + GNB.d, 20], { tone: "mid" }, { r: 1, steps: 3, bevel: 0.5, inner: Ln(k.sideSeam(GNB, 14, P, 3), { tone: "faint" }), extra: Dots(k.corners(GNB, 2.5).map(([x, y]) => at([x, y, 20])), { size: 0.42 }) });
  turned("gn.hopper", vert(GN[0], GN[1]), [[20, 5], [24, 9]], { tone: "hi" }, { inner: Ln(G.arcOf(vert(GN[0], GN[1]), 22.5, 8.1, P, { slope: 4 / 4 }), { tone: "faint" }) });
  const FR = alongY([GN[0], GNB.y + GNB.d, 14]);
  disc("gn.rotor", FR, 0, 1.6, 5, { tone: "hi" }, { extra: `<g data-part="gn-rotor"></g>` + Ln(G.circleOf(FR, 1.6, 1.3, P, 16), { tone: "lo" }) });
  SPINNERS.push({ part: "gn-rotor", kind: "spokes", c: [GN[0], GNB.y + GNB.d + 1.65, 14], u: [1, 0, 0], v: [0, 0, 1], r0: 1.7, r1: 4.3, n: 8, key: "rotorTurning", rate: 4 });
  motor("gn.motor", G.frameAlong([GN[0], GNB.y, 14], [0, -1, 0]), 0, 9, 4.5);
  box("gn.chute", [50, GN[1] - 3, 9], [GNB.x, GN[1] + 3, 13], { tone: "lo" });
  stream("slab-in", [[91, YF, 27.5], [86, YF, 26.6], [80, YF, 22.5], [GN[0], GN[1], 15]], "rotorTurning", { count: 10, size: 0.7, speed: 0.9, tone: "icedots", jitter: 1.2 });
  // an inclined cleated belt lifts the granules to the dryer's loading port
  const a = G.unit3(G.sub3(C5.B, C5.A));
  const u = [0, -1, 0];
  const v = G.cross3(a, u);
  const L = G.len3(G.sub3(C5.B, C5.A));
  const F5 = G.frameOf(C5.A, a, u, v);
  const on = (s, t, w) => G.add3(G.add3(C5.A, G.mul3(a, s)), G.add3(G.mul3(u, t), G.mul3(v, w)));
  prism("c5.belt", F5, [[-7, -3], [7, -3], [7, 0], [-7, 0]], 0, L, { tone: "lo" }, { extra: Ln(Array.from({ length: 13 }, (_, i) => path3([on(5 + i * 5.2, -6.5, 0.02), on(5 + i * 5.2, 6.5, 0.02)])).join(""), { tone: "faint" }) });
  prism("c5.rail", F5, [[7, -3], [9.5, -3], [9.5, 2], [7, 2]], -1, L + 1, { tone: "mid" });
  prism("c5.rail", F5, [[-9.5, -3], [-7, -3], [-7, 2], [-9.5, 2]], -1, L + 1, { tone: "mid" });
  // pedestals whose tops lie in the belt's underside, so each is a full-face seat
  const under = (x) => C5.A[2] - 3 / Math.abs(v[2]) * 1 + (C5.A[0] - x) * (-a[2] / a[0]) * -1; // z of the belt's bottom plane at x, on the belt's centre line
  const zUnder = (x) => {
    // bottom plane: points A - 3 v + a s + u t; solve for z at this x (t = 0)
    const base = G.sub3(C5.A, G.mul3(v, 3));
    const s = (x - base[0]) / a[0];
    return base[2] + a[2] * s;
  };
  for (const [x0, x1] of [[34, 42], [4, 12]]) prism("c5.pedestal", alongY([0, YF - 4, 0]), [[x0, 0], [x1, 0], [x1, zUnder(x1)], [x0, zUnder(x0)]], 0, 8, { tone: "mid" });
  motor("c5.motor", G.frameAlong(on(L - 6, 9.5, -0.5), [0, -1, 0]), 0, 8, 3.2);
  stream("granules-out", [[50, YF, 11.5], [46, YF, 10.6], ...Array.from({ length: 12 }, (_, i) => on((L * (i + 1)) / 12, 0, 0.6)), [-12, YF, 54.5], [-16, YF, 50]], "granulesOut", { count: 34, size: 0.5, speed: 0.55, jitter: 1.4 });
}

// ---------- station 7: freeze dryer, ice condenser, vacuum pump ----------
const FD = { x: -80, y: 56, w: 70, d: 32, r: 1.5 };
const TRAYS = [];
let FD_PORT;
{
  box("fd.base", [FD.x + 3, FD.y + 3, 0], [FD.x + FD.w - 3, FD.y + FD.d - 3, 4], { tone: "lo" }, { r: 1 });
  box("fd.floor", [FD.x, FD.y, 4], [FD.x + FD.w, FD.y + FD.d, 7], { tone: "mid" }, { r: 1.5, steps: 3, bevel: 0.4 });
  box("fd.back", [FD.x, FD.y, 7], [FD.x + FD.w, FD.y + 2.5, 44], { tone: "mid" });
  box("fd.wall", [FD.x, FD.y + 2.5, 7], [FD.x + 2.5, FD.y + FD.d, 44], { tone: "mid" });
  box("fd.pillar", [FD.x + FD.w - 3, FD.y + FD.d - 3, 7], [FD.x + FD.w, FD.y + FD.d, 44], { tone: "mid" });
  for (let i = 0; i < 5; i++) {
    const z = 11 + i * 7;
    box("fd.shelf", [FD.x + 2.5, FD.y + 2.5, z], [FD.x + FD.w - 3, FD.y + FD.d - 3, z + 1.2], { tone: "mid" });
    const tray = { x0: FD.x + 6, x1: FD.x + FD.w - 6, y0: FD.y + 5, y1: FD.y + FD.d - 5, z: z + 1.2 };
    const trayBox = box("fd.tray", [tray.x0, tray.y0, tray.z], [tray.x1, tray.y1, tray.z + 1.2], { tone: "lo" }, { r: 0.5 });
    const top = tray.z + 1.2;
    TRAYS.push({ ...tray, z: top });
    // the granules on this tray, frosted then dry (drawn live), and the vapour leaving the top one
    const id = nameFor("fd.granules");
    put(id, [(tray.x0 + tray.x1) / 2, (tray.y0 + tray.y1) / 2, top + 0.4], `<g data-part="tray-ice-${i}" class="iso-dots ic-icedots"></g><g data-part="tray-dry-${i}" class="iso-dots ic-grain"></g>${i === 4 ? `<g data-part="sublime" class="iso-dots ic-mist"></g>` : ""}`, [record(A.box([tray.x0 + 1, tray.y0 + 1, top], [tray.x1 - 1, tray.y1 - 1, top + 0.8], { name: id, owner: trayBox.id }))], { bias: 0.2 });
  }
  // the glass sides: the front and the right, drawn as panes, recorded as thin boxes
  const pane = (name, min, max, shine) => {
    const [x0, y0, z0] = min;
    const [x1, y1, z1] = max;
    const face = x1 - x0 < 2 ? [[x1, y0, z0], [x1, y1, z0], [x1, y1, z1], [x1, y0, z1]] : [[x0, y1, z0], [x1, y1, z0], [x1, y1, z1], [x0, y1, z1]];
    const id = nameFor(name);
    put(id, [(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2], Ln(path3(face, true), { tone: "lo" }) + Ln(path3(shine), { tone: "faint" }), [record(A.box(min, max, { name: id }))], { bias: 0.35 });
  };
  pane("fd.glass.front", [FD.x + 2.5, FD.y + FD.d - 1, 7], [FD.x + FD.w - 3, FD.y + FD.d, 44], [[FD.x + 8, FD.y + FD.d, 40], [FD.x + 14, FD.y + FD.d, 40]]);
  pane("fd.glass.side", [FD.x + FD.w - 1, FD.y + 2.5, 7], [FD.x + FD.w, FD.y + FD.d - 3, 44], [[FD.x + FD.w, FD.y + 6, 40], [FD.x + FD.w, FD.y + 10, 40]]);
  box("fd.top", [FD.x, FD.y, 44], [FD.x + FD.w, FD.y + FD.d, 48], { tone: "mid" }, { r: 1.5, steps: 3, bevel: 0.5, inner: Ln(k.sideSeam(FD, 46, P, 3), { tone: "faint" }), extra: Dots(k.corners(FD, 3).map(([x, y]) => at([x, y, 48])), { size: 0.42 }) });
  turned("fd.port", vert(-16, YF), [[48, 3], [54, 7]], { tone: "mid" });
  dial("dry", FD.x + 14, FD.y + FD.d - 8, 48, 4.5, "dryVac");
  FD_PORT = boss("fd.vac.boss", [-44, 66, 48], UP, 3, 5);
  // the ice condenser: a tall glass vessel where the vapour freezes back to ice
  const CDF = vert(CD[0], CD[1]);
  disc("cd.foot", CDF, 0, 1.6, 12, { tone: "lo" });
  level("ice", CD[0], CD[1], 10.2, 2, 48, "ic-ice", "dried", { tone: "faint" });
  glassCyl("cd.glass", CD[0], CD[1], 11, 1.6, 52, { wall: 0.8 });
  disc("cd.lid", CDF, 52, 55, 12, { tone: "hi" }, { bevel: 0.4, extra: Dots(G.dotsOf(CDF, 55, 10.8, 8, P, { all: true, phase: 0.2 }), { size: 0.4, tone: "mid" }) });
  const CD_TOP = boss("cd.vap.boss", [CD[0], CD[1], 55], UP, 3, 12);
  elbowDuct("fd-duct", FD_PORT, UP, 3, CD_TOP, UP, 3, 4.2, { ballR: 4.2 * 1.7, owners: ["fd.vac.boss", "cd.vap.boss"] });
  const CD_VAC = boss("cd.vac.boss", [CD[0] - 7.5, CD[1] + 7.5, 55], UP, 2, 6, { tone: "mid" });
  // the vacuum pump beyond it, drawing through the condenser so only dry vapour reaches it
  const DP = { x: -140, y: 100, w: 24, d: 14, r: 1.5 };
  box("dp.block", [DP.x, DP.y, 0], [DP.x + DP.w, DP.y + DP.d, 12], { tone: "mid" }, { r: 1.5, steps: 3, bevel: 0.5, inner: Ln(k.sideSeam(DP, 3, P, 3), { tone: "faint" }), extra: Dots(k.corners(DP, 2.5).map(([x, y]) => at([x, y, 12])), { size: 0.4 }) });
  const DP_IN = boss("dp.in.boss", [DP.x + 6, DP.y + 7, 12], UP, 2, 2.5);
  motor("dp.motor", vert(DP.x + 17, DP.y + 7), 12, 22, 3.8);
  pipe("fd-vac", [CD_VAC, [CD[0] - 7.5, CD[1] + 7.5, 72], [DP.x + 6, DP.y + 7, 72], DP_IN], 1.2, { flow: false });
  // the outlet: dry granules leave through a chute at the bottom of the chamber to the packing elevator
  box("fd.chute", [E3X + 4, YF - 3, 8], [FD.x, YF + 3, 12], { tone: "lo" });
  stream("pack-a", [[FD.x - 0.5, YF, 10.5], [E3X + 4, YF, 10.5]], "packIn", { count: 10, size: 0.45 });
}

// ---------- station 8: elevator, screw, filler, jars ----------
const JAR = { r: 6.5, z: [6, 24] };
const CV = { x: -202, y: YF - 9, w: 76, d: 18, r: 1 };
{
  box("lift3.body", [E3X - 4, YF - 6, 0], [E3X + 4, YF + 6, 84], { tone: "mid" }, { bevel: 0.3, inner: Ln(k.sideSeam({ x: E3X - 4, y: YF - 6, w: 8, d: 12, r: 0.6 }, 42, P, 2), { tone: "faint" }) });
  box("lift3.head", [E3X - 8, YF - 5, 84], [E3X + 4, YF + 5, 94], { tone: "mid" }, { bevel: 0.3 });
  motor("lift3.motor", vert(E3X - 2, YF), 94, 101, 3.5);
  const SC = G.frameOf([E3X - 8, YF, 89], [-1, 0, 0], [0, 0, 1], [0, 1, 0]);
  turned("fl.screw", SC, [[0, 4.5], [58, 4.5]], { tone: "hi" }, { inner: Ln([16, 36].map((s) => G.arcOf(SC, s, 4.5, P)).join(""), { tone: "faint" }) });
  disc("fl.screw.cap", SC, 58, 60, 5, { tone: "mid" });
  disc("fl.spout", vert(FL[0], FL[1]), 80.5, 84.5, 2, { tone: "lo" });
  // the filler on a gantry over the jar line
  for (const y of [YF - 16, YF + 16]) post("fl.post", FL[0], y, [[1.2, 56]], 2);
  box("fl.bar", [FL[0] - 4, YF - 18, 56], [FL[0] + 4, YF + 18, 60], { tone: "mid" });
  const FLF = vert(FL[0], FL[1]);
  turned("fl.body", FLF, [[60, 6], [72, 6]], { tone: "hi" }, { inner: Ln(G.arcOf(FLF, 66, 6, P), { tone: "faint" }) });
  turned("fl.hopper", FLF, [[72, 5], [80, 10]], { tone: "hi" }, { inner: Ln(G.arcOf(FLF, 77, 8.1, P, { slope: 5 / 8 }), { tone: "faint" }) });
  turned("fl.nozzle", FLF, [[44, 2.5], [56, 4]], { tone: "mid" });
  knob("fl.knob", [FL[0] + 4, YF + 10, 58], [1, 0, 0], 1.6, 2);
  stream("pack-b", [[FL[0], FL[1], 44], [FL[0], FL[1], 25]], "packIn", { count: 7, size: 0.45, speed: 1.4, jitter: 0.4 });
  // the jar conveyor with three jars: one waiting, one filling, one capped
  box("cv.bed", [CV.x, CV.y, 0], [CV.x + CV.w, CV.y + CV.d, 6], { tone: "mid" }, { r: 1, steps: 3, bevel: 0.4, inner: Ln(k.sideSeam(CV, 3, P, 3), { tone: "faint" }) });
  box("cv.rail", [CV.x, CV.y - 2, 6], [CV.x + CV.w, CV.y, 9], { tone: "lo" });
  box("cv.rail", [CV.x, CV.y + CV.d, 6], [CV.x + CV.w, CV.y + CV.d + 2, 9], { tone: "lo" });
  for (const [i, x] of JARS.entries()) {
    const which = ["full", "fill", "empty"][i];
    if (which === "full") level("jar-full", x, YF, JAR.r - 0.7, JAR.z[0] + 0.6, JAR.z[1] - 2, "ic-powder", "one", { tone: "hi" });
    if (which === "fill") level("jar", x, YF, JAR.r - 0.7, JAR.z[0] + 0.6, JAR.z[1] - 2, "ic-powder", "jar", { tone: "hi" });
    glassCyl("jar.glass", x, YF, JAR.r, JAR.z[0], JAR.z[1], { wall: 0.6 });
    if (which !== "empty") {
      const F = vert(x, YF);
      const live = which === "fill";
      const id = nameFor(live ? "jar.lid.live" : "jar.lid");
      const svg = S(G.disc(JAR.z[1], JAR.z[1] + 2.5, JAR.r + 0.5, F, P, { bevel: 0.4 }), { tone: "hi" }) + Faded(G.ribsOf(F, JAR.z[1], JAR.z[1] + 2.5, JAR.r + 0.5, 30, P, { fade: [0.1, 0.55], seams: true }), { tone: "lo" });
      put(id, [x, YF, JAR.z[1] + 1.25], live ? `<g data-part="lid-live">${svg}</g>` : svg, [record(A.disc(F, JAR.z[1], JAR.z[1] + 2.5, JAR.r + 0.5, { name: id }))], { bias: 0.1 });
    }
  }
  // the capper over the finished jar
  post("cap.post", JARS[0], YF + 16, [[1.2, 40]], 2);
  box("cap.arm", [JARS[0] - 3, YF - 1, 40], [JARS[0] + 3, YF + 18, 44], { tone: "mid" });
  disc("cap.head", vert(JARS[0], YF), 34, 40, 7.5, { tone: "hi" }, { extra: Faded(G.ribsOf(vert(JARS[0], YF), 34, 40, 7.5, 30, P, { fade: [0.1, 0.55], seams: true }), { tone: "lo" }) });
}

// ---------- controls ----------
function lamp(name, p, id) {
  put(nameFor(name), p, `<g class="iso-dots ic-lamp" data-lamp="${id}">${Dots([at(p)], { size: 0.7, tone: "hi" }).replace(/<g[^>]*>|<\/g>/g, "")}</g>`, [record(A.ball(p, 0.5, { name }))], { bias: 0.3 });
}
const CB = { x: 196, y: 100, w: 32, d: 16, r: 1.5 };
box("ctl.box", [CB.x, CB.y, 0], [CB.x + CB.w, CB.y + CB.d, 16], { tone: "mid" }, {
  r: 1.5, steps: 3, bevel: 0.6,
  inner: Ln(k.sideSeam(CB, 12, P, 3), { tone: "faint" }),
  extra: Dots(k.corners(CB, 2.5).map(([x, y]) => at([x, y, 16])), { size: 0.4 }) + Ln(k.planOutline({ x: CB.x + 3, y: CB.y + 3, w: 12, d: 10, r: 1 }, 16, P, 2), { tone: "faint" }),
});
knob("ctl.knob", [CB.x + 6, CB.y + CB.d, 6], [0, 1, 0], 2.4, 2.5);
knob("ctl.knob", [CB.x + 15, CB.y + CB.d, 6], [0, 1, 0], 2.4, 2.5);
{
  const sw = [CB.x + 26, CB.y + CB.d, 6];
  const F = G.frameAlong(sw, [0, 1, 0]);
  disc("ctl.switch.ring", F, 0, 1, 1.6, { tone: "lo" });
  put("ctl.switch.lever", G.add3(sw, [0, 1.6, 0]), Ln(path3([G.add3(sw, [0, 1, 0]), G.add3(sw, [0, 3.2, 1.8])]), { tone: "hi", free: "end" }), [record(A.disc(F, 1, 3.4, 0.4, { name: "ctl.switch.lever" }))], { bias: 0.3 });
}
for (let i = 1; i <= 8; i++) lamp("ctl.lamp", [CB.x + 3.5 + (i - 1) * 3.6, CB.y + CB.d + 0.02, 12.5], `s${i}`);

// ---------- order, page ----------
A.settle(R, P);
R.items.sort((a, b) => a.key - b.key);
const STATION_OF = [
  [1, /^(silo\.|roaster\.|cooler\.|beans-|roast$)/],
  [2, /^(lift1\.|mill\.|lift2\.|screw\.|grind-in|grounds-)/],
  [3, /^(ex\.|boiler\.|pump1\.|water|extract-a|sump|bed|therm)/],
  [4, /^(ke\.|co\.|vac\.|pump2\.|extract-b|vapour|vacuum|kettle|condensate)/],
  [5, /^(fz\.|concentrate|pour|slab$|frost|belt$)/],
  [6, /^(gn\.|c5\.|slab-in|granules-out)/],
  [7, /^(fd\.|fd-|cd\.|dp\.|ice|dry$|pack-a)/],
  [8, /^(lift3\.|fl\.|jar|cv\.|cap\.|pack-b)/],
];
const stationOf = (name) => STATION_OF.find(([, re]) => re.test(name))?.[0] ?? 0;
const groups = R.items.map((item) => `<g class="it" data-name="${item.name}" data-station="${stationOf(item.name)}"${item.attrs ?? ""}>${item.svg}</g>`);

const B = M.balance();
const g = (v) => Math.round(v);
const LABEL_TEXT =
  `A pilot instant coffee line on one floor plate, back row left to right: a silo of green beans feeding a drum roaster with a chimney and a cooling tray; a bucket elevator to a roller mill and a second elevator with a screw conveyor to a glass extraction column fed with hot water from a boiler; a pump to a vacuum kettle with a glass dome, a sight glass, a condenser and a vacuum pump. Front row right to left: a belt freezer with a cold tunnel where the concentrate freezes into a slab; a granulator that breaks the slab, and a climbing belt to a freeze dryer shown with glass sides and five trays, a tall glass ice condenser and a vacuum pump; an elevator and screw to a filler over a jar conveyor with a capper. One batch of ${g(M.BATCH.green)} g of green coffee ends as ${g(B.powder)} g of instant coffee.`;
const svg = k.figureSvg({ width: W, height: H, label: LABEL_TEXT, body: [...back, `<g class="ic-line">${groups.join("")}</g>`] });

// Camera boxes in viewBox units: the screen box of a world box, padded, widened to the frame's aspect.
const ASPECT = VIDEO ? FRAME[0] / FRAME[1] : W / H;
function camOf(points, pad = 10) {
  const ps = points.map(at);
  let x0 = Math.min(...ps.map((p) => p[0])) - pad;
  let y0 = Math.min(...ps.map((p) => p[1])) - pad;
  let x1 = Math.max(...ps.map((p) => p[0])) + pad;
  let y1 = Math.max(...ps.map((p) => p[1])) + pad;
  y1 += (y1 - y0) * (VIDEO ? 0.3 : 0);
  let w = x1 - x0;
  let h = y1 - y0;
  if (w / h < ASPECT) {
    const nw = h * ASPECT;
    x0 -= (nw - w) / 2;
    w = nw;
  } else {
    const nh = w / ASPECT;
    y0 -= (nh - h) / 2;
    h = nh;
  }
  return [x0, y0, w, h].map(f2);
}
const camBox = ([x0, x1], [y0, y1], [z0, z1], pad) => camOf(k.boxCorners({ x: x0, y: y0, w: x1 - x0, d: y1 - y0 }, z0, z1), pad);
const CAMS = {
  wide: camOf([...k.boxCorners(PLATE, -PLATE_H - FOOT_H, 0), [SI[0], SI[1], 146], [E2[0], E2[1], 120], [KE[0], KE[1], 104], [CO[0], CO[1], 72]], 8),
  roast: camBox([-220, -46], [-98, -52], [-4, 146], 6),
  grind: camBox([-62, 96], [-100, -56], [-4, 124], 6),
  extract: camBox([54, 136], [-122, -50], [-4, 122], 6),
  concentrate: camBox([144, 232], [-136, -20], [-4, 106], 6),
  freeze: camBox([80, 192], [42, 100], [-4, 70], 6),
  granulate: camBox([-14, 96], [48, 96], [-4, 66], 6),
  dry: camBox([-144, -2], [50, 118], [-4, 84], 6),
  pack: camBox([-208, -94], [48, 96], [-4, 104], 6),
};
const SHOTS = [
  { dur: 4.5, cam: "wide", s: [0, 0], focus: 0, title: "How instant coffee is made", sub: `One batch: ${g(M.BATCH.green)} g of green coffee, from the silo to the jar` },
  { dur: 9, cam: "roast", s: [0, 1], focus: 1, title: "1 · Roasting", sub: `Green beans tumble in a drum at ${M.PLANT.roastC} °C for about ${M.PLANT.roastMinutes} minutes. They lose ${g(B.roastLoss)} g of water and turn brown` },
  { dur: 8, cam: "grind", s: [1, 2], focus: 2, title: "2 · Grinding", sub: `The roasted beans are cracked into a coarse ${M.PLANT.grindMm} mm grind, so hot water can reach the flavour` },
  { dur: 9, cam: "extract", s: [2, 3], focus: 3, title: "3 · Extraction", sub: `Water at ${M.PLANT.waterC} °C under pressure dissolves ${g(M.BATCH.yield * 100)} % of the grounds: ${g(B.extract)} g of strong brew at ${g(M.BATCH.extractSolids * 100)} % solids` },
  { dur: 9, cam: "concentrate", s: [3, 4], focus: 4, title: "4 · Concentration", sub: `Under vacuum the brew boils at only ${M.PLANT.kettleC} °C: ${g(B.evaporated)} g of water leave through the condenser. Now ${g(M.BATCH.concSolids * 100)} % solids` },
  { dur: 9, cam: "freeze", s: [4, 5], focus: 5, title: "5 · Freezing", sub: `The concentrate is poured on a belt at ${M.PLANT.beltC} °C and freezes into a solid slab` },
  { dur: 8, cam: "granulate", s: [5, 6], focus: 6, title: "6 · Granulating", sub: `The frozen slab is broken into ${M.PLANT.granuleMm} mm granules and spread on trays, still frozen` },
  { dur: 9, cam: "dry", s: [6, 7], focus: 7, title: "7 · Freeze drying", sub: `At ${M.PLANT.dryMbar} mbar the ice turns straight into vapour without melting: ${g(B.ice)} g of ice leave, the aroma stays` },
  { dur: 8, cam: "pack", s: [7, 8], focus: 8, title: "8 · Packing", sub: `The dry granules go into jars at ${g((1 - M.BATCH.powderSolids) * 100)} % moisture: ${g(B.powder)} g of instant coffee` },
  { dur: 6, cam: "wide", s: [8, 9], focus: 0, title: `${g(B.powder)} g of instant coffee · about ${g(B.cups)} cups`, sub: "Nothing added: brewed coffee with the water taken out, frozen and dried" },
  { dur: 2.2, cam: "wide", s: [9, 0], focus: 0, title: "", sub: "" },
];
const DATA = {
  cams: CAMS,
  shots: VIDEO ? SHOTS.map((shot) => ({ ...shot, cam: CAMS[shot.cam] })) : null,
  P,
  view: V,
  last: M.LAST,
  dials: DIALS,
  levels: LEVELS,
  streams: STREAMS,
  spinners: SPINNERS,
  slab: SLAB,
  trays: TRAYS,
  chamber: { x: [FD.x + 8, FD.x + FD.w - 8], y: [FD.y + 6, FD.y + FD.d - 6], z: [14, 46], port: [-44, 66, 50] },
  sight: LEVELS.find((l) => l.part === "kettle"),
  routes: Object.keys(ROUTES),
};
const CSS = readFileSync(join(HERE, "coffee.css"), "utf8");
const modelScript = readFileSync(join(HERE, "model.mjs"), "utf8").replace(/^export /gm, "");
const LIVE = readFileSync(join(HERE, "live.js"), "utf8").replace("__DATA__", JSON.stringify(DATA));

const body =
  `<style>${CSS}</style>` +
  k.plateHtml({
    fig: "Fig 1",
    title: "Instant coffee line",
    hint: "Hover to run the batch · ← →",
    readout: M.stateAt(0).readout,
    keys: [
      { mark: "lit", label: "The coffee on its way: beans, grounds, brew, frozen slab, granules" },
      { mark: "raised", label: "Glass: the column, the kettle's dome and sight glass, the dryer's sides, the ice condenser, the jars" },
      { mark: "edge", label: "Pipes carrying the batch, marked while that line runs" },
    ],
    caption: `Instant coffee is brewed coffee with the water taken back out. ${g(M.BATCH.green)} g of green beans lose ${g(B.roastLoss)} g in the roaster at ${M.PLANT.roastC} °C, are ground to ${M.PLANT.grindMm} mm, and give up ${g(B.solids)} g of soluble solids to water at ${M.PLANT.waterC} °C in the column: ${g(B.extract)} g of extract at ${g(M.BATCH.extractSolids * 100)} % solids. The kettle boils off ${g(B.evaporated)} g of that water under vacuum at about ${M.PLANT.kettleC} °C, so the flavour is not cooked. The ${g(B.concentrate)} g of concentrate freeze on a belt at ${M.PLANT.beltC} °C, the slab is broken into ${M.PLANT.granuleMm} mm granules, and in the freeze dryer at ${M.PLANT.dryMbar} mbar the ${g(B.ice)} g of ice sublimate straight to vapour, which the condenser catches as frost. ${g(B.powder)} g of dry granules go into the jar: about ${g(B.cups)} cups.`,
    body: `<div class="iso-stage ic-stage" tabindex="0" role="slider" aria-label="Instant coffee line. Move the pointer across the plant, or use the left and right arrow keys, to run one batch through roasting, grinding, extraction, concentration, freezing, granulating, freeze drying and packing." aria-valuemin="0" aria-valuemax="${M.LAST}" aria-valuenow="0" aria-valuetext="ready">${svg}<span class="ic-sr" role="status" aria-live="polite" data-status></span></div>`,
  });

let page;
let name;
if (VIDEO) {
  const [FW, FH] = FRAME;
  const VIDEO_CSS = `
.iso-page{width:${FW}px;margin:0}
body{background:var(--anatomy-page)}
.iso{--anatomy-page:#0e0e0e;--anatomy-card:#0e0e0e;--anatomy-paper:#0e0e0e;--anatomy-face:#1c1c1c;--anatomy-top:#252525;--anatomy-shade-0:#0b0b0b;--anatomy-shade-1:#121212;--anatomy-shade-2:#181818;--anatomy-shade-3:#1f1f1f;--anatomy-lit-top:#303030;--anatomy-lit-shade:#242424;--anatomy-hi:#f2f2f2;--anatomy-mid:#a6a6a6;--anatomy-lo:#616161;--anatomy-faint:#3a3a3a;--anatomy-weight:.85px;--anatomy-dot:#f0f0f0;--anatomy-strong:#f2f2f2}
.iso[data-theme="light"]{--anatomy-page:#fbfbf9;--anatomy-card:#fbfbf9;--anatomy-paper:#fbfbf9;--anatomy-face:#ffffff;--anatomy-top:#ffffff;--anatomy-hi:#151517;--anatomy-mid:#66666b;--anatomy-lo:#9a9a9f;--anatomy-faint:#cfcfd2;--anatomy-weight:.85px;--anatomy-shade-0:#d2d2cf;--anatomy-shade-1:#ddddda;--anatomy-shade-2:#e8e8e5;--anatomy-shade-3:#f2f2ef;--anatomy-dot:#2a2a2e;--anatomy-strong:#151517}
.ic-frame{width:${FW}px;height:${FH}px;position:relative;overflow:hidden}
.ic-frame .ic-stage{position:absolute;inset:0}
.ic-frame .iso-svg{width:${FW}px;height:${FH}px;margin:0}
.ic-shade{position:absolute;left:0;right:0;bottom:0;height:${Math.round(FH * 0.34)}px;background:linear-gradient(to bottom,transparent,var(--anatomy-page) 78%);pointer-events:none}
.ic-caption{position:absolute;left:${Math.round(FW * 0.045)}px;right:${Math.round(FW * 0.045)}px;bottom:${Math.round(FH * 0.075)}px;max-width:${Math.round(Math.min(FW * 0.72, 1180))}px;pointer-events:none}
.ic-title{font:600 ${Math.round(Math.min(FW, FH) * 0.044)}px/1.15 ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;color:var(--anatomy-strong);letter-spacing:-.01em;opacity:0}
.ic-sub{font:400 ${Math.round(Math.min(FW, FH) * 0.027)}px/1.35 ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;color:var(--anatomy-text);margin-top:${Math.round(Math.min(FW, FH) * 0.012)}px;opacity:0}
.iso[data-theme="light"] .ic-sub{color:#4a4a4e}
.ic-readout{position:absolute;right:${Math.round(FW * 0.045)}px;top:${Math.round(FH * 0.05)}px;padding:${Math.round(Math.min(FW, FH) * 0.011)}px ${Math.round(Math.min(FW, FH) * 0.016)}px;border-radius:6px;background:color-mix(in srgb,var(--anatomy-page) 82%,transparent);font-family:var(--anatomy-mono);font-size:${Math.round(Math.min(FW, FH) * 0.02)}px;line-height:1;letter-spacing:.03em;color:var(--anatomy-text);font-variant-numeric:tabular-nums;white-space:nowrap}
`;
  const frameBody = `<style>${CSS}${VIDEO_CSS}</style><div class="ic-frame"><div class="iso-stage ic-stage" tabindex="0" role="slider" aria-label="Instant coffee line" aria-valuemin="0" aria-valuemax="${M.LAST}" aria-valuenow="0" aria-valuetext="ready">${svg}<span class="ic-sr" role="status" aria-live="polite" data-status></span></div><div class="ic-shade"></div><div class="ic-caption"><div class="ic-title" data-title></div><div class="ic-sub" data-sub></div></div><div class="ic-readout" data-readout>${M.stateAt(0).readout}</div></div>`;
  page = k.pageHtml({ title: "Instant coffee line (video)", theme: THEME, body: frameBody, script: kitScript() + modelScript + LIVE, width: FW });
  name = `instant-coffee-video${THEME === "light" ? "-light" : ""}${FW === 1920 && FH === 1080 ? "" : `-${FW}x${FH}`}.html`;
} else {
  page = k.pageHtml({ title: "Instant coffee line", theme: THEME, body, script: kitScript() + modelScript + LIVE, width: 650 });
  name = THEME === "light" ? "instant-coffee-light.html" : "instant-coffee.html";
}
writeFileSync(join(HERE, name), page);
console.log("wrote", name, `${(page.length / 1024).toFixed(0)} KB`, `${R.items.length} items`, `${R.solids.length} solids`, `${R.tubes.length} tubes`, `scale ${KS.toFixed(3)}`);

// Contents drawn inside glass are ordered after the glass by choice; a duct whose rim sits on an elbow ball is drawn after the ball.
const SEE_THROUGH = [
  ["kettle", "ke.sight"], ["condensate", "co.receiver"], ["sump", "ex.glass"], ["bed", "ex.glass"], ["water", "ex.glass"], ["ex.plate", "ex.glass"],
  ["ice", "cd.glass"], ["jar-full", "jar.glass"], ["jar", "jar.glass#2"],
  ["fd.granules*", "fd.glass.front"], ["fd.granules*", "fd.glass.side"], ["fd.tray*", "fd.glass.front"], ["fd.tray*", "fd.glass.side"], ["fd.shelf*", "fd.glass.front"], ["fd.shelf*", "fd.glass.side"],
];
// Rings that wrap a part interlock with it on screen (the silo's ring around its cone, the cooler's rim around the arm); live overlays ride on their host.
const WRAPPED = [["silo.cone", "silo.ring"], ["roaster.vanes", "roaster.drum"], ["cooler.arm", "cooler.rim"], ["cooler.arm", "cooler.hub"]];
A.auditOrExit(R, P, { allow: [...SEE_THROUGH, ...WRAPPED, ["fd-duct*", "fd-duct.elbow"], ["fd-duct*", "fd-duct.elbow#2"]], crowd: [["water*", "ex.glass"]] });
