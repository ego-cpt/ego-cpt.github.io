// Optional, workspace-local asset preparation. No network or hardware access.
// Existing public assets are preserved; original recordings are never changed.
// This bootstraps base assets. Finish with the native-HD preparation/render/
// installation scripts documented in README.md for the current contact gallery.
import { constants, copyFileSync, existsSync, mkdirSync, readFileSync, statSync, writeFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { dirname, join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const site = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const workspace = resolve(site, '../..');
const records = [];
const hash = (path) => createHash('sha256').update(readFileSync(path)).digest('hex');
const v = (n, suffix) => `icra_paper/videos/icra2027_submission_v${n}/${suffix}`;
const generated = 'hardware_sharpa/franka_sharpa_model/generated';
const footage = {
  pour: `${generated}/pour0_hardware_9p5s_20260920_v1/arms_only_runs/pour_cli_replay_20260921T031624Z_3031583/video/replay_rgb.mp4`,
  lint: `${generated}/lint8_right_zup020_15s_20260920_v1/arms_only_runs/dustpan_cli_replay_20260920T095238Z_2950038/video/replay_rgb.mp4`,
  sweep: `${generated}/dustpan2_15s_offline_20260919_v3/arms_only_runs/dustpan_cli_replay_20260920T064501Z_2865496/video/replay_rgb.mp4`,
};

function targetPath(name) {
  const path = join(site, 'static', name);
  mkdirSync(dirname(path), {recursive: true});
  return path;
}

function record(source, output, transform) {
  records.push({
    source: relative(workspace, source), source_sha256: hash(source), source_bytes: statSync(source).size,
    output: relative(site, output), sha256: hash(output), bytes: statSync(output).size, transform,
  });
  console.log(`${relative(site, output)} (${statSync(output).size} bytes)`);
}

function copy(sourceName, destName) {
  const source = resolve(workspace, sourceName), output = targetPath(destName);
  if (!existsSync(output)) copyFileSync(source, output, constants.COPYFILE_EXCL);
  else if (hash(source) !== hash(output)) throw new Error(`Existing asset differs: ${destName}`);
  record(source, output, {method: 'byte-identical copy'});
}

function encode(sourceName, destName, {start = 0, duration, filter = 'scale=1280:-2', crf = 23} = {}) {
  const source = resolve(workspace, sourceName), output = targetPath(destName);
  const args = ['-hide_banner', '-loglevel', 'error', '-nostdin', '-n', '-ss', String(start), '-i', source];
  if (duration !== undefined) args.push('-t', String(duration));
  args.push('-vf', filter, '-an', '-c:v', 'libx264', '-preset', 'medium', '-crf', String(crf),
    '-threads', '4', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', '-map_metadata', '-1', output);
  if (existsSync(output)) throw new Error(`Refusing to overwrite existing encoded asset: ${destName}`);
  execFileSync('ffmpeg', args, {stdio: ['ignore', 'inherit', 'inherit']});
  record(source, output, {method: 'ffmpeg', start_s: start, duration_s: duration ?? null, filter, crf, speed: 1});
}

function poster(videoName, destName, time = 1) {
  const source = targetPath(`videos/${videoName}.mp4`), output = targetPath(`images/${destName}.jpg`);
  if (existsSync(output)) throw new Error(`Refusing to overwrite poster: ${destName}`);
  execFileSync('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-nostdin', '-n', '-ss', String(time), '-i', source,
    '-frames:v', '1', '-vf', 'scale=960:-2', '-q:v', '2', '-threads', '2', '-update', '1', output]);
  record(source, output, {method: 'video frame extraction', time_s: time});
}

// The double-blind review manuscript must not be copied into public assets.
copy('icra_paper/figures/pipeline_v6/pipeline.png', 'images/pipeline.png');
for (const [name, folder, variant] of [
  ['cup-before', 'cup_full', 'initial'], ['cup-after', 'cup_full', 'episode'],
  ['grasp-before', 'bottle_full_+20', 'initial'], ['grasp-after', 'bottle_full_+20', 'episode'],
]) copy(v(6, `assets/details/${folder}/${variant}.png`), `images/${name}.png`);

// Continuous 1x clips, matching the latest approved film's opening time windows.
for (const [name, start, duration] of [['pour', 1, 10], ['lint', 4, 6], ['sweep', 12.5, 6]]) {
  encode(footage[name], `videos/real-${name}.mp4`, {start, duration,
    filter: 'crop=950:535:300:65,scale=960:540:flags=lanczos,setsar=1', crf: 23});
  poster(`real-${name}`, `hero-${name}`, 2);
}

const scenes = {
  pour: 'gallery_pour_0', lint: 'gallery_lint_1', sweep: 'sweep_test_2', scoop: 'scoop_1018',
  'taco-pour': 'taco_00', 'taco-ladle': 'taco_16', 'taco-pick': 'taco_20',
};
for (const [name, sourceId] of Object.entries(scenes)) {
  copy(v(11, `renders/${sourceId}/${sourceId}_isaac.mp4`), `videos/${name}.mp4`);
  poster(name, name);
}
encode(v(11, 'renders/pick_0/pick_0_isaac.mp4'), 'videos/pick.mp4', {duration: 3, filter: 'scale=1280:-2'});
poster('pick', 'pick');
encode(v(16, 'light/deliverables/EgoCPT_success_wall_4K.mp4'), 'videos/success-wall.mp4', {filter: 'scale=1920:1080', crf: 24});
poster('success-wall', 'success-wall', 2);
copy(v(16, 'light/deliverables/EgoCPT_ICRA_1080p_master.mp4'), 'videos/overview-1080p.mp4');
poster('overview-1080p', 'video-poster', 25);

mkdirSync(join(site, '_local'), {recursive: true});
writeFileSync(join(site, '_local', 'asset_manifest.json'), JSON.stringify({
  created_at: new Date().toISOString(), sources_unchanged: true,
  paper_withheld_for_review: true, submission_video_version: 16,
  hardware_mode: 'scripted arms and left hand; right glove teleoperation',
  render_mode: 'archived reconstructed references; not new physics rollouts',
  records,
}, null, 2) + '\n', {flag: 'wx'});
console.log(`Prepared ${records.length} assets. Integrity manifest: _local/asset_manifest.json`);
