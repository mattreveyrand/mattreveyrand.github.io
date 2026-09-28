// Exporte la vidéo SVG en images ou en MP4, image par image (rendu déterministe).
//
//   node export.mjs frames 12.5 40 95        # captures PNG aux temps donnés (s)
//   node export.mjs mp4 [largeur]            # vidéo complète, 25 i/s, H.264
//   node export.mjs mp4 1920 --workers 3     # nombre de navigateurs en parallèle
//
// Prérequis : playwright (npm i -g playwright) et un ffmpeg ; chemin via $FFMPEG.
//
// Vitesse : plusieurs navigateurs Chromium capturent chacun une image sur N,
// en PNG sans perte encodé « pour la vitesse » (mêmes pixels, fichier plus gros) ;
// un seul ffmpeg reçoit les images dans l'ordre et encode avec des réglages fixes,
// donc la qualité ne dépend pas du nombre de navigateurs.
import { createRequire } from 'node:module';
import { execSync, spawn } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { cpus } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const globalRoot = execSync('npm root -g').toString().trim();
const { chromium } = require(path.join(globalRoot, 'playwright'));

const here = path.dirname(fileURLToPath(import.meta.url));
const svg = readFileSync(path.join(here, 'manuel-studio-ia.svg'), 'utf8');
const { total, fps } = JSON.parse(readFileSync(path.join(here, 'chapters.json'), 'utf8'));

const argv = process.argv.slice(2);
const flag = (name, dflt) => {
  const i = argv.indexOf(name);
  if (i === -1) return dflt;
  const v = argv[i + 1];
  argv.splice(i, 2);
  return v;
};
// Par défaut : un navigateur par cœur, moins un pour ffmpeg (au-delà de 8, le gain devient faible).
const workers = Math.max(1, Number(flag('--workers', Math.max(1, Math.min(8, cpus().length - 1)))));
const [mode = 'frames', ...rest] = argv;
const width = mode === 'mp4' ? Number(rest[0] || 1920) : 1280;
const height = Math.round(width * 9 / 16);

const proxy = process.env.HTTPS_PROXY ? { server: process.env.HTTPS_PROXY } : undefined;
const html = `<!doctype html><html><head><meta charset="utf-8">
<style>html,body{margin:0;background:#111418}svg{display:block;width:100vw;height:auto}</style></head>
<body>${svg}</body></html>`;

// Un navigateur prêt à capturer : le SVG embarque ses polices, rien à télécharger.
async function openRenderer() {
  const browser = await chromium.launch({ proxy, executablePath: process.env.CHROMIUM_PATH || undefined });
  const page = await browser.newPage({ viewport: { width, height } });
  await page.setContent(html);
  await page.evaluate(() => document.fonts.ready);
  await page.evaluate(() => document.getElementById('studio-video').pauseAnimations());
  const cdp = await page.context().newCDPSession(page);
  return {
    browser,
    page,
    async capture(t) {
      await page.evaluate((tt) => document.getElementById('studio-video').setCurrentTime(tt), t);
      const { data } = await cdp.send('Page.captureScreenshot', { format: 'png', optimizeForSpeed: true });
      return Buffer.from(data, 'base64');
    },
  };
}

if (mode === 'frames') {
  const r = await openRenderer();
  for (const t of rest.map(Number)) {
    const out = path.join(process.env.OUT_DIR || here, `frame-${String(t).replace('.', '_')}.png`);
    await r.page.evaluate((tt) => document.getElementById('studio-video').setCurrentTime(tt), t);
    await r.page.screenshot({ path: out });
    console.log(out);
  }
  await r.browser.close();
} else if (mode === 'mp4') {
  const ffmpeg = process.env.FFMPEG || 'ffmpeg';
  const out = path.join(here, 'manuel-studio-ia.mp4');
  const n = Math.round(total * fps);
  const started = Date.now();
  const ff = spawn(ffmpeg, ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-i', '-',
    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20', '-preset', 'slow',
    '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const ffDone = new Promise((resolve, reject) => ff.on('close', (code) => (code === 0 ? resolve() : reject(new Error(`ffmpeg ${code}`)))));

  // Les navigateurs travaillent en avance, mais pas plus de WINDOW images
  // devant la prochaine image à écrire : la mémoire reste bornée.
  const WINDOW = workers * 8;
  const pending = new Map();
  let nextToWrite = 0;
  let waiters = [];
  const wake = () => { const w = waiters; waiters = []; w.forEach((f) => f()); };

  async function flush() {
    while (pending.has(nextToWrite)) {
      const buf = pending.get(nextToWrite);
      pending.delete(nextToWrite);
      if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once('drain', r));
      nextToWrite++;
      if (nextToWrite % (fps * 20) === 0) {
        const secs = (Date.now() - started) / 1000;
        console.log(`${nextToWrite / fps} s / ${total} s · ${(nextToWrite / secs).toFixed(1)} images/s`);
      }
    }
    wake();
  }
  let flushing = Promise.resolve();

  const renderers = await Promise.all(Array.from({ length: workers }, openRenderer));
  await Promise.all(renderers.map(async (r, k) => {
    for (let i = k; i < n; i += workers) {
      while (i >= nextToWrite + WINDOW) await new Promise((res) => waiters.push(res));
      pending.set(i, await r.capture(i / fps));
      flushing = flushing.then(flush);
    }
  }));
  await flushing;
  ff.stdin.end();
  await ffDone;
  await Promise.all(renderers.map((r) => r.browser.close()));
  const secs = (Date.now() - started) / 1000;
  console.log(`${out} · ${n} images en ${secs.toFixed(0)} s (${(n / secs).toFixed(1)} images/s, ${workers} navigateurs)`);
}
