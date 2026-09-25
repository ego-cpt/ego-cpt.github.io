// Optional visual/interaction QA through Chrome's built-in DevTools protocol.
// Requires Chrome + Node 22+. No npm install; launches a separate headless profile.
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { existsSync, mkdirSync, mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const site = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const dir = join(site, '_local'); mkdirSync(dir, {recursive: true});
const profile = mkdtempSync(join(dir, 'chrome-'));
const chrome = spawn(process.env.CHROME || '/usr/bin/google-chrome', [
  '--headless=new', '--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage',
  '--no-first-run', '--disable-background-networking', '--remote-debugging-port=0',
  `--user-data-dir=${profile}`, 'about:blank',
], {stdio: 'ignore'});
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const pending = new Map(); let socket, nextId = 1;
const errors = [];
function call(method, params = {}) {
  return new Promise((resolve, reject) => {
    const id = nextId++, timer = setTimeout(() => { pending.delete(id); reject(new Error(`Timed out: ${method}`)); }, 20000);
    pending.set(id, {resolve: (value) => {clearTimeout(timer); resolve(value);}, reject: (err) => {clearTimeout(timer); reject(err);}});
    socket.send(JSON.stringify({id, method, params}));
  });
}
async function evaluate(expression) {
  const result = await call('Runtime.evaluate', {expression, returnByValue: true, awaitPromise: true});
  if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
  return result.result.value;
}
async function shot(name, full = false) {
  const args = {format: 'png', captureBeyondViewport: full};
  if (full) {
    const {cssContentSize: size} = await call('Page.getLayoutMetrics');
    args.clip = {x: 0, y: 0, width: size.width, height: size.height, scale: 1};
  }
  const {data} = await call('Page.captureScreenshot', args);
  writeFileSync(join(dir, name), Buffer.from(data, 'base64'));
}

try {
  const portFile = join(profile, 'DevToolsActivePort');
  for (let i = 0; i < 100 && !existsSync(portFile); i++) await sleep(100);
  assert(existsSync(portFile), 'Headless Chrome did not start');
  const port = readFileSync(portFile, 'utf8').split('\n')[0];
  const tab = await (await fetch(`http://127.0.0.1:${port}/json/new?about:blank`, {method: 'PUT'})).json();
  socket = new WebSocket(tab.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => { socket.onopen = resolve; socket.onerror = reject; });
  socket.onmessage = ({data}) => {
    const result = JSON.parse(data);
    if (result.id && pending.has(result.id)) {
      const task = pending.get(result.id); pending.delete(result.id);
      result.error ? task.reject(new Error(JSON.stringify(result.error))) : task.resolve(result.result);
    }
    if (result.method === 'Runtime.exceptionThrown') errors.push(result.params.exceptionDetails);
    if (result.method === 'Network.responseReceived' && result.params.response.status >= 400) errors.push(result.params.response);
  };
  await call('Page.enable'); await call('Runtime.enable'); await call('Network.enable');
  await call('Emulation.setDeviceMetricsOverride', {width: 1440, height: 1050, deviceScaleFactor: 1, mobile: false});
  await call('Page.navigate', {url: 'http://127.0.0.1:8765/EgoCPT.github.io/'});
  await sleep(2500);
  assert(await evaluate('document.readyState === "complete"'), 'Document not ready');
  assert(await evaluate('document.documentElement.scrollWidth <= window.innerWidth'), 'Desktop overflow');
  await shot('desktop.png');
  await evaluate('document.querySelector("#contacts").scrollIntoView()'); await sleep(500);
  await evaluate('for (const img of document.querySelectorAll(".image-comparison img")) img.loading = "eager"');
  await sleep(700);
  const sliderValue = await evaluate(`(() => {
    const slider = document.querySelector('.image-comparison input');
    slider.value = 25; slider.dispatchEvent(new Event('input', {bubbles: true}));
    return slider.closest('.image-comparison').style.getPropertyValue('--split');
  })()`);
  assert.equal(sliderValue, '25%');
  await shot('comparison.png');
  await evaluate('document.querySelector("#results").scrollIntoView()'); await sleep(1800);
  assert(await evaluate('[...document.querySelectorAll("#results video")].some(v => v.readyState >= 2)'), 'Gallery video not loaded');
  await shot('results.png');
  await evaluate('document.querySelector("#copy-bibtex").click()'); await sleep(300);
  assert(await evaluate('document.querySelector("#copy-status").textContent.length > 0'), 'Copy button feedback missing');
  // Honor keyboard and OS motion preferences without removing native controls.
  await call('Emulation.setEmulatedMedia', {features: [{name: 'prefers-reduced-motion', value: 'reduce'}]});
  await sleep(300);
  assert(await evaluate('[...document.querySelectorAll(".auto-video")].every(v => v.paused)'), 'Reduced motion ignored');
  await call('Emulation.setDeviceMetricsOverride', {width: 390, height: 844, deviceScaleFactor: 1, mobile: true});
  await evaluate('window.scrollTo({top: 0, behavior: "instant"})'); await sleep(500);
  assert(await evaluate('document.documentElement.scrollWidth <= window.innerWidth'), 'Mobile overflow');
  await shot('mobile.png');
  await evaluate('for (const img of document.images) img.loading = "eager"'); await sleep(500);
  const missing = await evaluate('[...document.images].filter(i => !i.complete || !i.naturalWidth).map(i=>i.src)');
  assert.deepEqual(missing, [], 'Broken images');
  assert.deepEqual(errors, [], 'Browser errors');
  const result = {passed: true, desktop_width: 1440, mobile_width: 390, project_subpath: true,
    comparison_slider: true, copy_feedback: true, gallery_playback: true, reduced_motion: true, browser_errors: errors,
    screenshots: ['desktop.png', 'comparison.png', 'results.png', 'mobile.png']};
  writeFileSync(join(dir, 'browser_validation.json'), JSON.stringify(result, null, 2) + '\n');
  console.log(JSON.stringify(result, null, 2));
} finally {
  socket?.close(); chrome.kill('SIGTERM');
}
