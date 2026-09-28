"""Install the inspected stapler presentation variant, preserving earlier assets."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess

SITE = Path(__file__).resolve().parents[1]
OUT = SITE / '_local/pick_held_start_20260928_v1'
RENDER = OUT / 'renders/pick_0'


def record(path):
    return dict(path=str(path), bytes=path.stat().st_size,
                sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def install(source, target):
    if target.exists():
        assert record(target)['sha256'] == record(source)['sha256'], str(target)
    else:
        with source.open('rb') as src, target.open('xb') as dst:
            shutil.copyfileobj(src, dst)
    return dict(source=record(source), installed=record(target))


report = json.loads((RENDER / 'render_report.json').read_text())
previous = json.loads((SITE / '_local/upgrade_20260928_v1/renders/pick_0/render_report.json').read_text())
assert report['valid'] and report['pose_edits'] and report['physics_step_calls'] == 0
assert report['presentation_edit']['anchor_frame_zero_based'] == 36
assert report['maximum_USD_transform_readback_error'] == 0
assert report['camera'] == previous['camera']
assert report['reference_frames'] == previous['reference_frames'] == list(range(90))
movie = RENDER / 'pick_0_isaac.mp4'
assert record(movie)['sha256'] == report['video']['sha256']
probe = json.loads(subprocess.check_output([
    'ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
    'stream=codec_name,width,height,pix_fmt,nb_frames,r_frame_rate,duration',
    '-of', 'json', str(movie)]))['streams'][0]
assert (probe['width'], probe['height'], probe['codec_name'], probe['pix_fmt']) == (1920, 1080, 'h264', 'yuv420p')
assert int(probe['nb_frames']) == 90 and probe['r_frame_rate'] == '30/1' and float(probe['duration']) == 3

poster = RENDER / 'poster.jpg'
if not poster.exists():
    subprocess.run(['ffmpeg', '-v', 'error', '-nostdin', '-n', '-ss', '1.2', '-i', str(movie),
                    '-frames:v', '1', '-q:v', '2', '-threads', '2', '-update', '1', str(poster)], check=True)
records = [install(movie, SITE / 'static/videos/pick-held-start-1080p.mp4'),
           install(poster, SITE / 'static/images/pick-held-start-1080p.jpg')]

page = SITE / 'index.html'
html = page.read_text()
for kind, ext in [('videos', 'mp4'), ('images', 'jpg')]:
    before = f'static/{kind}/pick-1080p.{ext}'
    after = f'static/{kind}/pick-held-start-1080p.{ext}'
    assert html.count(before) == 1
    html = html.replace(before, after, 1)
before = 'Reconstructed reference trajectories visualized in Isaac Sim. 1× playback; the stapler excerpt ends before hand release.'
after = 'Reconstructed reference trajectories visualized in Isaac Sim at 1×.'
assert html.count(before) == 1
html = html.replace(before, after, 1)
page.write_text(html)

# No prior media is overwritten, including the original stapler video and the
# independently selected Before/After contact comparison.
baseline = json.loads((OUT / 'baseline/static_inventory.json').read_text())
for row in baseline:
    assert record(Path(row['path'])) == row, row['path']
installation = dict(records=records, probe=probe, poster_time_s=1.2,
                    original_assets_preserved=len(baseline), camera_unchanged=True,
                    edit_manifest=record(OUT / 'edit_manifest.json'),
                    render_report=record(RENDER / 'render_report.json'),
                    installer=record(Path(__file__)), page=record(page), public_deployment=False)
with (OUT / 'installation.json').open('x') as stream:
    json.dump(installation, stream, indent=2)
    stream.write('\n')
print(json.dumps(installation, indent=2))
