"""Install the two missing TACO tasks and group all five TACO comparisons."""
from pathlib import Path
from html import escape
import argparse
import hashlib
import json
import os
import re
import shutil

SITE = Path(__file__).resolve().parents[1]
OUT = SITE / '_local/taco_contact_additions_20260928_v1'
RESULT = SITE / '_local/taco_five_tasks_20260928_v1'
PARENT = SITE / '_local/contact_alternates_20260928_v1/selected_details.json'
parser = argparse.ArgumentParser(description=__doc__)
for group in ['lint', 'brush']:
    parser.add_argument('--' + group, nargs=2, required=True, metavar=('CASE', 'ANGLE'))
args = parser.parse_args()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


plans = json.loads((OUT / 'comparison_plan.json').read_text())
manifest = json.loads(PARENT.read_text())
manifest['parent_manifest'] = dict(path=str(PARENT), sha256=sha(PARENT))
manifest['new_examples'] = []
index = SITE / 'index.html'
html = index.read_text()
assert 'id="taco-contacts"' not in html, 'Preserve an already installed TACO section'
cards = []
for group in ['lint', 'brush']:
    case, angle = getattr(args, group)
    name = 'taco-' + group
    plan = next(r for r in plans if r['id'] == case and r['name'] == name)
    report_path = OUT / 'renders' / case / 'detail_report.json'
    report = json.loads(report_path.read_text())
    assert report['source_frame'] == plan['source_frame']
    assert report['before_poses_sha256'] == plan['before_poses_sha256']
    assert report['maximum_pose_error'] == 0 and report['complete_hand_parts'] == 28
    assert report['physics_steps'] == 0 and not report['pose_edits']
    view = next(v for v in report['views'] if v['angle'] == int(angle))
    scene = OUT / 'prepared' / case / 'scene.npz'
    before = scene.with_name('before_poses.npz')
    assert sha(scene) == plan['isolated_scene_sha256']
    assert sha(before) == plan['before_poses_sha256']
    row = dict(name=name, title=plan['title'], case=case, source_frame=plan['source_frame'],
               hand=plan['selected_hand'], object=plan['selected_object'], angle=int(angle),
               camera=view['camera'], render_report=str(report_path), render_report_sha256=sha(report_path),
               before_poses=str(before), before_poses_sha256=sha(before), scene_sha256=sha(scene), images={})
    for variant in ['before', 'after']:
        source = Path(view['images'][variant]['path'])
        assert sha(source) == view['images'][variant]['sha256']
        target = SITE / 'static/images' / f'contact-{name}-{case}-view{int(angle)}-{variant}.png'
        if target.exists():
            assert sha(target) == sha(source), 'Preserve existing assets'
        else:
            with source.open('rb') as src, target.open('xb') as dst:
                shutil.copyfileobj(src, dst)
        row['images'][variant] = dict(path=str(target.relative_to(SITE)), sha256=sha(target),
                                       bytes=target.stat().st_size)
    title = escape(plan['title'])
    cards.append(f'''          <article class="task-comparison" data-task="{name}">
            <div class="image-comparison" style="--split:50%">
              <img class="comparison-image" src="{row['images']['after']['path']}" alt="{title}: EgoCPT hand–object contact" loading="lazy" width="1920" height="1080">
              <div class="before-layer"><img class="comparison-image" src="{row['images']['before']['path']}" alt="{title}: input retargeted hand pose at the same time" loading="lazy" width="1920" height="1080"></div>
              <span class="comparison-label-layer label-layer-before"><span class="comparison-label label-before">Before</span></span>
              <span class="comparison-label-layer label-layer-after"><span class="comparison-label label-after">After</span></span>
              <span class="comparison-divider" aria-hidden="true"><span>‹ ›</span></span>
              <input type="range" min="0" max="100" step="0.1" value="50" aria-label="Compare {title} before and after contact optimization" aria-valuetext="50 percent Before, 50 percent After">
            </div>
            <h3 class="detail-title">{title}</h3>
          </article>
''')
    manifest['additional_examples'].append(row)
    manifest['new_examples'].append(name)

pattern = r'          <article class="task-comparison" data-task="taco-[^"]+">.*?          </article>\n'
existing = list(re.finditer(pattern, html, re.S))
assert len(existing) == 3
start, end = existing[0].start(), existing[-1].end()
original_cards = ''.join(m.group(0) for m in existing)
assert html[start:end] == original_cards
section = ('        </div>\n'
           '        <div class="comparison-grid taco-contact-grid" id="taco-contacts" role="group" aria-label="TACO comparisons">\n'
           + original_cards + ''.join(cards))
html = html[:start] + section + html[end:]
for item in manifest['original_examples']:
    assert sha(SITE / item['output']) == item['sha256']
for row in manifest['additional_examples']:
    for item in row['images'].values():
        assert sha(SITE / item['path']) == item['sha256']
manifest['total_comparisons'] = 11
manifest['taco_comparisons'] = 5
manifest['selection_note'] = 'Five TACO task categories, one example each; only lint rolling and surface brushing are added to the original three.'
RESULT.mkdir(parents=True, exist_ok=True)
(RESULT / 'selected_details.json').write_text(json.dumps(manifest, indent=2) + '\n')
temporary = SITE / 'index.next.html'
temporary.write_text(html)
os.replace(temporary, index)
print('Installed two TACO additions: five TACO pairs and eleven comparisons total.')
