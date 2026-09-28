"""Select and isolate archived hand-object contact examples for the website.

Only frame and framing are selected. No pose, geometry, or solver result changes.
Candidate ranking is a presentation heuristic, not a contact-success metric.
"""
from pathlib import Path
import argparse
import importlib.util
import hashlib
import json
import sys
import numpy as np
from scipy.spatial import cKDTree

SITE = Path(__file__).resolve().parents[1]
ROOT = SITE.parents[1]
OLD = SITE / '_local/upgrade_20260928_v1'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source-plan', type=Path, default=OLD / 'comparison_plan.json')
parser.add_argument('--output-dir', type=Path, default=SITE / '_local/contact_revision_20260928_v4')
args = parser.parse_args()
OUT = args.output_dir.resolve()
spec = importlib.util.spec_from_file_location('contact_detail_robot', ROOT / 'final_full_pipeline/sharpa_contact_retarget/robot.py')
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

PAIRS = {
    'lint': [('right', 'object_roller')],
    'sweep': [('left', 'object_dustpan'), ('right', 'object_sweeper')],
    'scoop': [('left', 'object_tray'), ('right', 'object_ice_scoop')],
    'pick': [('right', 'object_stapler')],
    'taco-pour': [('left', 'object_target'), ('right', 'object_tool')],
    'taco-ladle': [('left', 'object_target'), ('right', 'object_tool')],
    'taco-pick': [('left', 'object_target'), ('right', 'object_tool')],
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def world_samples(data, parts, poses):
    result = []
    for part, pose in zip(parts, poses):
        vertices = data[part['prefix'] + '_vertices']
        vertices = vertices[np.linspace(0, len(vertices)-1, min(80, len(vertices)), dtype=int)]
        result.append(vertices @ pose[:3,:3].T + pose[:3,3])
    return np.concatenate(result)


rows = []
for original in json.loads(args.source_plan.read_text()):
    name, case = original['name'], original['id']
    if name not in PAIRS and 'contact_pairs' not in original:
        continue
    meta_path = Path(original['inputs'][0]['path'])
    assert sha(meta_path) == original['inputs'][0]['sha256']
    meta = json.loads(meta_path.read_text())
    assert sha(meta['scene']['path']) == meta['scene']['sha256']
    data = dict(np.load(meta['scene']['path'], allow_pickle=False))
    candidate_record = original['inputs'][2]
    assert sha(candidate_record['path']) == candidate_record['sha256']
    candidate = dict(np.load(candidate_record['path'], allow_pickle=False))
    basis = np.asarray(meta['display_basis'])
    models, scores = {}, []
    frames = range(max(10, int(original['frames']*.2)), int(original['frames']*.85), 5)
    for side, object_role in original.get('contact_pairs', PAIRS.get(name, [])):
        hand = ['left', 'right'].index(side)
        parts = [p for p in meta['parts'] if p['role'] == side]
        target = next(p for p in meta['parts'] if p['role'] == object_role)
        robot = module.SharpaHandModel(side, Path(parts[0]['source']).parents[2], load_visuals=True)
        assert len(parts) == len(robot.visual_geometry.mesh_paths) == 28
        assert [Path(p['source']).name for p in parts] == [p.name for p in robot.visual_geometry.mesh_paths]
        models[side] = robot
        for frame in frames:
            before = basis[None] @ candidate['T_world_wrist_pre_episode'][frame,hand][None] @ robot.visual_poses(candidate['q_official_pre_episode'][frame,hand])
            after = np.array([data[p['prefix']+'_poses'][frame] for p in parts])
            a, b = world_samples(data, parts, after), world_samples(data, parts, before)
            obj = data[target['prefix']+'_poses'][frame]
            # Archived object transforms can include scale. Compare in world
            # meters rather than treating every 3x3 block as a rigid rotation.
            object_world = data[target['prefix']+'_vertices'] @ obj[:3,:3].T + obj[:3,3]
            distances = cKDTree(object_world).query(a)[0]
            near = distances < .035
            if near.sum() < 12:
                continue
            score = float(np.quantile(np.linalg.norm(a-b, axis=1)[near], .65))
            scores.append(dict(frame=frame, side=side, object_role=object_role, score=score,
                               nearby_surface_samples=int(near.sum())))
    assert scores, name
    scores.sort(key=lambda row: row['score'], reverse=True)
    chosen = scores[0]
    frame, side = chosen['frame'], chosen['side']
    hand = ['left', 'right'].index(side)
    selected = [p for p in meta['parts'] if p['role'] in [side, chosen['object_role']]]
    hand_parts = [p for p in selected if p['role'] == side]
    robot = models[side]
    before = basis[None] @ candidate['T_world_wrist_pre_episode'][frame,hand][None] @ robot.visual_poses(candidate['q_official_pre_episode'][frame,hand])
    after = basis[None] @ candidate['T_world_wrist_repaired'][frame,hand][None] @ robot.visual_poses(candidate['q_official_repaired'][frame,hand])
    error = max(float(np.max(np.abs(pose-data[p['prefix']+'_poses'][frame]))) for p,pose in zip(hand_parts, after))
    assert error < 1e-7
    folder = OUT / 'prepared' / case
    folder.mkdir(parents=True, exist_ok=True)
    assert not (folder / 'manifest.json').exists(), 'Preserve existing preparation'
    isolated = {}
    for part in selected:
        prefix = part['prefix']
        for key, value in data.items():
            if key.startswith(prefix+'_'):
                isolated[key] = value[frame:frame+1] if key.endswith('_poses') else value
    np.savez_compressed(folder/'scene.npz', **isolated)
    np.savez_compressed(folder/'before_poses.npz', **{p['prefix']: pose for p,pose in zip(hand_parts, before)})
    subset = dict(meta, parts=selected, frames=1, source_frame=frame,
                  scene=dict(path=str(folder/'scene.npz'), sha256=sha(folder/'scene.npz')))
    (folder/'manifest.json').write_text(json.dumps(subset, indent=2)+'\n')
    row = dict(original, frame=0, source_frame=frame, selected_hand=side,
               selected_object=chosen['object_role'], fk_max_error=error,
               complete_hand_parts=28, selection_candidates=scores,
               display_isolation='one complete hand and its object, identical in both states',
               original_scene_sha256=meta['scene']['sha256'],
               isolated_scene_sha256=sha(folder/'scene.npz'),
               poses=dict(path=str(folder/'before_poses.npz'), sha256=sha(folder/'before_poses.npz'), bytes=(folder/'before_poses.npz').stat().st_size),
               before_poses_sha256=sha(folder/'before_poses.npz'))
    rows.append(row)
    print(name, 'frame', frame, side, chosen['object_role'], 'visible correction', round(chosen['score']*1000,1), 'mm', flush=True)
(OUT/'comparison_plan.json').write_text(json.dumps(rows, indent=2)+'\n')
