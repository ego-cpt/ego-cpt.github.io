"""Prepare replacement lint/scoop examples from other archived EgoDex clips.

Run with the sharpa-retarget Python environment. This reads frozen poses and
uses the existing presentation frame selector; it never runs a solver.
"""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

SITE = Path(__file__).resolve().parents[1]
ROOT = SITE.parents[1]
OUT = SITE / '_local/contact_alternates_20260928_v1'
SOURCE = ROOT / 'icra_paper/videos/icra2027_submission_v11/prepared'
CASES = ['lint_03', 'lint_08', 'lint_11', 'lint_41', 'scoop_2151', 'scoop_2238']


def record(path):
    path = Path(path)
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                bytes=path.stat().st_size)


def checked(item, key='path'):
    result = record(item[key])
    assert result['sha256'] == item['sha256'], item[key]
    return result


OUT.mkdir(parents=True, exist_ok=True)
source_plan = OUT / 'source_plan.json'
assert not source_plan.exists(), 'Preserve previous preparations'
rows = []
for case in CASES:
    meta_path = SOURCE / case / 'manifest.json'
    meta = json.loads(meta_path.read_text())
    inputs = [record(meta_path), checked(meta['scene'])]
    candidate = next((r for r in meta['inputs']
                      if Path(r['path']).name == 'reference_episode_candidate.npz'), None)
    receipt_record = None
    if candidate is None:
        receipt = next(r for r in meta['inputs'] if r['path'].endswith('render_inputs.json'))
        receipt_record = checked(receipt)
        provenance = json.loads(Path(receipt['path']).read_text())
        candidate = next(r for r in provenance['source_files']
                         if r['role'] == 'episode:reference_episode_candidate.npz')
        inputs.append(checked(candidate, 'local_path'))
    else:
        inputs.append(checked(candidate))
    if receipt_record:
        inputs.append(receipt_record)
    for side in ['left', 'right']:
        first = next(p for p in meta['parts'] if p['role'] == side)
        urdf_root = Path(first['source']).parents[2]
        inputs.append(record(urdf_root / f'{side}_sharpa_wave/{side}_sharpa_wave.urdf'))
    name = 'lint' if case.startswith('lint') else 'scoop'
    rows.append(dict(name=name, id=case,
                     title=('Lint rolling' if name == 'lint' else 'Scooping') + ' · EgoDex',
                     frames=meta['frames'], fps=meta['fps'], inputs=inputs,
                     contact_pairs=[['right', 'object_roller' if name == 'lint' else 'object_ice_scoop']],
                     before='saved q_official_pre_episode and T_world_wrist_pre_episode',
                     after='archived accepted render-scene poses',
                     objects_unchanged=True, physics_steps=0, solver_runs=0))
source_plan.write_text(json.dumps(rows, indent=2) + '\n')
subprocess.run([sys.executable, str(SITE / 'scripts/prepare_contact_details.py'),
                '--source-plan', str(source_plan), '--output-dir', str(OUT)], check=True)
