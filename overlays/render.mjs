// Render the 2D overlay (overlays/overlay.html, cues from scripts/overlay_cues.py) to an FFV1 .mkv with alpha
// (bgra), one frame per 1/60 s of song time, or single frames as PNG for checks.
//
// Usage:
//   node overlays/render.mjs main|vertical [--from s] [--to s] [--jobs n] [--out file.mkv]
//   node overlays/render.mjs vertical --short <id> [--jobs n]     (one vertical short: its span and opening label)
//   node overlays/render.mjs main|vertical --at t1,t2,... --out dir     (PNG stills for checks)
// main is 3840x2160 for the whole video; vertical is 2160x3840 from S30 (brief, vertical cut).
import { spawn } from "node:child_process";
import { mkdirSync, readFileSync, writeFileSync, rmSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import puppeteer from "puppeteer";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const cues = JSON.parse(readFileSync(join(ROOT, "overlays/cues.json"), "utf8"));
const args = process.argv.slice(2);
const fmt = args[0];
const opt = (k, d) => (args.includes(k) ? args[args.indexOf(k) + 1] : d);
const [W, H] = fmt === "vertical" ? [2160, 3840] : [3840, 2160];
const FPS = cues.fps;
const short = opt("--short", null);
const SH = short && cues.shorts.find(s => s.id === short);
if (short && !SH) throw new Error(`no short ${short}`);
const from = Number(opt("--from", SH ? SH.from : fmt === "vertical" ? cues.vertical_from : 0));
const to = Number(opt("--to", SH ? SH.to : fmt === "vertical" ? cues.s67 : cues.end));
const jobs = Number(opt("--jobs", 6));

async function page(browser) {
  const p = await browser.newPage();
  await p.setViewport({ width: W, height: H, deviceScaleFactor: 1 });
  await p.goto(pathToFileURL(join(ROOT, "overlays/overlay.html")).href);
  const ok = await p.evaluate((c, w, h) => setup(c, w, h), cues, W, H);
  if (!ok) throw new Error("fonts did not load");
  if (short) await p.evaluate(id => setShort(id), short);
  return p;
}

const frame = (p, t) => p.evaluate(t => draw(t) ? cv.toDataURL("image/png").slice(22) : null, t);

async function stills(browser) {
  const out = opt("--out", "renders/overlays/stills");
  mkdirSync(out, { recursive: true });
  const p = await page(browser);
  for (const t of opt("--at", "").split(",").map(Number)) {
    await p.evaluate(t => draw(t), t);
    const b64 = await p.evaluate(() => cv.toDataURL("image/png").slice(22));
    writeFileSync(join(out, `${short ? "short_" + short : fmt}_${t.toFixed(2)}.png`), Buffer.from(b64, "base64"));
  }
}

// One segment: frames [f0, f1) piped as PNG into ffmpeg -> FFV1 bgra.
async function segment(browser, f0, f1, file) {
  const p = await page(browser);
  const blank = await p.evaluate(() => { g.clearRect(0, 0, W, H); return cv.toDataURL("image/png").slice(22); });
  const blankBuf = Buffer.from(blank, "base64");
  const ff = spawn("ffmpeg", ["-v", "error", "-y", "-f", "image2pipe", "-c:v", "png", "-framerate", String(FPS),
                              "-i", "-", "-c:v", "ffv1", "-level", "3", "-pix_fmt", "bgra", "-slices", "16", file],
                   { stdio: ["pipe", "inherit", "inherit"] });
  const done = new Promise((ok, bad) => ff.on("close", c => (c ? bad(new Error(`ffmpeg ${c}`)) : ok())));
  for (let f = f0; f < f1; f++) {
    const b64 = await frame(p, f / FPS);
    const buf = b64 ? Buffer.from(b64, "base64") : blankBuf;
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once("drain", r));
  }
  ff.stdin.end();
  await done;
  await p.close();
}

async function video(browser) {
  const out = opt("--out", short ? `renders/overlays/overlay_short_${short}.mkv` : `renders/overlays/overlay_${fmt}.mkv`);
  const tmp = `${out}.parts`;
  mkdirSync(tmp, { recursive: true });
  const F0 = Math.round(from * FPS), F1 = Math.round(to * FPS);
  const n = Math.ceil((F1 - F0) / jobs);
  const parts = [];
  for (let k = 0; k < jobs; k++) {
    const a = F0 + k * n, b = Math.min(F1, a + n);
    if (a < b) parts.push([a, b, join(tmp, `part${k}.mkv`)]);
  }
  const t = Date.now();
  await Promise.all(parts.map(([a, b, f]) => segment(browser, a, b, f)));
  writeFileSync(join(tmp, "list.txt"), parts.map(([, , f]) => `file '${resolve(f)}'`).join("\n") + "\n");
  await new Promise((ok, bad) => spawn("ffmpeg", ["-v", "error", "-y", "-f", "concat", "-safe", "0", "-i",
                                                   join(tmp, "list.txt"), "-c", "copy", out], { stdio: "inherit" })
    .on("close", c => (c ? bad(new Error(`concat ${c}`)) : ok())));
  rmSync(tmp, { recursive: true });
  console.log(`overlay ${fmt}: frames ${F0}..${F1 - 1} (${(F1 - F0)} at ${FPS} fps, from ${from.toFixed(3)} s) -> ${out} in ${((Date.now() - t) / 1000).toFixed(0)} s`);
}

// --no-sandbox as the project's other Puppeteer scripts: this Ubuntu blocks Chrome's user-namespace sandbox, and the
// page only loads local project files.
const browser = await puppeteer.launch({ headless: "shell", args: ["--no-sandbox", "--allow-file-access-from-files"] });
try {
  if (args.includes("--at")) await stills(browser); else await video(browser);
} finally {
  await browser.close();
}
