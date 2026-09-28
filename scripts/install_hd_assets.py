"""Install verified native 1080p media without overwriting earlier website assets."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone

SITE = Path(__file__).resolve().parents[1]
ROOT = SITE.parents[1]
OUT = SITE / '_local/upgrade_20260928_v1'
records = []


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def probe(path):
    return json.loads(subprocess.check_output([
        'ffprobe', '-v', 'error', '-select_streams', 'v:0',
        '-show_entries', 'stream=codec_name,width,height,pix_fmt,nb_frames,r_frame_rate,duration',
        '-of', 'json', str(path)]))['streams'][0]


def install(source, name, metadata):
    target = SITE / 'static' / name
    if target.exists():
        assert digest(target) == digest(source), f'Existing asset differs: {target}'
    else:
        with source.open('rb') as src, target.open('xb') as dst:
            shutil.copyfileobj(src, dst)
    records.append(dict(source=str(source.relative_to(ROOT)), source_sha256=digest(source),
                        output=str(target.relative_to(SITE)), sha256=digest(target),
                        bytes=target.stat().st_size, **metadata))


for row in json.loads((OUT / 'comparison_plan.json').read_text()):
    name, case = row['name'], row['id']
    rendered = OUT / 'renders' / case
    report = json.loads((rendered / 'render_report.json').read_text())
    comparison = OUT / 'closeups' / case
    pair = json.loads((comparison / 'comparison.json').read_text())
    assert report['valid'] and report['physics_step_calls'] == 0 and not report['pose_edits']
    assert pair['frame'] == row['frame'] and pair['objects_unchanged']
    movie = rendered / (case + '_isaac.mp4')
    info = probe(movie)
    assert (info['width'], info['height'], info['codec_name'], info['pix_fmt']) == (1920, 1080, 'h264', 'yuv420p')
    assert int(info['nb_frames']) == (90 if name == 'pick' else row['frames'])
    assert digest(movie) == report['video']['sha256']
    install(movie, f'videos/{name}-1080p.mp4', dict(kind='native 1080p archived-pose render', probe=info))
    for variant in ['before', 'after']:
        source = comparison / f'{variant}.png'
        assert digest(source) == pair[f'{variant}_sha256']
        install(source, f'images/contact-{name}-{variant}-detail.png', dict(
            kind='same-camera, same-frame contact comparison', frame=row['frame'], variant=variant,
            width=1920, height=1080, camera=pair['camera']))
    poster = rendered / 'poster.jpg'
    if not poster.exists():
        subprocess.run(['ffmpeg', '-v', 'error', '-nostdin', '-n', '-ss', '1', '-i', str(movie),
                        '-frames:v', '1', '-q:v', '2', '-threads', '2', '-update', '1', str(poster)], check=True)
    install(poster, f'images/{name}-1080p.jpg', dict(kind='native 1080p video frame', time_s=1))

master = ROOT / 'icra_paper/videos/icra2027_submission_v16/light/deliverables/EgoCPT_ICRA_1080p_master.mp4'
info = probe(master)
assert (info['width'], info['height']) == (1920, 1080)
install(master, 'videos/overview-1080p.mp4', dict(kind='byte-identical native 1080p master', probe=info))

# The original D455 clips and their approved crops remain unchanged.
original = json.loads((SITE / '_local/asset_manifest.json').read_text())
hardware = []
for name in ['pour', 'lint', 'sweep']:
    path = SITE / 'static/videos' / f'real-{name}.mp4'
    prior = next(r for r in original['records'] if r['output'] == str(path.relative_to(SITE)))
    assert digest(path) == prior['sha256'], 'Approved real-robot clip changed'
    hardware.append(dict(path=str(path.relative_to(SITE)), sha256=digest(path), probe=probe(path)))

manifest = dict(created_at=datetime.now(timezone.utc).isoformat(), records=records,
                hardware_preserved=hardware, baseline_manifest_sha256=digest(OUT / 'baseline/manifest.json'),
                d455_sources_manifest_sha256=digest(OUT / 'd455_sources/manifest.json'),
                comparison_plan_sha256=digest(OUT / 'comparison_plan.json'),
                render_driver_sha256=digest(SITE / 'scripts/render_hd_comparisons.py'),
                closeup_driver_sha256=digest(SITE / 'scripts/render_contact_closeups.py'),
                prepare_driver_sha256=digest(SITE / 'scripts/prepare_hd_comparisons.py'),
                solver_runs=0, physics_steps=0, public_deployment=False)
dest = OUT / 'hd_asset_manifest_v2.json'
if dest.exists():
    previous = json.loads(dest.read_text())
    assert previous['records'] == manifest['records'], 'Preserve the existing installation record'
else:
    dest.write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps(dict(installed=len(records), manifest=str(dest)), indent=2))
