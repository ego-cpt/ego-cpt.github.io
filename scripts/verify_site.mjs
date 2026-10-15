// No dependencies. Runs locally and before every GitHub Pages deployment.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { existsSync, lstatSync, readFileSync, readdirSync, statSync } from 'node:fs';
import { dirname, join, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

const site = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const html = readFileSync(join(site, 'index.html'), 'utf8');
const ids = [...html.matchAll(/\bid="([^"]+)"/g)].map((m) => m[1]);
assert.equal(ids.length, new Set(ids).size, 'Duplicate HTML IDs');
let checked = 0;
for (const [, raw] of html.matchAll(/\b(?:src|href|poster|data-src)="([^"]+)"/g)) {
  if (/^https?:\/\//.test(raw)) continue;
  if (raw.startsWith('#')) {
    assert(ids.includes(raw.slice(1)), `Missing fragment target: ${raw}`);
  } else {
    assert(!raw.startsWith('/'), `Root-relative URL breaks project Pages deployment: ${raw}`);
    const path = resolve(site, decodeURIComponent(raw.split(/[?#]/)[0]));
    assert(path.startsWith(site + sep), `Reference leaves website: ${raw}`);
    assert(existsSync(path), `Missing local asset: ${raw}`);
    assert(statSync(path).size > 0, `Empty local asset: ${raw}`);
  }
  checked++;
}
assert(!/gtag\(|googletagmanager|google-analytics|G-PYVRSFMDRL/.test(html), 'Upstream analytics must not be shipped');
assert(!/Albert Author|Bernard D\.|Keunhong Park/.test(html), 'Template authors must be removed');
assert(html.includes('Ant Group') && html.includes('University at Buffalo, SUNY') && html.includes('Stanford University'));
assert(!html.toLowerCase().includes('.pdf'), 'Paper download links are withheld during double-blind review');
const logos = JSON.parse(readFileSync(join(site, 'static/logos/provenance.json'), 'utf8'));
assert.equal(logos.source_page, 'https://ume-exo.github.io/');
assert.equal(logos.assets.length, 3);
for (const logo of logos.assets) {
  assert(html.includes(`src="${logo.path}"`), `Missing affiliation logo: ${logo.path}`);
  const data = readFileSync(join(site, logo.path));
  assert.equal(data.length, logo.bytes, `Logo file size changed: ${logo.path}`);
  assert.equal(createHash('sha256').update(data).digest('hex'), logo.sha256, `Logo no longer matches its recorded source: ${logo.path}`);
}
for (const name of ['Zhixin Sun', 'Kairui Shi', 'Tianao Ren', 'Ming Yang', 'Mark Cutkosky', 'James Jingxi Xu']) assert(html.includes(name));
assert(html.includes('https://nerfies.github.io/'), 'Keep the template attribution');
assert(html.includes('creativecommons.org/licenses/by-sa/4.0'), 'Keep template license');
let bytes = 0, files = 0;
function scan(folder) {
  for (const name of readdirSync(folder)) {
    const file = join(folder, name), stat = lstatSync(file);
    assert(!stat.isSymbolicLink(), `Public asset cannot be a symlink: ${file}`);
    if (stat.isDirectory()) scan(file);
    else {
      assert(!name.toLowerCase().endsWith('.pdf'), `Review manuscript/PDF cannot be published: ${file}`);
      assert(stat.size < 95 * 1024 * 1024, `Asset too large for regular GitHub files: ${file}`);
      assert(!/\.(npz|pt|pth|ckpt|pem|key|env|log)$/.test(name), `Unexpected experiment/secret file: ${file}`);
      bytes += stat.size; files++;
    }
  }
}
scan(join(site, 'static'));
assert(bytes < 250 * 1024 * 1024, 'Keep the website payload small');
console.log(JSON.stringify({passed: true, local_links_checked: checked, static_files: files, static_bytes: bytes}, null, 2));
