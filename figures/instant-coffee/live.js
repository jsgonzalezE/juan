const DATA = __DATA__;
const P = DATA.P; // LAST comes from the model, inlined before this script
const stage = document.querySelector(".ic-stage");
const svg = stage.querySelector("svg");
const readout = document.querySelector("[data-readout]");
const status = stage.querySelector("[data-status]");
const still = matchMedia("(prefers-reduced-motion: reduce)");
const part = (name) => svg.querySelector(`[data-part="${name}"]`);
const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
const f1 = (v) => Math.round(v * 10) / 10;
const f2 = (v) => Math.round(v * 100) / 100;

// Everything live is data-driven: levels, streams of material, spinners, dials, lamps and flow marks come from the build.
const levelEls = DATA.levels.map((spec) => ({ spec, el: part(spec.part) }));
const bubbles = part("bubbles");
const needles = Object.fromEntries(DATA.dials.map((d) => [d.name, part(d.name)]));
const lamps = Object.fromEntries([...svg.querySelectorAll("[data-lamp]")].map((el) => [el.dataset.lamp, el]));
const routeGroups = Object.fromEntries(DATA.routes.map((name) => [name, [...svg.querySelectorAll(`[data-route="${name}"]`)]]));
const spinnerEls = DATA.spinners.map((spec) => ({ spec, el: part(spec.part), angle: 0 }));
const slabWet = part("slab-wet");
const slabIce = part("slab-ice");
const trayEls = DATA.trays.map((_, n) => ({ ice: part(`tray-ice-${n}`), dry: part(`tray-dry-${n}`) }));
const sublime = part("sublime");
const VIEW = DATA.view;
const lidLive = part("lid-live");
const line = svg.querySelector(".ic-line");

// Streams: a group per stream, appended to the drawing in front of its station (the build placed none, so they ride on top of the line).
const streamLayer = document.createElementNS("http://www.w3.org/2000/svg", "g");
streamLayer.setAttribute("class", "ic-streams");
line.appendChild(streamLayer);
const streams = DATA.streams.map((spec) => {
  const el = document.createElementNS("http://www.w3.org/2000/svg", "g");
  el.setAttribute("class", `iso-dots ic-${spec.tone}`);
  el.setAttribute("data-part", spec.part);
  streamLayer.appendChild(el);
  // arc length table along the polyline, in world units
  const pts = spec.path;
  const cum = [0];
  for (let i = 1; i < pts.length; i++) cum.push(cum[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1], pts[i][2] - pts[i - 1][2]));
  const total = cum[cum.length - 1];
  const seeds = Array.from({ length: spec.count }, (_, i) => ({ phase: (i * 0.618034) % 1, jx: Math.sin(i * 12.9898) * spec.jitter, jy: Math.cos(i * 78.233) * spec.jitter, jz: Math.sin(i * 37.719) * spec.jitter * 0.5 }));
  const along = (d) => {
    d = clamp(d, 0, total);
    let i = 1;
    while (i < cum.length - 1 && cum[i] < d) i++;
    const t = (d - cum[i - 1]) / Math.max(1e-6, cum[i] - cum[i - 1]);
    const a = pts[i - 1];
    const b = pts[i];
    return [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t];
  };
  return { spec, el, total, seeds, along };
});

// The guided tour (video pages): shots with a camera box, a stretch of the batch, the station in focus and a caption.
const SHOTS = DATA.shots;
const TOTAL_SHOTS = SHOTS ? SHOTS.reduce((a, shot) => a + shot.dur, 0) : 0;
const titleEl = document.querySelector("[data-title]");
const subEl = document.querySelector("[data-sub]");
const dims = Object.fromEntries([1, 2, 3, 4, 5, 6, 7, 8].map((k) => [k, 1]));
const CAM_SECONDS = 1.6;
function shotAt(t) {
  let at = t % TOTAL_SHOTS;
  for (let i = 0; i < SHOTS.length; i++) {
    const shot = SHOTS[i];
    if (at <= shot.dur || i === SHOTS.length - 1) return { shot, u: at, prev: SHOTS[(i + SHOTS.length - 1) % SHOTS.length] };
    at -= shot.dur;
  }
  return { shot: SHOTS[0], u: 0, prev: SHOTS[SHOTS.length - 1] };
}
function direct(d) {
  const { shot, u, prev } = d;
  const k = ease(u / CAM_SECONDS);
  const box = shot.cam.map((v, i) => prev.cam[i] + (v - prev.cam[i]) * k);
  svg.setAttribute("viewBox", box.map((v) => v.toFixed(2)).join(" "));
  const out = ease((shot.dur - u) / 0.6);
  const title = shot.title || "";
  const sub = shot.sub || "";
  if (titleEl.textContent !== title) titleEl.textContent = title;
  if (subEl.textContent !== sub) subEl.textContent = sub;
  titleEl.style.opacity = (title ? ease((u - 0.5) / 0.5) * out : 0).toFixed(3);
  subEl.style.opacity = (sub ? ease((u - 0.9) / 0.5) * out : 0).toFixed(3);
}
function focusDraw(focus, dt) {
  const lag = still.matches ? 1 : 1 - Math.exp(-dt / 0.45);
  for (const key of Object.keys(dims)) {
    const want = focus === 0 || focus === Number(key) ? 1 : 0.3;
    dims[key] += (want - dims[key]) * lag;
    if (Math.abs(want - dims[key]) < 0.002) dims[key] = want;
    line.style.setProperty(`--dim${key}`, dims[key].toFixed(3));
  }
}

function levelSvg(spec, share, tone) {
  const h = (spec.z[1] - spec.z[0]) * clamp(share, 0, 1);
  if (h < 0.08) return "";
  return solidSvg(cylinder(spec.cx, spec.cy, spec.r, spec.z[0], h, P, 48), { tone, crease: "none" }).replace(/^<g[^>]*>|<\/g>$/g, "");
}
function slabSvg(x0, x1) {
  if (x1 - x0 < 0.6) return "";
  const s = DATA.slab;
  return solidSvg(slabOf({ x: x0, y: s.y[0], w: x1 - x0, d: s.y[1] - s.y[0], r: 0.3 }, s.z, s.h, P, 2), { tone: "lo", crease: "none" }).replace(/^<g[^>]*>|<\/g>$/g, "");
}
function dotsOf(points, size) {
  return points.map(([x, y, a]) => `<circle cx="${f1(x)}" cy="${f1(y)}" r="${size}"${a !== undefined ? ` fill-opacity="${a.toFixed(2)}"` : ""}/>`).join("");
}
function needleAt(d, value) {
  const a = d.from + d.span * clamp(value, 0, 1);
  return lineOnTop([d.cx - Math.sin(a) * 1.2, d.cy + Math.cos(a) * 1.2], [d.cx + Math.sin(a) * (d.R - 1.9), d.cy - Math.cos(a) * (d.R - 1.9)], d.top + 0.2, P);
}
const BUBBLES = Array.from({ length: 6 }, (_, i) => ({ phase: (i * 0.618034) % 1, dx: ((i % 3) - 1) * 0.5, dy: ((i % 2) - 0.5) * 0.6 }));
// Granules on the trays: a fixed scatter per tray, drawn frosted while frozen and as dry grain once dried.
const TRAY_DOTS = DATA.trays.map((t, n) => Array.from({ length: 26 }, (_, i) => {
  const u = ((i * 0.618034 + n * 0.173) % 1);
  const v = ((i * 0.381966 + n * 0.091) % 1);
  return [t.x0 + 1.5 + (t.x1 - t.x0 - 3) * u, t.y0 + 1.5 + (t.y1 - t.y0 - 3) * v, t.z + 0.3];
}));
const VAPOUR = Array.from({ length: 22 }, (_, i) => ({ phase: (i * 0.618034) % 1, u: (i * 0.381966) % 1, v: (i * 0.173) % 1 }));

let s = 0, target = 0, clock = 0, frame = 0, last = 0, visible = false, touring = !still.matches, idleTimer = 0, flowClock = 0;
let said = "";
const gauges = Object.fromEntries(DATA.dials.map((d) => [d.name, 0]));

// The idle tour (card page): one batch through the line, a pause at the end, then back to the start.
const TOUR = [[0, 1.2], ...Array.from({ length: LAST }, (_, i) => [i + 1, i + 1 === LAST ? 2.6 : 4.2]), [LAST, 1.6], [0, 1.8]];
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
  const share = (key) => (key === "one" ? 1 : state[key] ?? 0);
  for (const { spec, el } of levelEls) el.innerHTML = levelSvg(spec, share(spec.key), spec.tone);
  // bubbles rising in the sight glass while the kettle boils
  if (bubbles && state.boiling > 0.02) {
    const sg = DATA.sight;
    const top = sg.z[0] + (sg.z[1] - sg.z[0]) * state.kettleFill;
    bubbles.innerHTML = dotsOf(BUBBLES.map((b) => {
      const age = (flowClock * 0.55 + b.phase) % 1;
      const z = sg.z[0] + 1 + (top - sg.z[0] - 1.5) * age;
      const p = iso([sg.cx + b.dx, sg.cy + b.dy, z], P);
      return [p[0], p[1], state.boiling * (1 - age * 0.6)];
    }), 0.32);
  } else if (bubbles) bubbles.innerHTML = "";
  // the slab on the freezer belt: liquid until the tunnel, ice after it; it grows from the pour point and is fed off the end
  {
    const sl = DATA.slab;
    const span = sl.xPour - sl.xEnd;
    const x0 = sl.xPour - span * state.slab;
    const x1 = sl.xPour - span * state.slabIn;
    slabWet.innerHTML = slabSvg(Math.max(x0, sl.xTunnel), x1);
    slabIce.innerHTML = slabSvg(x0, Math.min(x1, sl.xTunnel));
  }
  // granules on the dryer trays, frosted then dry, and the vapour leaving them
  {
    const fill = state.trays;
    const dry = state.dried;
    TRAY_DOTS.forEach((dots, n) => {
      const have = clamp(fill * DATA.trays.length - n, 0, 1);
      const els = trayEls[n];
      if (have <= 0.02) { els.ice.innerHTML = ""; els.dry.innerHTML = ""; return; }
      const ice = [];
      const grain = [];
      for (const [x, y, z] of dots) {
        const p = iso([x, y, z], P);
        ice.push([p[0], p[1], have * (1 - dry)]);
        grain.push([p[0], p[1], have * dry]);
      }
      els.ice.innerHTML = dotsOf(ice, 0.42);
      els.dry.innerHTML = dotsOf(grain, 0.42);
    });
    if (state.subliming > 0.02) {
      const ch = DATA.chamber;
      sublime.innerHTML = dotsOf(VAPOUR.map((w) => {
        const age = (flowClock * 0.35 + w.phase) % 1;
        const x = ch.x[0] + (ch.x[1] - ch.x[0]) * w.u + (ch.port[0] - (ch.x[0] + (ch.x[1] - ch.x[0]) * w.u)) * age * 0.6;
        const y = ch.y[0] + (ch.y[1] - ch.y[0]) * w.v + (ch.port[1] - (ch.y[0] + (ch.y[1] - ch.y[0]) * w.v)) * age * 0.6;
        const z = ch.z[0] + (ch.z[1] - ch.z[0]) * age;
        const p = iso([x, y, z], P);
        return [p[0], p[1], state.subliming * (0.3 + 0.7 * (1 - age))];
      }), 0.36);
    } else sublime.innerHTML = "";
  }
  if (lidLive) lidLive.style.opacity = state.capped.toFixed(3);
  // streams of material along their paths, dense only while their key is on
  for (const st of streams) {
    const on = share(st.spec.key);
    if (on < 0.02) { st.el.innerHTML = ""; continue; }
    const pts = [];
    for (const seed of st.seeds) {
      const age = (flowClock * st.spec.speed * 0.5 + seed.phase) % 1;
      const w = st.along(age * st.total);
      const p = iso([w[0] + seed.jx * 0.5, w[1] + seed.jy * 0.5, w[2] + seed.jz], P);
      pts.push([p[0], p[1], on]);
    }
    st.el.innerHTML = dotsOf(pts, st.spec.size);
  }
  // spinners: drum vanes, the cooler arm, roll ends, the granulator rotor and the fan
  for (const sp of spinnerEls) {
    const spec = sp.spec;
    const rate = share(spec.key) * spec.rate;
    if (!still.matches) sp.angle += dt * rate;
    if (!sp.el) continue;
    let d = "";
    if (spec.kind === "spokes") {
      for (let i = 0; i < spec.n; i++) {
        const a = sp.angle + (i * Math.PI * 2) / spec.n;
        const dir = [spec.u[0] * Math.cos(a) + spec.v[0] * Math.sin(a), spec.u[1] * Math.cos(a) + spec.v[1] * Math.sin(a), spec.u[2] * Math.cos(a) + spec.v[2] * Math.sin(a)];
        const p0 = iso([spec.c[0] + dir[0] * spec.r0, spec.c[1] + dir[1] * spec.r0, spec.c[2] + dir[2] * spec.r0], P);
        const p1 = iso([spec.c[0] + dir[0] * spec.r1, spec.c[1] + dir[1] * spec.r1, spec.c[2] + dir[2] * spec.r1], P);
        d += `M${f2(p0[0])} ${f2(p0[1])}L${f2(p1[0])} ${f2(p1[1])}`;
      }
    } else if (spec.kind === "arm") {
      for (let i = 0; i < spec.n; i++) {
        const a = sp.angle + (i * Math.PI * 2) / spec.n;
        const p0 = iso([spec.c[0] + Math.cos(a) * spec.r0, spec.c[1] + Math.sin(a) * spec.r0, spec.c[2]], P);
        const p1 = iso([spec.c[0] + Math.cos(a) * spec.r1, spec.c[1] + Math.sin(a) * spec.r1, spec.c[2]], P);
        d += `M${f2(p0[0])} ${f2(p0[1])}L${f2(p1[0])} ${f2(p1[1])}`;
      }
    } else if (spec.kind === "vanes") {
      // lines along the drum at its rim, only on the side facing the viewer
      for (let i = 0; i < spec.n; i++) {
        const a = sp.angle + (i * Math.PI * 2) / spec.n;
        const dir = [spec.u[0] * Math.cos(a) + spec.v[0] * Math.sin(a), spec.u[1] * Math.cos(a) + spec.v[1] * Math.sin(a), spec.u[2] * Math.cos(a) + spec.v[2] * Math.sin(a)];
        const facing = dir[0] * VIEW[0] + dir[1] * VIEW[1] + dir[2] * VIEW[2];
        if (facing < 0.15) continue;
        const o0 = [spec.o[0] + spec.a[0] * spec.s0 + dir[0] * spec.r, spec.o[1] + spec.a[1] * spec.s0 + dir[1] * spec.r, spec.o[2] + spec.a[2] * spec.s0 + dir[2] * spec.r];
        const o1 = [spec.o[0] + spec.a[0] * spec.s1 + dir[0] * spec.r, spec.o[1] + spec.a[1] * spec.s1 + dir[1] * spec.r, spec.o[2] + spec.a[2] * spec.s1 + dir[2] * spec.r];
        const p0 = iso(o0, P);
        const p1 = iso(o1, P);
        d += `M${f2(p0[0])} ${f2(p0[1])}L${f2(p1[0])} ${f2(p1[1])}`;
      }
    }
    sp.el.innerHTML = d ? `<path class="iso-line" data-tone="lo" d="${d}"/>` : "";
  }
  // gauges follow their quantities with a little lag, so a needle swings rather than jumps
  const lag = still.matches ? 1 : 1 - Math.exp(-dt / 0.22);
  for (const d of DATA.dials) {
    gauges[d.name] += (share(d.key) - gauges[d.name]) * lag;
    needles[d.name].setAttribute("d", needleAt(d, gauges[d.name] * 0.92));
  }
  // lamps and flow marks
  const on = (el, yes) => { if (!el) return; if (yes) el.setAttribute("data-on", ""); else el.removeAttribute("data-on"); };
  for (let i = 1; i <= 8; i++) on(lamps[`s${i}`], state.stage === i);
  const flows = {
    water: state.stage === 3 && state.f < 0.9,
    "extract-a": state.stage === 3 && state.f > 0.08 && state.f < 0.95,
    "extract-b": state.stage === 3 && state.f > 0.1 && state.f < 0.97,
    vapour: state.stage === 4 && state.boiling > 0.3,
    "kettle-out": state.stage === 5 && state.pouring > 0.3,
    concentrate: state.stage === 5 && state.pouring > 0.3,
    "fd-duct": state.stage === 7 && state.subliming > 0.3,
  };
  for (const [name, els] of Object.entries(routeGroups)) for (const el of els) on(el, !!flows[name]);
  if (readout.textContent !== state.readout) readout.textContent = state.readout;
}

function tick(now) {
  const dt = last ? Math.min((now - last) / 1000, 1 / 30) : 1 / 60;
  last = now;
  const calm = still.matches;
  let d = null;
  if (SHOTS) {
    clock += dt;
    d = shotAt(clock);
    const [s0, s1] = d.shot.s;
    target = s0 + (s1 - s0) * ease((d.u / d.shot.dur - 0.08) / 0.84);
  } else if (touring) { clock += dt; target = tourAt(clock); }
  s = calm ? target : s + (target - s) * (1 - Math.exp(-dt / 0.32));
  if (Math.abs(target - s) < 0.0015) s = target;
  const state = stateAt(s);
  if (!calm) flowClock += dt;
  draw(state, dt);
  if (d) direct(d);
  focusDraw(d ? d.shot.focus : state.stage >= 1 && state.stage < LAST ? state.stage : 0, dt);
  const busy = touring || s !== target || state.stage > 0 && state.stage < LAST;
  frame = visible && (SHOTS || busy) ? requestAnimationFrame(tick) : 0;
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
  target = clamp(next, 0, LAST);
  describe(target);
  clearTimeout(idleTimer);
  idleTimer = setTimeout(() => { touring = !still.matches; clock = 0; run(); }, 3600);
  run();
}
const shareAt = (event) => {
  const box = svg.getBoundingClientRect();
  return clamp(((event.clientX - box.left) / box.width - 0.1) / 0.8, 0, 1) * LAST;
};
new IntersectionObserver((entries) => { visible = entries[entries.length - 1].isIntersecting; if (visible) run(); }, { rootMargin: "120px 0px" }).observe(stage);
if (still.matches || SHOTS) touring = false;
if (!SHOTS) stage.addEventListener("pointermove", (event) => steer(shareAt(event)));
if (!SHOTS) stage.addEventListener("pointerdown", (event) => steer(shareAt(event)));
if (!SHOTS) stage.addEventListener("pointerleave", () => steer(target));
stage.addEventListener("focus", () => { if (!said) { said = stateAt(touring ? s : target).phase; status.textContent = said; } });
if (!SHOTS) stage.addEventListener("keydown", (event) => {
  const here = touring ? s : target;
  let to = null;
  if (event.key === "ArrowRight" || event.key === "ArrowUp") to = Math.min(LAST, Math.floor(here + 1e-6) + 1);
  if (event.key === "ArrowLeft" || event.key === "ArrowDown") to = Math.max(0, Math.ceil(here - 1e-6) - 1);
  if (event.key === "Home") to = 0;
  if (event.key === "End") to = LAST;
  if (event.key === "Escape") { to = here; }
  if (to === null) return;
  event.preventDefault();
  if (event.shiftKey && (event.key === "ArrowRight" || event.key === "ArrowLeft")) to = clamp(here + (event.key === "ArrowRight" ? 0.25 : -0.25), 0, LAST);
  steer(to);
});
draw(stateAt(0), 1 / 60);
if (SHOTS) direct(shotAt(0));
focusDraw(0, 1);
describe(0);
