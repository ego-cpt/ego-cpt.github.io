"""Install the reviewed contact views and preserve the original two examples."""
from pathlib import Path
import hashlib
import json
import os
import shutil

SITE = Path(__file__).resolve().parents[1]
OUT = SITE / '_local/contact_revision_20260928_v4'
EARLIER = OUT.with_name('contact_revision_20260928_v3')
ANGLES = {'lint': 70, 'sweep': 70, 'scoop': -70, 'pick': 70,
          'taco-pour': 70, 'taco-ladle': 70, 'taco-pick': 70}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


rows = []
for plan in json.loads((OUT/'comparison_plan.json').read_text()):
    name, case = plan['name'], plan['id']
    render_root = OUT if name == 'pick' else EARLIER
    source = render_root/'renders'/case/'detail_report.json'
    report = json.loads(source.read_text())
    assert report['source_frame'] == plan['source_frame']
    assert report['selected_hand'] == plan['selected_hand']
    assert report['selected_object'] == plan['selected_object']
    assert report['maximum_pose_error'] == 0 and report['complete_hand_parts'] == 28
    assert report['physics_steps'] == 0 and not report['pose_edits']
    chosen = next(v for v in report['views'] if v['angle'] == ANGLES[name])
    record = dict(name=name, case=case, source_frame=plan['source_frame'],
                  hand=plan['selected_hand'], object=plan['selected_object'],
                  angle=ANGLES[name], camera=chosen['camera'],
                  render_report=str(source), render_report_sha256=sha(source),
                  before_poses=str(OUT/'prepared'/case/'before_poses.npz'),
                  before_poses_sha256=plan['before_poses_sha256'],
                  scene_sha256=plan['isolated_scene_sha256'], images={})
    for variant in ['before', 'after']:
        image = chosen['images'][variant]
        path = Path(image['path'])
        assert sha(path) == image['sha256']
        target = SITE/'static/images'/f'contact-{name}-focus-{variant}.png'
        if target.exists():
            assert sha(target) == sha(path), 'Preserve existing assets'
        else:
            with path.open('rb') as src, target.open('xb') as dst:
                shutil.copyfileobj(src, dst)
        record['images'][variant] = dict(path=str(target.relative_to(SITE)),
                                       sha256=sha(target), bytes=target.stat().st_size)
    rows.append(record)

paper_sources = json.loads((SITE/'_local/asset_manifest.json').read_text())['records']
originals = []
for name in ['cup-before', 'cup-after', 'grasp-before', 'grasp-after']:
    path = f'static/images/{name}.png'
    record = next(r for r in paper_sources if r['output'] == path)
    assert sha(SITE/path) == record['sha256']
    originals.append(record)
manifest = dict(original_examples=originals, additional_examples=rows,
                physics_steps=0, pose_edits=False, method_results_unchanged=True,
                before_and_after_share_frame_camera_lighting=True)
(OUT/'selected_details.json').write_text(json.dumps(manifest, indent=2)+'\n')

index = SITE/'index.html'
html = index.read_text()
for row in rows:
    for variant in ['before', 'after']:
        old = f"static/images/contact-{row['name']}-{variant}-detail.png"
        new = row['images'][variant]['path']
        assert old in html or new in html
        html = html.replace(old, new)
temp = SITE/'index.next.html'
temp.write_text(html)
os.replace(temp, index)
print('Installed seven reviewed detail pairs; original cup and bottle examples retained.')
