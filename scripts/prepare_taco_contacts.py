"""Prepare additional TACO contact examples using frozen scene/candidate poses."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

SITE = Path(__file__).resolve().parents[1]
ROOT = SITE.parents[1]
SOURCE = ROOT / 'icra_paper/videos/icra2027_submission_v11/prepared'
OUT = SITE / '_local/taco_contact_additions_20260928_v1'
GROUPS = {
    'taco-lint': ('Lint rolling · TACO', ['taco_05', 'taco_06', 'taco_07', 'taco_08']),
    'taco-brush': ('Surface brushing · TACO', ['taco_10', 'taco_11', 'taco_12', 'taco_13']),
}


def record(path):
    path = Path(path)
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                bytes=path.stat().st_size)


OUT.mkdir(parents=True, exist_ok=True)
plan = OUT / 'source_plan.json'
assert not plan.exists(), 'Preserve previous preparation'
rows = []
for name, (title, cases) in GROUPS.items():
    for case in cases:
        meta_path = SOURCE / case / 'manifest.json'
        meta = json.loads(meta_path.read_text())
        candidate = next(r for r in meta['inputs']
                         if Path(r['path']).name == 'reference_episode_candidate.npz')
        inputs = [record(meta_path), record(meta['scene']['path']), record(candidate['path'])]
        assert inputs[1]['sha256'] == meta['scene']['sha256']
        assert inputs[2]['sha256'] == candidate['sha256']
        first = next(p for p in meta['parts'] if p['role'] == 'right')
        urdf_root = Path(first['source']).parents[2]
        inputs.append(record(urdf_root / 'right_sharpa_wave/right_sharpa_wave.urdf'))
        rows.append(dict(name=name, id=case, title=title, dataset='TACO',
                         frames=meta['frames'], fps=meta['fps'], inputs=inputs,
                         contact_pairs=[['right', 'object_tool']],
                         before='saved q_official_pre_episode and T_world_wrist_pre_episode',
                         after='archived accepted render-scene poses',
                         objects_unchanged=True, physics_steps=0, solver_runs=0))
plan.write_text(json.dumps(rows, indent=2) + '\n')
subprocess.run([sys.executable, str(SITE / 'scripts/prepare_contact_details.py'),
                '--source-plan', str(plan), '--output-dir', str(OUT)], check=True)
prepared = json.loads((OUT / 'comparison_plan.json').read_text())
shortlist = []
for name in GROUPS:
    candidates = sorted((r for r in prepared if r['name'] == name),
                        key=lambda r: r['selection_candidates'][0]['score'], reverse=True)
    shortlist.extend(dict(name=name, id=r['id'], frame=r['source_frame'],
                          presentation_score=r['selection_candidates'][0]['score'])
                     for r in candidates[:2])
(OUT / 'render_shortlist.json').write_text(json.dumps(shortlist, indent=2) + '\n')
print('Render candidates:', ' '.join(r['id'] for r in shortlist))
