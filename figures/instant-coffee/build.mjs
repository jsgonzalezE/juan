// Instant coffee line: a bench-top pilot plant that brews, concentrates and spray-dries one batch.
// node build.mjs [--light] [--audit]
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
// --video: a frame for the video edit, --frame=WxH (default 1920x1080): bigger figure, stronger inks, a large readout and nothing else.
const VIDEO = process.argv.includes("--video");
const FRAME = (process.argv.find((a) => a.startsWith("--frame=")) ?? "--frame=1920x1080").slice(8).split("x").map(Number);
const KIT = join(HERE, "..", "..", ".claude", "skills", "anatomy");

const W = VIDEO && FRAME[1] > FRAME[0] ? 450 : 600; // a tall frame gets a tighter viewBox so the figure fills its width
const H = 440;
const PLATE = { x: -162, y: -48, w: 324, d: 96, r: 8 };
const PLATE_H = 12;
const FOOT_H = 5;

// Stations
const EX = [-112, 0]; // extraction column
const BO = [-112, -32]; // hot-water boiler
const KE = [-20, 0]; // vacuum kettle
const CO = [22, -12]; // condenser over its receiver
const DR = [90, 0]; // spray-drying chamber
const HT = [77, -39]; // air heater behind the chamber
const CY = [134, -18]; // cyclone
const TOP_FEED = 164;

const P = k.fitProjection(
  [...k.boxCorners(PLATE, -PLATE_H - FOOT_H, 0), [DR[0], DR[1], 146], [150, -40, TOP_FEED], [90, 0, TOP_FEED], [BO[0], BO[1], 114], [CY[0] + 5, CY[1], 88], [HT[0], HT[1], 140], [92, -34, 142]],
  W,
  H,
  { pad: 26, azimuth: 38, elevation: 30 },
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
// A boss on a flat face: a short disc along the face's outward normal. Returns its outer face point.
function boss(name, centre, outward, r, length, { tone = "hi", bias = 0.1, ring = true, owner } = {}) {
  const F = G.frameAlong(centre, outward);
  const id = nameFor(name);
  put(id, G.add3(centre, G.mul3(F.a, length / 2)), S(G.disc(0, length, r, F, P), { tone }) + (ring && G.dot3(F.a, V) > 0.15 ? Ln(G.circleOf(F, length, r * 0.55, P, 16), { tone: "faint" }) : ""), [record(A.disc(F, 0, length, r, { name: id, owner }))], { bias });
  return G.add3(centre, G.mul3(F.a, length));
}
// A saddle pad on a curved host, as in the Raptor: a cylinder whose base follows the host's surface.
function padOn(name, host, point, outward, a, h, { tone = "hi", bias = 0.1, owner, ring = false } = {}) {
  const hosts = [host].flat();
  const inside = (p) => hosts.some((shape) => A.sdf(shape, p) < 0);
  const axis = G.unit3(outward);
  const F = G.frameAlong(point, axis);
  const start = (angle) => {
    let lo = -2.5 * a;
    let hi = h;
    if (!inside(G.pointOf(F, lo, a, angle))) return 0;
    for (let step = 0; step < 40; step++) {
      const mid = (lo + hi) / 2;
      if (inside(G.pointOf(F, mid, a, angle))) lo = mid;
      else hi = mid;
    }
    return hi;
  };
  const low = Math.min(...Array.from({ length: 48 }, (_, index) => start((index / 48) * Math.PI * 2)));
  const id = nameFor(name);
  const face = ring && G.dot3(axis, V) > 0.15 ? Ln(G.circleOf(F, h, a * 0.55, P, 16), { tone: "faint" }) : "";
  put(id, G.add3(point, G.mul3(axis, h / 2)), S(G.saddleOf(F, a, start, h, P), { tone }) + face, [record(A.disc(F, low - 0.05, h, a, { name: id, owner, seated: true, cut: hosts }))], { bias });
  return G.add3(point, G.mul3(axis, h));
}
function elbow(name, face, normal, faceR, toward, ballR, rim, { owner } = {}) {
  const centre = G.add3(face, G.mul3(normal, Math.sqrt(ballR ** 2 - faceR ** 2)));
  ball(name, centre, ballR, { tone: "hi" }, { owner });
  const axis = G.unit3(G.sub3(toward, centre));
  return G.add3(centre, G.mul3(axis, Math.sqrt(ballR ** 2 - rim ** 2)));
}
function flangeAt(name, centre, axis, r, thick, { bolts = 0, tone = "hi", bias = 0, owner } = {}) {
  const F = G.frameAlong(centre, axis);
  const id = nameFor(name);
  const towards = G.dot3(F.a, V) > 0 ? thick / 2 : -thick / 2;
  const dots = Math.abs(G.dot3(F.a, V)) > 0.12 && bolts ? Dots(G.dotsOf(F, towards, r * 0.74, bolts, P, { all: true }), { size: 0.4, tone: "mid" }) : "";
  put(id, centre, S(G.disc(-thick / 2, thick / 2, r, F, P), { tone }) + dots, [record(A.disc(F, -thick / 2, thick / 2, r, { name: id, owner }))], { bias });
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

// ---------- helpers: glass and live parts ----------
const LIGHT = G.lightOf(P);
const SHINE_ANGLE = (95 * Math.PI) / 180;
function glassCyl(name, cx, cy, r, z0, z1, { wall = 0.7, bias = 0.3, extra = "", tone = "lo", solid = false } = {}) {
  const F = vert(cx, cy);
  const paths = k.cylinder(cx, cy, r, z0, z1 - z0, P, 64);
  const sx = cx + (r - 0.01) * Math.cos(SHINE_ANGLE);
  const sy = cy + (r - 0.01) * Math.sin(SHINE_ANGLE);
  const svg = [
    Ln(paths.outline, { tone }),
    Ln(k.sideArc(cx, cy, r, z0, P, 48), { tone }),
    Ln(k.ring(cx, cy, r, z1, P, 64), { tone }),
    Ln(k.rise([sx, sy], z0, z1, P), { tone: "faint" }),
    extra,
  ].join("");
  const id = nameFor(name);
  const shape = record(solid ? A.cylinder(cx, cy, r, z0, z1 - z0, { name: id }) : A.ring(F, z0, z1, r - wall, r, { name: id }));
  put(id, [cx, cy, (z0 + z1) / 2], svg, [shape], { bias });
  return shape;
}
// A glass body of revolution (cone, dome) drawn as its silhouette; recorded as a thin shell.
function glassLathe(name, F, outer, { wall = 0.7, bias = 0.3, extra = "", ref, tone = "lo" } = {}) {
  const closed = [[outer[0][0], 0], ...outer, [outer[outer.length - 1][0], 0]];
  const out = G.outlineOf(closed, F, P, { rims: "all" });
  const inner = [...outer].reverse().map(([s, r]) => [s, Math.max(0.2, r - wall)]);
  const meridian = [...outer.map(([s, r]) => [s, r]), ...inner];
  const id = nameFor(name);
  const mid = (outer[0][0] + outer[outer.length - 1][0]) / 2;
  put(id, ref ?? G.add3(F.o, G.mul3(F.a, mid)), Ln(out.outline, { tone }) + extra, [record(A.lathe(F, meridian, { name: id }))], { bias });
}
// A liquid or powder level inside a vessel: drawn full here, rebuilt by the page as the level moves.
function level(name, cx, cy, r, z0, zMax, cls, { tone = "lo", bias = 0.1, extra = "" } = {}) {
  const svg = `<g data-part="${name}" class="iso-solid ${cls}">${S(k.cylinder(cx, cy, r, z0, zMax - z0, P, 48), { tone, crease: "none" })}</g>${extra}`;
  const id = nameFor(name);
  put(id, [cx, cy, (z0 + zMax) / 2], svg, [record(A.cylinder(cx, cy, r, z0, zMax - z0, { name: id }))], { bias });
}
const DIALS = [];
function dial(name, cx, cy, z, Rr, { count = 40, every = 5, from = (-135 * Math.PI) / 180, span = (270 * Math.PI) / 180, bias = 0.2 } = {}) {
  const top = z + 3;
  const ticks = k.radialTicks(cx, cy, Rr - 1.6, count, every, top, [0.7, 1.3], P, from, span);
  const needle = (value) => {
    const a = from + span * value;
    return k.lineOnTop([cx - Math.sin(a) * 1.2, cy + Math.cos(a) * 1.2], [cx + Math.sin(a) * (Rr - 1.9), cy - Math.cos(a) * (Rr - 1.9)], top + 0.2, P);
  };
  const svg = [
    S(k.cylinder(cx, cy, Rr, z, 3, P, 48, 0.4), { tone: "hi", crease: "lo" }),
    Ln(k.knurl(cx, cy, Rr, top - 1.2, top, 44, P, 0.3), { tone: "lo" }),
    Ln(k.sideArc(cx, cy, Rr, top - 1.2, P, 32), { tone: "faint" }),
    Ln(k.ring(cx, cy, Rr - 1, top, P, 48), { tone: "lo" }),
    Ln(ticks.minor, { tone: "lo" }),
    Ln(ticks.major, { tone: "mid" }),
    `<path data-part="${name}" class="iso-line" data-tone="hi" data-free="" d="${needle(0)}" style="stroke-width:0.9px"/>`,
    Ln(k.ring(cx, cy, 0.8, top, P, 12), { tone: "mid" }),
  ].join("");
  const id = nameFor(name);
  put(id, [cx, cy, z + 1.5], svg, [record(A.cylinder(cx, cy, Rr, z, 3, { name: id }))], { bias });
  DIALS.push({ name, cx, cy, top, R: Rr, from, span });
}
function knob(name, centre, outward, r, length, { pointer = true } = {}) {
  const F = G.frameAlong(centre, outward);
  const tip = G.add3(centre, G.mul3(F.a, length));
  const side = G.unit3(G.cross3(F.a, UP));
  const pointerLine = pointer ? Ln(path3([G.add3(tip, G.mul3(F.a, 0.05)), G.add3(G.add3(tip, G.mul3(F.a, 0.05)), G.mul3(G.unit3(G.add3(side, G.mul3(UP, 0.6))), r * 0.85))]), { tone: "hi", free: "end" }) : "";
  const id = nameFor(name);
  put(id, G.add3(centre, G.mul3(F.a, length / 2)), S(G.disc(0, length, r, F, P, { bevel: 0.3 }), { tone: "hi" }) + Faded(G.ribsOf(F, 0, length, r, 22, P, { fade: [0.1, 0.55], seams: true }), { tone: "lo" }) + pointerLine, [record(A.disc(F, 0, length, r, { name: id }))], { bias: 0.2 });
}
function lamp(name, p, id) {
  put(nameFor(name), p, `<g class="iso-dots ic-lamp" data-lamp="${id}">${Dots([at(p)], { size: 0.7, tone: "hi" }).replace(/<g[^>]*>|<\/g>/g, "")}</g>`, [record(A.ball(p, 0.5, { name }))], { bias: 0.3 });
}

// ---------- bench ----------
const back = [];
back.push(`<path class="iso-halo" d="${k.haloOf(PLATE, -PLATE_H - FOOT_H, PLATE_H, P)}"/>`);
const byDepth = (points) => [...points].sort((a, b) => k.depthOf([a[0], a[1], 0], P) - k.depthOf([b[0], b[1], 0], P));
for (const [x, y] of byDepth(k.corners(PLATE, 22))) {
  back.push(S(k.cylinder(x, y, 7, -PLATE_H - FOOT_H, 1.6, P, 28), { tone: "lo" }));
  back.push(S(k.cylinder(x, y, 5.4, -PLATE_H - FOOT_H + 1.6, FOOT_H - 1.6, P, 28), { tone: "mid" }));
}
back.push(S(k.slabOf(PLATE, -PLATE_H, PLATE_H, P, 8, 1.6), { tone: "mid", inner: Ln(k.sideSeam(PLATE, -4, P, 8), { tone: "faint" }) }));
back.push(Ln(k.planOutline(k.insetPlan(PLATE, 5), 0, P), { tone: "lo" }));
const plateScrews = k.corners(PLATE, 10);
back.push(Ln(plateScrews.map(([x, y]) => k.ring(x, y, 2.2, 0, P, 16)).join(""), { tone: "lo" }));
back.push(Dots(plateScrews.map(([x, y]) => at([x, y, 0])), { size: 0.5 }));
record(A.slab(PLATE, -PLATE_H, PLATE_H, { name: "stand.plate", ground: true }, 8));
const STRIP = { x: -150, y: PLATE.y + PLATE.d - 10, w: 258, d: 6, r: 1 };
back.push(S(k.slabOf(STRIP, 0, 0.6, P, 3), { tone: "lo", crease: "none" }));
const ticks = k.topTicks(STRIP.x + 4, STRIP.x + STRIP.w - 4, 4, 5, STRIP.y, 0.6, [1.8, 3.4], P);
back.push(Ln(ticks.minor, { tone: "lo" }), Ln(ticks.major, { tone: "mid" }));
const LABEL = { x: -158, y: 24, w: 28, d: 11, r: 1.2 };
back.push(S(k.slabOf(LABEL, 0, 0.8, P, 3), { tone: "lo", crease: "none" }));
back.push(Ln(k.planOutline(k.insetPlan(LABEL, 1.4), 0.8, P, 3), { tone: "faint" }));
back.push(Ln([18, 12, 15].map((w, i) => k.lineOnTop([LABEL.x + 4, LABEL.y + 2.8 + i * 2.7], [LABEL.x + 4 + w, LABEL.y + 2.8 + i * 2.7], 0.8, P)).join(""), { tone: "lo", free: true }));
back.push(Dots([at([LABEL.x + LABEL.w - 2.4, LABEL.y + 2.2, 0.8]), at([LABEL.x + LABEL.w - 2.4, LABEL.y + LABEL.d - 2.2, 0.8])], { size: 0.45 }));
record(A.slab(STRIP, 0, 0.6, { name: "stand.strip", ground: true }, 3));
record(A.slab(LABEL, 0, 0.8, { name: "stand.label", ground: true }, 3));

// ---------- station 1: extraction column ----------
const EXB = { x: EX[0] - 20, y: EX[1] - 20, w: 40, d: 40, r: 2 };
const EXF = vert(EX[0], EX[1]);
const GL1 = { r: 11, z0: 12, z1: 84 };
box("ex.base", [EXB.x, EXB.y, 0], [EXB.x + EXB.w, EXB.y + EXB.d, 12], { tone: "mid" }, {
  r: 2, steps: 4, bevel: 0.6,
  inner: Ln(k.sideSeam(EXB, 3, P, 4), { tone: "faint" }),
  extra: Dots(k.corners(EXB, 3).map(([x, y]) => at([x, y, 12])), { size: 0.45 }),
});
// drain valve on the front face, extract outlet on the right face
{
  const c = [EX[0], EXB.y + EXB.d, 6];
  const face = boss("ex.drain.boss", c, [0, 1, 0], 2.2, 2.5, { tone: "mid" });
  const SF = G.frameAlong(face, [0, 1, 0]);
  disc("ex.drain.stem", SF, 0, 3.5, 0.9, { tone: "mid" });
  disc("ex.drain.wheel", SF, 3.5, 4.9, 3.4, { tone: "hi" }, { extra: Faded(G.ribsOf(SF, 3.5, 4.9, 3.4, 24, P, { fade: [0.1, 0.55], seams: true }), { tone: "lo" }) + Ln(G.circleOf(SF, 4.9, 1.2, P, 16), { tone: "lo" }) });
}
const EX_OUT = boss("ex.out.boss", [EXB.x + EXB.w, 8, 5], [1, 0, 0], 3, 2.5);
dial("therm", EX[0] + 14.5, EX[1] + 14.5, 12, 4.5);
// the column: sump, support plate, coffee bed, hot water, glass, tie rods, head
level("sump", EX[0], EX[1], 10.3, GL1.z0 + 0.3, 19, "ic-coffee", { tone: "lo" });
disc("ex.plate", EXF, 19, 20, 10.3, { tone: "mid" });
{
  const grains = [];
  for (let i = 0; i < 46; i++) {
    const a = i * 2.399963;
    const rr = 9.4 * Math.sqrt(((i * 0.618) % 1));
    grains.push(at([EX[0] + rr * Math.cos(a), EX[1] + rr * Math.sin(a), 46]));
  }
  put("ex.bed", [EX[0], EX[1], 33], `<g class="iso-solid ic-bed">${S(k.cylinder(EX[0], EX[1], 10.3, 20, 26, P, 48), { tone: "lo", crease: "none" })}</g><g class="iso-dots ic-grain">${Dots(grains, { size: 0.42 }).replace(/<g[^>]*>|<\/g>/g, "")}</g>`, [record(A.cylinder(EX[0], EX[1], 10.3, 20, 26, { name: "ex.bed" }))], { bias: 0.1 });
}
level("water", EX[0], EX[1], 10.3, 46, 72, "ic-water", { tone: "faint" });
glassCyl("ex.glass", EX[0], EX[1], GL1.r, GL1.z0, GL1.z1);
const ROD_AT = [[13.5, 0], [0, 13.5], [-13.5, 0], [0, -13.5]];
for (const [dx, dy] of ROD_AT) {
  const F = vert(EX[0] + dx, EX[1] + dy);
  disc("ex.nut", F, 12, 14, 1.8, { tone: "mid" }, { steps: 6 });
  disc("ex.rod", F, 14, 84, 1, { tone: "mid" }, { steps: 16 });
  disc("ex.nut.top", F, 90, 92, 1.8, { tone: "mid" }, { steps: 6 });
}
disc("ex.head", EXF, 84, 90, 14, { tone: "hi" }, { bevel: 0.6, inner: Ln(G.arcOf(EXF, 86, 14, P), { tone: "faint" }) });
const EX_IN = boss("ex.in.boss", [EX[0], EX[1], 90], UP, 3.2, 6);

// boiler behind the column
const BOF = vert(BO[0], BO[1]);
disc("boiler.foot", BOF, 0, 1.6, 9.8, { tone: "lo" });
turned("boiler.shell", BOF, [[1.6, 9], [28, 9]], { tone: "hi" }, { inner: Ln(G.arcOf(BOF, 8, 9, P) + G.arcOf(BOF, 20, 9, P), { tone: "faint" }) });
turned("boiler.lid", BOF, [[28, 9.6], [29.6, 9.6], [29.6, 9], [31, 8.2, 1], [32.4, 6, 1], [33, 3.4]], { tone: "hi" });
const BO_OUT = boss("boiler.out.boss", [BO[0], BO[1], 33], UP, 3.2, 3);
box("boiler.element", [BO[0] + 8.8, BO[1] - 2, 4], [BO[0] + 15, BO[1] + 2, 12], { tone: "mid" }, { r: 0.8, steps: 2, extra: Dots([at([BO[0] + 15, BO[1] - 1.2, 10]), at([BO[0] + 15, BO[1] + 1.2, 10])], { size: 0.4 }) });
pipe("water", [BO_OUT, [BO[0], BO[1], 112], [EX[0], EX[1], 112], EX_IN], 1.9, { bands: [0.5] });

// pump 1 and the extract lines
function pump(name, x0, y0) {
  const plan = { x: x0, y: y0, w: 12, d: 12, r: 1 };
  box(`${name}.block`, [x0, y0, 0], [x0 + 12, y0 + 12, 9], { tone: "mid" }, { r: 1, steps: 3, bevel: 0.4, extra: Dots([at([x0 + 2, y0 + 2, 9]), at([x0 + 10, y0 + 10, 9]), at([x0 + 10, y0 + 2, 9])], { size: 0.4 }) });
  const F = vert(x0 + 6, y0 + 6);
  turned(`${name}.motor`, F, [[9, 3.8], [17, 3.8], [17.6, 3.2, 1], [18, 2]], { tone: "hi" }, { inner: Ln(G.arcOf(F, 11, 3.8, P), { tone: "faint" }) });
  const inlet = boss(`${name}.in.boss`, [x0, y0 + 6, 5], [-1, 0, 0], 3, 2.5);
  const outlet = boss(`${name}.out.boss`, [x0 + 12, y0 + 6, 5], [1, 0, 0], 3, 2.5);
  return { inlet, outlet, plan };
}
const P1 = pump("pump1", -78, 2);
pipe("extract-a", [EX_OUT, P1.inlet], 1.9);

// ---------- station 2: vacuum kettle, condenser, vacuum pump ----------
const KEB = { x: KE[0] - 20, y: KE[1] - 20, w: 40, d: 40, r: 2 };
const KEF = vert(KE[0], KE[1]);
box("ke.base", [KEB.x, KEB.y, 0], [KEB.x + KEB.w, KEB.y + KEB.d, 10], { tone: "mid" }, {
  r: 2, steps: 4, bevel: 0.6,
  inner: Ln(k.sideSeam(KEB, 2.5, P, 4), { tone: "faint" }),
  extra: Dots(k.corners(KEB, 3).map(([x, y]) => at([x, y, 10])), { size: 0.45 }),
});
const KE_IN = boss("ke.in.boss", [KEB.x, 8, 5], [-1, 0, 0], 3, 2.5);
const KE_OUT = boss("ke.out.boss", [KEB.x + KEB.w, 14, 5], [1, 0, 0], 3, 2.5);
knob("ke.heat.knob", [KE[0] - 10, KEB.y + KEB.d, 5], [0, 1, 0], 2.2, 2.5);
lamp("ke.lamp", [KE[0] - 3, KEB.y + KEB.d + 0.02, 5], "heat");
pipe("extract-b", [P1.outlet, KE_IN], 1.9);
turned("ke.shell", KEF, [[10, 16], [30, 16]], { tone: "hi" }, { inner: Ln(G.arcOf(KEF, 12, 16, P), { tone: "faint" }) });
disc("ke.jacket", KEF, 30, 33.5, 17.4, { tone: "mid" });
turned("ke.shell", KEF, [[33.5, 16], [52, 16]], { tone: "hi" }, { inner: Ln(G.arcOf(KEF, 50, 16, P), { tone: "faint" }) });
disc("ke.flange", KEF, 52, 55, 17.6, { tone: "hi" }, { extra: Dots(G.dotsOf(KEF, 55, 16.8, 10, P, { all: true }), { size: 0.42, tone: "mid" }) });
{
  const dome = [];
  for (let i = 0; i <= 8; i++) {
    const z = 55 + (15.2 * i) / 8;
    dome.push([z, Math.sqrt(Math.max(25, 256 - (z - 55) ** 2)), i > 0 && i < 8 ? 1 : 0]);
  }
  dome[dome.length - 1] = [70.2, 5];
  glassLathe("ke.dome", KEF, dome, { ref: [KE[0], KE[1], 61] });
}
disc("ke.neck", KEF, 70.2, 74, 5.5, { tone: "mid" });
const KE_VAP = boss("ke.vap.boss", [KE[0], KE[1], 74], UP, 4.5, 3);
// sight glass on the front of the kettle
const U = k.towardViewer(P);
const SG = [KE[0] + 22 * U[0], KE[1] + 22 * U[1]];
for (const z of [17, 47]) {
  const from = [KE[0] + 16 * U[0], KE[1] + 16 * U[1], z];
  boss("ke.sight.boss", from, [U[0], U[1], 0], 1.1, 3.8, { tone: "mid", ring: false });
}
level("kettle", SG[0], SG[1], 1.5, 15, 49, "ic-coffee", { tone: "lo", extra: `<g class="iso-dots ic-mist" data-part="bubbles"></g>` });
glassCyl("ke.sight", SG[0], SG[1], 2.2, 14, 50, { wall: 0.55 });
// condenser standing on its receiver
const COF = vert(CO[0], CO[1]);
level("condensate", CO[0], CO[1], 7.2, 0.6, 17, "ic-water", { tone: "faint" });
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
// vacuum pump
const VP = { x: 36, y: -46, w: 26, d: 16, r: 1.5 };
box("vac.box", [VP.x, VP.y, 0], [VP.x + VP.w, VP.y + VP.d, 12], { tone: "mid" }, {
  r: 1.5, steps: 3, bevel: 0.5,
  inner: Ln(k.sideSeam(VP, 3, P, 3), { tone: "faint" }),
  extra: Dots(k.corners(VP, 2.5).map(([x, y]) => at([x, y, 12])), { size: 0.4 }),
});
dial("vac", 43, -38, 12, 4.5);
const VP_IN = boss("vac.in.boss", [49.5, -38, 12], UP, 2, 2.5);
{
  const F = vert(56.5, -38);
  turned("vac.motor", F, [[12, 3.8], [21, 3.8], [21.6, 3.2, 1], [22, 2]], { tone: "hi" }, { inner: Ln(G.arcOf(F, 14, 3.8, P), { tone: "faint" }) });
}
pipe("vacuum", [CO_VAC, [VAC_AT[0], VAC_AT[1], 84], [49.5, -38, 84], VP_IN], 1.2, { flow: false });
// pump 2 and the feed line to the atomizer
const P2 = pump("pump2", 30, 8);
pipe("concentrate", [KE_OUT, P2.inlet], 1.9);

// ---------- station 3: spray dryer ----------
const DRF = vert(DR[0], DR[1]);
const POST = [92, -34];
{
  const F = vert(POST[0], POST[1]);
  disc("dr.post.foot", F, 0, 1.2, 3.8, { tone: "lo" });
  disc("dr.post", F, 1.2, 36, 3, { tone: "mid" }, { steps: 24 });
  disc("dr.post", F, 42, 118, 3, { tone: "mid" }, { steps: 24 });
  disc("dr.post", F, 124, 140, 3, { tone: "mid" }, { steps: 24 });
  turned("dr.post.cap", F, [[140, 3.4], [141, 3.4], [141.6, 2.6, 1], [142, 1.2]], { tone: "mid" });
  for (const z of [36, 118]) {
    ringOf("dr.collar", F, z, z + 6, 3, 5.5, { tone: "mid" }, { bevel: 0.3, extra: Dots([at([POST[0] + 5.5 * 0.5, POST[1] + 5.5 * 0.86, z + 3])], { size: 0.4, tone: "hi" }) });
    const rimY = -Math.sqrt(21 * 21 - (POST[0] - DR[0]) ** 2);
    box("dr.arm", [POST[0] - 2, POST[1] + 5.5, z + 1], [POST[0] + 2, rimY, z + 5], { tone: "lo" }, { r: 0.4 });
  }
}
// glass collection jar with the powder in it
level("powder", DR[0], DR[1], 9.2, 0.8, 12, "ic-powder", { tone: "hi", extra: `<g class="iso-dots ic-grain" data-part="grains"></g>` });
glassCyl("dr.jar", DR[0], DR[1], 10, 0, 15, { wall: 0.8 });
ringOf("dr.jar.neck", DRF, 15, 17.5, 5, 10.6, { tone: "mid" });
disc("dr.nozzle", DRF, 17.5, 22, 4.5, { tone: "mid" });
turned("dr.cone", DRF, [[22, 4], [36, 19]], { tone: "hi" }, { inner: Ln(G.arcOf(DRF, 29, 11.5, P, { slope: 15 / 14 }), { tone: "faint" }) });
ringOf("dr.flange", DRF, 36, 42, 17, 21, { tone: "hi" }, { bevel: 0.4, extra: Dots(G.dotsOf(DRF, 42, 19.8, 10, P, { all: true }), { size: 0.42, tone: "mid" }) });
ringOf("dr.port", DRF, 42, 50, 17.3, 20.5, { tone: "mid" }, { inner: Ln(G.arcOf(DRF, 46, 20.5, P), { tone: "faint" }) });
const EXH_FACE = boss("dr.exhaust.boss", [DR[0] + 20.5, DR[1], 46], [1, 0, 0], 3.6, 2.5, { tone: "mid", owner: "dr.exhaust.fitting" });
// the spray: the one lit thing in the figure
{
  const svg = `<g class="iso-dots ic-spray" data-part="spray"></g>`;
  put("dr.spray", [DR[0], DR[1], 81], `<path class="iso-fill" d="${k.cylinder(DR[0], DR[1], 15.5, 52, 58, P, 24).fill}" opacity="0"/>${svg}`, [record(A.cylinder(DR[0], DR[1], 15.5, 52, 58, { name: "dr.spray" }))], { bias: 0.05 });
}
disc("dr.shaft", DRF, 113, 118, 1.2, { tone: "mid" }, { steps: 12 });
disc("dr.wheel", DRF, 110, 113, 7, { tone: "hi" }, { extra: `<g data-part="spokes"></g>` + Ln(G.circleOf(DRF, 113, 1.6, P, 16), { tone: "lo" }) });
glassCyl("dr.glass", DR[0], DR[1], 17, 50, 118, { wall: 0.7 });
disc("dr.head", DRF, 118, 126, 21, { tone: "hi" }, { bevel: 0.6, inner: Ln(G.arcOf(DRF, 120.5, 21, P), { tone: "faint" }), extra: Dots(G.dotsOf(DRF, 126, 19.6, 12, P, { all: true, phase: 0.15 }), { size: 0.42, tone: "mid" }) });
turned("dr.motor", DRF, [[126, 6], [140, 6], [141.2, 5, 1], [142, 3.4]], { tone: "mid" }, { inner: Ln(G.arcOf(DRF, 128, 6, P), { tone: "faint" }) });
const DR_FEED = boss("dr.feed.boss", [DR[0], DR[1], 142], UP, 2.5, 3);
const PLEN = box("dr.plenum", [72, -9, 126], [82, 1, 136], { tone: "mid" }, { r: 1, steps: 3, bevel: 0.4, extra: Dots([at([74, -7, 136]), at([80, -1, 136])], { size: 0.4 }) });
const PLEN_IN = boss("dr.plenum.boss", [77, -9, 131], [0, -1, 0], 4.5, 2.5);
// air heater: blower box, heater tube, outlet header
const BL = { x: 66, y: -48, w: 22, d: 18, r: 1.5 };
{
  const slots = [0, 1, 2].map((i) => path3([[88.02, -45 + i * 4.6, 4], [88.02, -43 + i * 4.6, 4], [88.02, -43 + i * 4.6, 11], [88.02, -45 + i * 4.6, 11]], true)).join("");
  box("ht.blower", [BL.x, BL.y, 0], [BL.x + BL.w, BL.y + BL.d, 14], { tone: "mid" }, { r: 1.5, steps: 3, bevel: 0.5, inner: Ln(k.sideSeam(BL, 3, P, 3), { tone: "faint" }), extra: Ln(slots, { tone: "faint" }) + Dots(k.corners(BL, 2.5).map(([x, y]) => at([x, y, 14])), { size: 0.4 }) });
}
const HTF = vert(HT[0], HT[1]);
turned("ht.tube", HTF, [[14, 6.5], [124, 6.5]], { tone: "hi" }, { inner: Ln([40, 70, 100].map((z) => G.arcOf(HTF, z, 6.5, P)).join(""), { tone: "faint" }) });
box("ht.header", [72, -44, 124], [82, -34, 136], { tone: "mid" }, { r: 1, steps: 3, bevel: 0.4 });
dial("air", 77, -39, 136, 4, { count: 36, every: 6 });
const HT_OUT = boss("ht.out.boss", [77, -34, 131], [0, 1, 0], 4.5, 2.5);
pipe("air", [HT_OUT, PLEN_IN], 3.2, { flangeR: 1.3, bands: [0.5] });
// cyclone on the right, held from the right post
const CYF = vert(CY[0], CY[1]);
glassCyl("cy.fines", CY[0], CY[1], 5.5, 0, 10, { wall: 0.6 });
ringOf("cy.fines.neck", CYF, 10, 12, 2.8, 5.9, { tone: "mid" });
disc("cy.nozzle", CYF, 12, 14, 2.4, { tone: "mid" });
glassLathe("cy.cone", CYF, [[14, 2.2], [30, 7]], { ref: [CY[0], CY[1], 22], wall: 0.6 });
const CY_SOLID = glassCyl("cy.glass", CY[0], CY[1], 7, 30, 56, { wall: 0.6, solid: true, extra: `<g class="iso-dots ic-mist" data-part="swirl"></g>` });
disc("cy.lid", CYF, 56, 59, 7.8, { tone: "mid" }, { bevel: 0.3, extra: Dots(G.dotsOf(CYF, 59, 6.8, 6, P, { all: true }), { size: 0.4, tone: "mid" }) });
disc("cy.stack.boss", CYF, 59, 62, 3, { tone: "hi" });
disc("cy.stack", CYF, 62, 74, 2.4, { tone: "hi" }, { steps: 20 });
turned("cy.filter", CYF, [[74, 4.5], [84, 4.5], [85.2, 3.6, 1], [86, 2]], { tone: "mid" }, { inner: Ln(G.arcOf(CYF, 76, 4.5, P) + G.arcOf(CYF, 82, 4.5, P), { tone: "faint" }) });
box("cy.bracket", [POST[0] + 5.5, POST[1] - 2, 37], [136, POST[1] + 2, 41], { tone: "mid" }, { r: 0.4, extra: Dots([at([101, POST[1] + 2, 39]), at([128, POST[1] + 2, 39])], { size: 0.4 }) });
box("cy.bracket.toe", [132, POST[1] + 2, 37], [136, -25, 41], { tone: "mid" }, { r: 0.4 });
// exhaust duct from the port ring to the cyclone, between two elbow balls
{
  const BALL = 4.4;
  const RIM = 3;
  const toCy = G.unit3([CY[0] - EXH_FACE[0], CY[1] - EXH_FACE[1], 0]);
  const padPoint = [CY[0] - toCy[0] * 7, CY[1] - toCy[1] * 7, 46];
  const padNormal = [-toCy[0], -toCy[1], 0];
  const padFace = padOn("cy.in.pad", CY_SOLID, padPoint, padNormal, 3.6, 2.5, { tone: "mid", owner: "cy.in.fitting" });
  const c1 = G.add3(EXH_FACE, G.mul3([1, 0, 0], Math.sqrt(BALL ** 2 - 3.6 ** 2)));
  const c2 = G.add3(padFace, G.mul3(padNormal, Math.sqrt(BALL ** 2 - 3.6 ** 2)));
  ball("dr.exhaust.elbow", c1, BALL, { tone: "hi" }, { owner: "dr.exhaust.fitting" });
  ball("cy.in.elbow", c2, BALL, { tone: "hi" }, { owner: "cy.in.fitting" });
  const axis = G.unit3(G.sub3(c2, c1));
  const reach = Math.sqrt(BALL ** 2 - RIM ** 2);
  pipe("exhaust", [G.add3(c1, G.mul3(axis, reach)), G.sub3(c2, G.mul3(axis, reach))], RIM, { flanges: [false, false], rims: [RIM, RIM] });
}
// feed line from pump 2 up the right post to the atomizer
pipe("feed", [P2.outlet, [150, 14, 5], [150, -40, 5], [150, -40, TOP_FEED], [DR[0], DR[1], TOP_FEED], DR_FEED], 1.6, { bands: [0.25, 0.62, 0.82] });

// ---------- controls ----------
const CB = { x: 114, y: 24, w: 36, d: 16, r: 1.5 };
box("ctl.box", [CB.x, CB.y, 0], [CB.x + CB.w, CB.y + CB.d, 16], { tone: "mid" }, {
  r: 1.5, steps: 3, bevel: 0.6,
  inner: Ln(k.sideSeam(CB, 12, P, 3), { tone: "faint" }),
  extra: Dots(k.corners(CB, 2.5).map(([x, y]) => at([x, y, 16])), { size: 0.4 }) + Ln(k.planOutline({ x: CB.x + 3, y: CB.y + 3, w: 14, d: 10, r: 1 }, 16, P, 2), { tone: "faint" }),
});
knob("ctl.knob", [122, CB.y + CB.d, 7], [0, 1, 0], 2.4, 2.5);
knob("ctl.knob", [131, CB.y + CB.d, 7], [0, 1, 0], 2.4, 2.5);
{
  const sw = [142, CB.y + CB.d, 7];
  const F = G.frameAlong(sw, [0, 1, 0]);
  disc("ctl.switch.ring", F, 0, 1, 1.6, { tone: "lo" });
  put("ctl.switch.lever", G.add3(sw, [0, 1.6, 0]), Ln(path3([G.add3(sw, [0, 1, 0]), G.add3(sw, [0, 3.2, 1.8])]), { tone: "hi", free: "end" }), [record(A.disc(F, 1, 3.4, 0.4, { name: "ctl.switch.lever" }))], { bias: 0.3 });
}
lamp("ctl.lamp", [120, CB.y + CB.d + 0.02, 12.5], "extract");
lamp("ctl.lamp", [124.5, CB.y + CB.d + 0.02, 12.5], "concentrate");
lamp("ctl.lamp", [129, CB.y + CB.d + 0.02, 12.5], "dry");

// ---------- order, page ----------
A.settle(R, P);
R.items.sort((a, b) => a.key - b.key);
const groups = R.items.map((item) => `<g class="it" data-name="${item.name}"${item.attrs ?? ""}>${item.svg}</g>`);

const LABEL_TEXT =
  "A bench-top instant coffee line, left to right: a glass extraction column with a bed of ground coffee, fed with hot water from a boiler behind it, draining through a pump into a vacuum kettle with a glass dome and a sight glass; a condenser on a glass receiver collects the water boiled off; a second pump feeds the concentrate to a spray-drying tower with a glass chamber, an atomizer wheel under its head, hot air from a heater behind it, a cyclone and a glass collection jar where the powder gathers.";
const svg = k.figureSvg({ width: W, height: H, label: LABEL_TEXT, body: [...back, `<g class="ic-line">${groups.join("")}</g>`] });

const B = M.balance();
const DATA = {
  P,
  dials: DIALS,
  column: { cx: EX[0], cy: EX[1], r: 10.3, sump: [GL1.z0 + 0.3, 19], water: [46, 72] },
  sight: { cx: SG[0], cy: SG[1], r: 1.5, z: [15, 49] },
  receiver: { cx: CO[0], cy: CO[1], r: 7.2, z: [0.6, 17] },
  jar: { cx: DR[0], cy: DR[1], r: 9.2, z: [0.8, 12] },
  spray: { cx: DR[0], cy: DR[1], zTop: 109.5, zBot: 50, rTop: 2, rBot: 12.5 },
  wheel: { cx: DR[0], cy: DR[1], z: 113.2, r0: 2.2, r1: 6.2 },
  cyclone: { cx: CY[0], cy: CY[1], z: [33, 54], r: 5.2 },
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
      { mark: "lit", label: "The spray: concentrate atomized into hot air, drying into powder as it falls" },
      { mark: "raised", label: "Glass vessels: the coffee at each stage, water leaving at every one" },
      { mark: "edge", label: "Pipes carrying the batch, marked while that line runs" },
    ],
    caption: `Instant coffee is brewed coffee with the water taken back out. ${B.solids.toFixed(0)} g of soluble solids come out of ${M.BATCH.ground} g of roast and ground coffee in the column, with water at ${M.PLANT.waterC} °C under pressure: ${B.extract.toFixed(0)} g of extract at ${Math.round(M.BATCH.extractSolids * 100)} % solids. The kettle boils off ${B.evaporated.toFixed(0)} g of that water under vacuum at about ${M.PLANT.kettleC} °C, so the flavour is not cooked, and the condenser catches it. The ${B.concentrate.toFixed(0)} g of concentrate are sprayed into air at ${M.PLANT.airInC} °C; each droplet dries in seconds, and ${B.powder.toFixed(0)} g of powder at ${Math.round((1 - M.BATCH.powderSolids) * 100)} % moisture fall into the jar: about ${Math.round(B.cups)} cups. Freeze-drying does the last step cold, by sublimation under vacuum, and keeps more aroma.`,
    body: `<div class="iso-stage ic-stage" tabindex="0" role="slider" aria-label="Instant coffee line. Move the pointer across the bench, or use the left and right arrow keys, to run one batch through extraction, concentration and spray drying." aria-valuemin="0" aria-valuemax="3" aria-valuenow="0" aria-valuetext="ready">${svg}<span class="ic-sr" role="status" aria-live="polite" data-status></span></div>`,
  });

let page;
let name;
if (VIDEO) {
  const [FW, FH] = FRAME;
  const svgW = Math.round(Math.min(FW - 100, ((FH - 150) * W) / H));
  const font = Math.round(Math.min(FW, FH) / 30);
  const VIDEO_CSS = `
.iso-page{width:${FW}px;margin:0}
body{background:var(--anatomy-page)}
.iso{--anatomy-page:#0e0e0e;--anatomy-card:#0e0e0e;--anatomy-paper:#0e0e0e;--anatomy-face:#1c1c1c;--anatomy-top:#252525;--anatomy-shade-0:#0b0b0b;--anatomy-shade-1:#121212;--anatomy-shade-2:#181818;--anatomy-shade-3:#1f1f1f;--anatomy-lit-top:#303030;--anatomy-lit-shade:#242424;--anatomy-hi:#f2f2f2;--anatomy-mid:#a6a6a6;--anatomy-lo:#616161;--anatomy-faint:#3a3a3a;--anatomy-weight:.85px;--anatomy-dot:#f0f0f0;--anatomy-strong:#f2f2f2}
.iso[data-theme="light"]{--anatomy-page:#fbfbf9;--anatomy-card:#fbfbf9;--anatomy-paper:#fbfbf9;--anatomy-face:#ffffff;--anatomy-top:#ffffff;--anatomy-hi:#151517;--anatomy-mid:#66666b;--anatomy-lo:#9a9a9f;--anatomy-faint:#cfcfd2;--anatomy-weight:.85px;--anatomy-shade-0:#d2d2cf;--anatomy-shade-1:#ddddda;--anatomy-shade-2:#e8e8e5;--anatomy-shade-3:#f2f2ef;--anatomy-dot:#2a2a2e;--anatomy-strong:#151517}
.ic-frame{width:${FW}px;height:${FH}px;position:relative;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:${Math.round(font * 0.8)}px;overflow:hidden}
.ic-frame .iso-svg{width:${svgW}px;height:auto;margin:0}
.ic-readout{font-family:var(--anatomy-mono);font-size:${font}px;line-height:1;letter-spacing:.02em;color:var(--anatomy-strong);font-variant-numeric:tabular-nums;white-space:nowrap}
`;
  const frameBody = `<style>${CSS}${VIDEO_CSS}</style><div class="ic-frame"><div class="iso-stage ic-stage" tabindex="0" role="slider" aria-label="Instant coffee line" aria-valuemin="0" aria-valuemax="3" aria-valuenow="0" aria-valuetext="ready">${svg}<span class="ic-sr" role="status" aria-live="polite" data-status></span></div><div class="ic-readout" data-readout>${M.stateAt(0).readout}</div></div>`;
  page = k.pageHtml({ title: "Instant coffee line (video)", theme: THEME, body: frameBody, script: kitScript() + modelScript + LIVE, width: FW });
  name = `instant-coffee-video${THEME === "light" ? "-light" : ""}${FW === 1920 && FH === 1080 ? "" : `-${FW}x${FH}`}.html`;
} else {
  page = k.pageHtml({ title: "Instant coffee line", theme: THEME, body, script: kitScript() + modelScript + LIVE, width: 650 });
  name = THEME === "light" ? "instant-coffee-light.html" : "instant-coffee.html";
}
writeFileSync(join(HERE, name), page);
console.log("wrote", name, `${(page.length / 1024).toFixed(0)} KB`, `${R.items.length} items`, `${R.solids.length} solids`, `${R.tubes.length} tubes`, `scale ${KS.toFixed(3)}`);

const SEE_THROUGH = [
  ["kettle", "ke.sight"], ["condensate", "co.receiver"], ["powder", "dr.jar"], ["sump", "ex.glass"], ["water", "ex.glass"], ["ex.bed", "ex.glass"], ["ex.plate", "ex.glass"],
  ["dr.spray", "dr.glass"], ["dr.wheel", "dr.glass"], ["dr.shaft", "dr.glass"],
];
// A duct whose rim sits on an elbow ball is drawn after the ball by choice; the slender glass column under the head is not a rod the water line lands on.
A.auditOrExit(R, P, { allow: [...SEE_THROUGH, ["exhaust*", "cy.in.elbow"], ["exhaust*", "dr.exhaust.elbow"]], crowd: [["water*", "ex.glass"]] });
