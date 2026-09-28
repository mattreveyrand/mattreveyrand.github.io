// Exporte la vidéo SVG en images ou en MP4, image par image (rendu déterministe).
//
//   node export.mjs frames 12.5 40 95        # captures PNG aux temps donnés (s)
//   node export.mjs mp4 [largeur]            # vidéo complète, 25 i/s, H.264
//
// Prérequis : playwright (npm i -g playwright) et un ffmpeg ; chemin via $FFMPEG.
import { createRequire } from 'node:module';
import { execSync, spawn } from 'node:child_process';
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const globalRoot = execSync('npm root -g').toString().trim();
const { chromium } = require(path.join(globalRoot, 'playwright'));

const here = path.dirname(fileURLToPath(import.meta.url));
const svgPath = path.join(here, 'manuel-studio-ia.svg');
const { total, fps } = JSON.parse(readFileSync(path.join(here, 'chapters.json'), 'utf8'));
const [mode = 'frames', ...rest] = process.argv.slice(2);

const proxy = process.env.HTTPS_PROXY ? { server: process.env.HTTPS_PROXY } : undefined;
const browser = await chromium.launch({ proxy, executablePath: process.env.CHROMIUM_PATH || undefined });
const width = mode === 'mp4' ? Number(rest[0] || 1920) : 1280;
const page = await browser.newPage({ viewport: { width, height: Math.round(width * 9 / 16) } });

const svg = readFileSync(svgPath, 'utf8');
await page.setContent(`<!doctype html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@700;800&family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:ital,wght@0,400;0,500;0,600;1,400&display=swap">
<style>html,body{margin:0;background:#111418}svg{display:block;width:100vw;height:auto}</style></head>
<body>${svg}</body></html>`, { waitUntil: 'networkidle' });
await page.evaluate(() => document.fonts.ready);
await page.evaluate(() => { const s = document.getElementById('studio-video'); s.pauseAnimations(); s.setCurrentTime(0); });

async function seek(t) {
  await page.evaluate((tt) => document.getElementById('studio-video').setCurrentTime(tt), t);
}

if (mode === 'frames') {
  for (const t of rest.map(Number)) {
    await seek(t);
    const out = path.join(process.env.OUT_DIR || here, `frame-${String(t).replace('.', '_')}.png`);
    await page.screenshot({ path: out });
    console.log(out);
  }
} else if (mode === 'mp4') {
  const ffmpeg = process.env.FFMPEG || 'ffmpeg';
  const out = path.join(here, 'manuel-studio-ia.mp4');
  const ff = spawn(ffmpeg, ['-y', '-f', 'image2pipe', '-framerate', String(fps), '-i', '-',
    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20', '-preset', 'slow',
    '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const n = Math.round(total * fps);
  for (let i = 0; i < n; i++) {
    await seek(i / fps);
    const buf = await page.screenshot({ type: 'png' });
    if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once('drain', r));
    if (i % (fps * 10) === 0) console.log(`${(i / fps).toFixed(0)} s / ${total} s`);
  }
  ff.stdin.end();
  await new Promise((r) => ff.on('close', r));
  console.log(out);
}
await browser.close();
