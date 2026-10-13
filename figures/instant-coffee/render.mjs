// Render the idle tour of a built page to an MP4, frame by frame, on a controlled clock.
// node render.mjs [page.html] [--frame=1920x1080] [--fps=30] [--seconds=20.4] [--out=name.mp4]
import { chromium } from "/opt/node22/lib/node_modules/playwright/index.mjs";
import { mkdirSync, rmSync, statSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const args = process.argv.slice(2);
const file = args.find((a) => !a.startsWith("--")) ?? "instant-coffee-video.html";
const opt = (name, fallback) => {
  const hit = args.find((a) => a.startsWith(`--${name}=`));
  return hit ? hit.slice(name.length + 3) : fallback;
};
const fps = Number(opt("fps", 30));
const seconds = Number(opt("seconds", 20.4));
const [fw, fh] = opt("frame", "1920x1080").split("x").map(Number);
const out = opt("out", file.replace(/\.html$/, ".mp4"));
const HERE = dirname(fileURLToPath(import.meta.url));
const frames = join(HERE, "frames");
rmSync(frames, { recursive: true, force: true });
mkdirSync(frames);

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: fw, height: fh }, deviceScaleFactor: 1 });
page.on("pageerror", (error) => console.error("page error:", error.message));
await page.clock.install({ time: 0 });
await page.clock.pauseAt(1); // paused: only runFor advances the page's clock, so screenshots cost no page time
await page.goto(pathToFileURL(resolve(HERE, file)).href);
await page.clock.runFor(16);
const count = Math.round(seconds * fps);
const started = Date.now();
for (let i = 0; i < count; i++) {
  await page.screenshot({ path: join(frames, `f${String(i).padStart(4, "0")}.png`), type: "png" });
  await page.clock.runFor(1000 / fps);
  if (i % 90 === 0) console.log(`frame ${i}/${count} · ${await page.textContent("[data-readout]")}`);
}
await browser.close();
console.log(`${count} frames in ${((Date.now() - started) / 1000).toFixed(0)} s`);
const ff = spawnSync("ffmpeg", ["-y", "-loglevel", "error", "-framerate", String(fps), "-i", join(frames, "f%04d.png"), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "17", "-preset", "slow", "-movflags", "+faststart", join(HERE, out)], { stdio: "inherit" });
if (ff.status !== 0) process.exit(ff.status ?? 1);
rmSync(frames, { recursive: true, force: true });
console.log("wrote", out, `${(statSync(join(HERE, out)).size / 1048576).toFixed(1)} MB`, `${seconds} s at ${fps} fps, ${fw}x${fh}`);
