const DATA = __DATA__;
const P = DATA.P;
const stage = document.querySelector(".ic-stage");
const svg = stage.querySelector("svg");
const readout = document.querySelector("[data-readout]");
const status = stage.querySelector("[data-status]");
const still = matchMedia("(prefers-reduced-motion: reduce)");
const part = (name) => svg.querySelector(`[data-part="${name}"]`);
const parts = {
  sump: part("sump"), water: part("water"), kettle: part("kettle"), bubbles: part("bubbles"), condensate: part("condensate"),
  powder: part("powder"), grains: part("grains"), spray: part("spray"), swirl: part("swirl"), spokes: part("spokes"),
};
const needles = Object.fromEntries(DATA.dials.map((d) => [d.name, part(d.name)]));
const lamps = Object.fromEntries([...svg.querySelectorAll("[data-lamp]")].map((el) => [el.dataset.lamp, el]));
const routeGroups = Object.fromEntries(DATA.routes.map((name) => [name, [...svg.querySelectorAll(`[data-route="${name}"]`)]]));
const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
const f1 = (v) => Math.round(v * 10) / 10;

// Grain positions inside the jar, fixed in the plan; only their height follows the pile.
const GRAINS = Array.from({ length: 40 }, (_, i) => {
  const a = i * 2.399963;
  const rr = (DATA.jar.r - 0.8) * Math.sqrt((i * 0.618) % 1);
  return [DATA.jar.cx + rr * Math.cos(a), DATA.jar.cy + rr * Math.sin(a)];
});
const DROPS = Array.from({ length: 44 }, (_, i) => ({ phase: (i * 0.618034) % 1, angle: i * 2.399963, swirl: 2.4 + ((i * 7) % 5) * 0.3 }));
const BUBBLES = Array.from({ length: 6 }, (_, i) => ({ phase: (i * 0.618034) % 1, dx: ((i % 3) - 1) * 0.5, dy: ((i % 2) - 0.5) * 0.6 }));
const SWIRL = Array.from({ length: 10 }, (_, i) => ({ phase: (i * 0.618034) % 1, angle: i * 1.3 }));

function levelSvg(spec, share, cls, tone) {
  const h = (spec.z[1] - spec.z[0]) * clamp(share, 0, 1);
  if (h < 0.08) return "";
  return solidSvg(cylinder(spec.cx, spec.cy, spec.r, spec.z[0], h, P, 48), { tone, crease: "none" }).replace(/^<g[^>]*>|<\/g>$/g, "");
}
function dotsOf(points, size) {
  return points.map(([x, y, a]) => `<circle cx="${f1(x)}" cy="${f1(y)}" r="${size}"${a !== undefined ? ` fill-opacity="${a.toFixed(2)}"` : ""}/>`).join("");
}
function needleAt(d, value) {
  const a = d.from + d.span * clamp(value, 0, 1);
  return lineOnTop([d.cx - Math.sin(a) * 1.2, d.cy + Math.cos(a) * 1.2], [d.cx + Math.sin(a) * (d.R - 1.9), d.cy - Math.cos(a) * (d.R - 1.9)], d.top + 0.2, P);
}

let s = 0, target = 0, clock = 0, frame = 0, last = 0, visible = false, touring = !still.matches, idleTimer = 0, spin = 0, flowClock = 0;
let said = "";
const gauges = { therm: 0, vac: 0, air: 0 };

// The idle tour: one batch through the line, a pause at the end, then back to the start.
const TOUR = [[0, 1.2], [1, 4.6], [2, 4.6], [3, 5.6], [3, 2.8], [0, 1.6]];
const TOUR_LENGTH = TOUR.reduce((a, [, d]) => a + d, 0);
function tourAt(t) {
  let at = t % TOUR_LENGTH;
  let from = 0;
  for (const [to, d] of TOUR) {
    if (at <= d) {
      const u = d > 0 ? at / d : 1;
      const e = u * u * (3 - 2 * u);
      return from === to ? to : from + (to - from) * (to < from ? e : u);
    }
    at -= d;
    from = to;
  }
  return 0;
}

function draw(state, dt) {
  parts.sump.innerHTML = levelSvg(DATA.column.sump ? { cx: DATA.column.cx, cy: DATA.column.cy, r: DATA.column.r, z: DATA.column.sump } : null, state.sump, "ic-coffee", "lo");
  parts.water.innerHTML = levelSvg({ cx: DATA.column.cx, cy: DATA.column.cy, r: DATA.column.r, z: DATA.column.water }, state.water, "ic-water", "faint");
  parts.kettle.innerHTML = levelSvg(DATA.sight, state.kettleFill, "ic-coffee", "lo");
  parts.condensate.innerHTML = levelSvg(DATA.receiver, state.condensate, "ic-water", "faint");
  parts.powder.innerHTML = levelSvg(DATA.jar, state.dried, "ic-powder", "hi");
  // grains on top of the pile
  const pileTop = DATA.jar.z[0] + (DATA.jar.z[1] - DATA.jar.z[0]) * state.dried;
  parts.grains.innerHTML = state.dried > 0.03 ? dotsOf(GRAINS.map(([x, y]) => iso([x, y, pileTop], P)), 0.4) : "";
  // bubbles rising in the sight glass while it boils
  if (state.boiling > 0.02) {
    const top = DATA.sight.z[0] + (DATA.sight.z[1] - DATA.sight.z[0]) * state.kettleFill;
    parts.bubbles.innerHTML = dotsOf(BUBBLES.map((b) => {
      const age = (flowClock * 0.55 + b.phase) % 1;
      const z = DATA.sight.z[0] + 1 + (top - DATA.sight.z[0] - 1.5) * age;
      const p = iso([DATA.sight.cx + b.dx, DATA.sight.cy + b.dy, z], P);
      return [p[0], p[1], state.boiling * (1 - age * 0.6)];
    }), 0.32);
  } else parts.bubbles.innerHTML = "";
  // the spray: droplets leave the wheel's rim, swirl outward and down, and shrink into powder
  if (state.spraying > 0.02) {
    const sp = DATA.spray;
    const pts = [];
    const sizes = [];
    for (const d of DROPS) {
      const age = (flowClock * 0.42 + d.phase) % 1;
      const z = sp.zTop - (sp.zTop - sp.zBot) * age;
      const r = sp.rTop + (sp.rBot - sp.rTop) * Math.pow(age, 0.6);
      const a = d.angle + age * d.swirl + spin * 0.15;
      const p = iso([sp.cx + r * Math.cos(a), sp.cy + r * Math.sin(a), z], P);
      pts.push([p[0], p[1], state.spraying * (0.55 + 0.45 * (1 - age))]);
      sizes.push(0.85 - 0.5 * age);
    }
    parts.spray.innerHTML = pts.map(([x, y, a], i) => `<circle cx="${f1(x)}" cy="${f1(y)}" r="${sizes[i].toFixed(2)}" fill-opacity="${a.toFixed(2)}"/>`).join("");
    const cy = DATA.cyclone;
    parts.swirl.innerHTML = dotsOf(SWIRL.map((w) => {
      const age = (flowClock * 0.5 + w.phase) % 1;
      const z = cy.z[1] - (cy.z[1] - cy.z[0]) * age;
      const r = cy.r * (1 - age * 0.55);
      const a = w.angle - age * 7;
      const p = iso([cy.cx + r * Math.cos(a), cy.cy + r * Math.sin(a), z], P);
      return [p[0], p[1], state.spraying * (1 - age * 0.5)];
    }), 0.3);
  } else {
    parts.spray.innerHTML = "";
    parts.swirl.innerHTML = "";
  }
  // the atomizer wheel's spokes
  const w = DATA.wheel;
  parts.spokes.innerHTML = `<path class="iso-line" data-tone="lo" d="${Array.from({ length: 6 }, (_, i) => {
    const a = spin + (i * Math.PI) / 3;
    return lineOnTop([w.cx + Math.cos(a) * w.r0, w.cy + Math.sin(a) * w.r0], [w.cx + Math.cos(a) * w.r1, w.cy + Math.sin(a) * w.r1], w.z, P);
  }).join("")}"/>`;
  // gauges follow their quantities with a little lag, so a needle swings rather than jumps
  const lag = still.matches ? 1 : 1 - Math.exp(-dt / 0.22);
  gauges.therm += ((state.waterC - 20) / (PLANT.waterC - 20) - gauges.therm) * lag;
  gauges.vac += (state.vacuum - gauges.vac) * lag;
  gauges.air += (state.airHot - gauges.air) * lag;
  for (const d of DATA.dials) needles[d.name].setAttribute("d", needleAt(d, gauges[d.name] * 0.92));
  // lamps and flow marks
  const on = (el, yes) => { if (!el) return; if (yes) el.setAttribute("data-on", ""); else el.removeAttribute("data-on"); };
  on(lamps.extract, state.stage === 1);
  on(lamps.concentrate, state.stage === 2);
  on(lamps.dry, state.stage === 3);
  on(lamps.heat, state.stage === 2 || state.stage === 1);
  const flows = {
    water: state.stage === 1 && state.f < 0.9,
    "extract-a": state.stage === 1 && state.f > 0.08 && state.f < 0.95,
    "extract-b": state.stage === 1 && state.f > 0.1 && state.f < 0.97,
    vapour: state.stage === 2 && state.boiling > 0.3,
    concentrate: state.stage === 3 && state.spraying > 0.3,
    feed: state.stage === 3 && state.spraying > 0.3,
    air: state.stage === 3 && state.airHot > 0.5,
    exhaust: state.stage === 3 && state.airHot > 0.5,
  };
  for (const [name, els] of Object.entries(routeGroups)) for (const el of els) on(el, !!flows[name]);
  if (readout.textContent !== state.readout) readout.textContent = state.readout;
}

function tick(now) {
  const dt = last ? Math.min((now - last) / 1000, 1 / 30) : 1 / 60;
  last = now;
  const calm = still.matches;
  if (touring) { clock += dt; target = tourAt(clock); }
  s = calm ? target : s + (target - s) * (1 - Math.exp(-dt / 0.32));
  if (Math.abs(target - s) < 0.0015) s = target;
  const state = stateAt(s);
  if (!calm) { flowClock += dt; spin += dt * 9 * state.spraying; }
  draw(state, dt);
  const settled = !touring && s === target && state.spraying < 0.02 && state.boiling < 0.02 && Object.values(gauges).every((g) => Math.abs(g - (g > 0.5 ? 1 : 0)) < 0.002 || true);
  frame = visible && !(settled && s === target && !touring && state.spraying === 0 && state.boiling === 0) ? requestAnimationFrame(tick) : 0;
}
const run = () => { if (!frame && visible) { last = 0; frame = requestAnimationFrame(tick); } };
function describe(value) {
  const st = stateAt(value);
  const words = `${st.phase}. ${st.readout.replace(/^[^·]*· /, "")}`;
  stage.setAttribute("aria-valuenow", value.toFixed(2));
  stage.setAttribute("aria-valuetext", words);
  if (document.activeElement === stage && words.split(".")[0] !== said) { said = words.split(".")[0]; status.textContent = said; }
}
function steer(next) {
  touring = false;
  target = clamp(next, 0, 3);
  describe(target);
  clearTimeout(idleTimer);
  idleTimer = setTimeout(() => { touring = !still.matches; clock = 0; run(); }, 3600);
  run();
}
new IntersectionObserver((entries) => { visible = entries[entries.length - 1].isIntersecting; if (visible) run(); }, { rootMargin: "120px 0px" }).observe(stage);
if (still.matches) touring = false;
stage.addEventListener("pointermove", (event) => {
  const box = svg.getBoundingClientRect();
  const share = clamp(((event.clientX - box.left) / box.width - 0.14) / 0.72, 0, 1);
  steer(share * 3);
});
stage.addEventListener("pointerdown", (event) => {
  const box = svg.getBoundingClientRect();
  const share = clamp(((event.clientX - box.left) / box.width - 0.14) / 0.72, 0, 1);
  steer(share * 3);
});
stage.addEventListener("pointerleave", () => steer(target));
stage.addEventListener("focus", () => { if (!said) { said = stateAt(touring ? s : target).phase; status.textContent = said; } });
stage.addEventListener("keydown", (event) => {
  const here = touring ? s : target;
  let to = null;
  if (event.key === "ArrowRight" || event.key === "ArrowUp") to = Math.min(3, Math.floor(here + 1e-6) + 1);
  if (event.key === "ArrowLeft" || event.key === "ArrowDown") to = Math.max(0, Math.ceil(here - 1e-6) - 1);
  if (event.key === "Home") to = 0;
  if (event.key === "End") to = 3;
  if (event.key === "Escape") { to = here; }
  if (to === null) return;
  event.preventDefault();
  if (event.shiftKey && (event.key === "ArrowRight" || event.key === "ArrowLeft")) to = clamp(here + (event.key === "ArrowRight" ? 0.25 : -0.25), 0, 3);
  steer(to);
});
draw(stateAt(0), 1 / 60);
describe(0);
