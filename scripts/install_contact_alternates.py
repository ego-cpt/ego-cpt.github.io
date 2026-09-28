"""Install two visually reviewed replacement clips without changing other cards."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import shutil

SITE = Path(__file__).resolve().parents[1]
OUT = SITE / '_local/contact_alternates_20260928_v1'
PREVIOUS = SITE / '_local/contact_revision_20260928_v4/selected_details.json'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--lint', nargs=2, required=True, metavar=('CASE', 'ANGLE'))
parser.add_argument('--scoop', nargs=2, required=True, metavar=('CASE', 'ANGLE'))
args = parser.parse_args()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


plans = json.loads((OUT / 'comparison_plan.json').read_text())
manifest = json.loads(PREVIOUS.read_text())
manifest['parent_manifest'] = dict(path=str(PREVIOUS), sha256=sha(PREVIOUS))
manifest['replaced_examples'] = []
html = (SITE / 'index.html').read_text()
for name in ['lint', 'scoop']:
    case, angle = getattr(args, name)
    plan = next(r for r in plans if r['id'] == case and r['name'] == name)
    report_path = OUT / 'renders' / case / 'detail_report.json'
    report = json.loads(report_path.read_text())
    assert report['maximum_pose_error'] == 0 and report['complete_hand_parts'] == 28
    assert report['physics_steps'] == 0 and not report['pose_edits']
    assert report['source_frame'] == plan['source_frame']
    assert report['before_poses_sha256'] == plan['before_poses_sha256']
    view = next(v for v in report['views'] if v['angle'] == int(angle))
    before = OUT / 'prepared' / case / 'before_poses.npz'
    scene = OUT / 'prepared' / case / 'scene.npz'
    assert sha(before) == plan['before_poses_sha256']
    assert sha(scene) == plan['isolated_scene_sha256']
    row = dict(name=name, case=case, source_frame=plan['source_frame'],
               hand=plan['selected_hand'], object=plan['selected_object'],
               angle=int(angle), camera=view['camera'], render_report=str(report_path),
               render_report_sha256=sha(report_path), before_poses=str(before),
               before_poses_sha256=sha(before), scene_sha256=sha(scene), images={})
    for variant in ['before', 'after']:
        source = Path(view['images'][variant]['path'])
        assert sha(source) == view['images'][variant]['sha256']
        target = SITE / 'static/images' / f'contact-{case.replace("_", "-")}-view{int(angle)}-{variant}.png'
        if target.exists():
            assert sha(target) == sha(source), 'Preserve existing assets'
        else:
            with source.open('rb') as src, target.open('xb') as dst:
                shutil.copyfileobj(src, dst)
        row['images'][variant] = dict(path=str(target.relative_to(SITE)),
                                       sha256=sha(target), bytes=target.stat().st_size)
    index = next(i for i, r in enumerate(manifest['additional_examples']) if r['name'] == name)
    manifest['replaced_examples'].append(manifest['additional_examples'][index])
    manifest['additional_examples'][index] = row
    pattern = rf'(<article class="task-comparison" data-task="{name}">)(.*?)(</article>)'
    matches = list(re.finditer(pattern, html, re.S))
    assert len(matches) == 1
    match = matches[0]
    card = match.group(0)
    for variant in ['before', 'after']:
        card, count = re.subn(rf'src="static/images/contact-{name}[^\"]*-{variant}\.png"',
                              f'src="{row["images"][variant]["path"]}"', card)
        assert count == 1, (name, variant, count)
    html = html[:match.start()] + card + html[match.end():]

for record in manifest['original_examples']:
    assert sha(SITE / record['output']) == record['sha256']
for row in manifest['additional_examples']:
    for record in row['images'].values():
        assert sha(SITE / record['path']) == record['sha256']
(OUT / 'selected_details.json').write_text(json.dumps(manifest, indent=2) + '\n')
temporary = SITE / 'index.next.html'
temporary.write_text(html)
os.replace(temporary, SITE / 'index.html')
print('Installed lint and scoop replacements; all nine paired images verified.')
