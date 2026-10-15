// Build a prototype video (an animatic) from one still image per shot: the camera moves over each image
// (push-in, pan, tilt, pull-out) following storyboard.json, a title and a line of caption fade in and out, and
// the shots are joined with short dips to black. The images come from an image generator; this only moves a
// camera over them.
//
// node animatic.mjs [--images=fotos] [--frame=1920x1080] [--out=prototipo.mp4] [--long] [--fps=30]
//   --images  folder with shot-01.png … (jpg/webp also fine); for a vertical frame, shot-01-v.png is used when it exists
//   --long    include the optional shots (the spray-drying route)
import { readFileSync, mkdirSync, rmSync, writeFileSync, existsSync, readdirSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const opt = (name, fallback) => {
  const hit = args.find((a) => a.startsWith(`--${name}=`));
  return hit ? hit.slice(name.length + 3) : fallback;
};
const IMAGES = resolve(HERE, opt("images", "fotos"));
const [FW, FH] = opt("frame", "1920x1080").split("x").map(Number);
const VERTICAL = FH > FW;
const OUT = resolve(HERE, opt("out", `prototipo${VERTICAL ? "-vertical" : ""}.mp4`));
const LONG = args.includes("--long");
const board = JSON.parse(readFileSync(join(HERE, "storyboard.json"), "utf8"));
const FPS = Number(opt("fps", board.fps ?? 30));
const FADE = board.fade ?? 0.4;
const FONT = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf";
const FONT_BOOK = "/usr/share/fonts/opentype/inter/Inter-Regular.otf";
const work = join(HERE, "animatic-work");
rmSync(work, { recursive: true, force: true });
mkdirSync(work);

const run = (cmd, argv) => {
  const r = spawnSync(cmd, argv, { encoding: "utf8" });
  if (r.status !== 0) {
    console.error(r.stderr);
    throw new Error(`${cmd} failed`);
  }
  return r.stdout;
};
const imageFor = (id) => {
  const files = readdirSync(IMAGES);
  const pick = (base) => files.find((f) => f.toLowerCase().startsWith(base.toLowerCase() + ".") && /\.(png|jpe?g|webp)$/i.test(f));
  const v = VERTICAL ? pick(`${id}-v`) : null;
  const h = pick(id);
  const hit = v ?? h;
  return hit ? join(IMAGES, hit) : null;
};
const ONLY = opt("only", "").split(",").filter(Boolean); // --only=shot-01,shot-04 builds just those shots
const shots = board.shots.filter((s) => (LONG || !s.optional) && (!ONLY.length || ONLY.includes(s.id)));
const missing = shots.filter((s) => !imageFor(s.id)).map((s) => s.id);
if (missing.length) {
  console.error(`missing images in ${IMAGES}: ${missing.join(", ")}`);
  process.exit(1);
}

// The working image: the source scaled up (zoompan crops from it, a bigger source keeps the moves smooth)
// and cropped to the frame's aspect, so every camera window has the frame's shape.
const SW = FW * 2;
const SH = FH * 2;
const ease = "(pow(on/(duration-1),2)*(3-2*on/(duration-1)))"; // zoompan names its frame count `duration` inside expressions
const lerp = (a, b) => (a === b ? `${a}` : `(${a}+(${b}-${a})*${ease})`);
const fontSize = (share) => Math.round(Math.min(FW, FH) * share);
// drawtext runs with expansion=none, so a % is literal; only quotes and colons need care inside the filter string
const esc = (s) => s.replace(/\\/g, "\\\\").replace(/'/g, "’").replace(/:/g, "\\:");
const wrap = (text, max) => {
  const words = text.split(" ");
  const lines = [];
  let line = "";
  for (const w of words) {
    if ((line + " " + w).trim().length > max && line) {
      lines.push(line);
      line = w;
    } else line = (line + " " + w).trim();
  }
  if (line) lines.push(line);
  return lines;
};

const segments = [];
shots.forEach((shot, i) => {
  const img = imageFor(shot.id);
  const d = Math.round(shot.dur * FPS);
  const { from, to } = shot.cam;
  // zoom = 1 / width share; the window's top-left follows its centre
  const z = `1/${lerp(from.w, to.w)}`;
  const cx = lerp(from.cx, to.cx);
  const cy = lerp(from.cy, to.cy);
  const x = `min(max(${cx}*iw-iw/zoom/2,0),iw-iw/zoom)`;
  const y = `min(max(${cy}*ih-ih/zoom/2,0),ih-ih/zoom)`;
  const left = Math.round(FW * 0.045);
  const bottom = Math.round(FH * 0.075);
  const titleSize = fontSize(0.044);
  const subSize = fontSize(0.027);
  const subLines = wrap(shot.sub, VERTICAL ? 38 : 70);
  const subBlock = subLines.length * Math.round(subSize * 1.35);
  const fadeText = (start, dur) => `if(lt(t,${start}),0,if(lt(t,${start + 0.5}),(t-${start})/0.5,if(gt(t,${dur - 0.6}),max(0,(${dur}-t)/0.6),1)))`;
  const texts = [];
  // a shade band so the words read over the picture
  texts.push(`drawbox=x=0:y=ih-${Math.round(FH * 0.34)}:w=iw:h=${Math.round(FH * 0.34)}:color=black@0.55:t=fill`);
  texts.push(`drawtext=expansion=none:fontfile=${FONT}:text='${esc(shot.title)}':fontsize=${titleSize}:fontcolor=white:x=${left}:y=h-${bottom + subBlock + Math.round(titleSize * 1.25)}:alpha='${fadeText(0.5, shot.dur)}'`);
  subLines.forEach((line, n) => {
    texts.push(`drawtext=expansion=none:fontfile=${FONT_BOOK}:text='${esc(line)}':fontsize=${subSize}:fontcolor=0xd0d0d0:x=${left}:y=h-${bottom + subBlock - n * Math.round(subSize * 1.35)}:alpha='${fadeText(0.9, shot.dur)}'`);
  });
  const vf = [
    `scale=${SW}:${SH}:force_original_aspect_ratio=increase`,
    `crop=${SW}:${SH}`,
    `zoompan=z='${z}':x='${x}':y='${y}':d=${d}:s=${FW}x${FH}:fps=${FPS}`,
    ...texts,
    `fade=t=in:st=0:d=${FADE}`,
    `fade=t=out:st=${(shot.dur - FADE).toFixed(2)}:d=${FADE}`,
    "format=yuv420p",
  ].join(",");
  const seg = join(work, `${String(i).padStart(2, "0")}-${shot.id}.mp4`);
  console.log(`${shot.id} · ${shot.dur} s · ${shot.title}`);
  run("ffmpeg", ["-y", "-loglevel", "error", "-i", img, "-vf", vf, "-frames:v", String(d), "-r", String(FPS), "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", seg]);
  segments.push(seg);
});
const list = join(work, "list.txt");
writeFileSync(list, segments.map((s) => `file '${s}'`).join("\n"));
run("ffmpeg", ["-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", list, "-c", "copy", "-movflags", "+faststart", OUT]);
rmSync(work, { recursive: true, force: true });
const total = shots.reduce((a, s) => a + s.dur, 0);
console.log(`wrote ${OUT} · ${shots.length} shots · ${total} s · ${FW}x${FH}`);
