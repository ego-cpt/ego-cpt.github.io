"""Prepare the user-requested stapler hold as an isolated presentation edit."""
from pathlib import Path
import hashlib
import json
import shutil

import numpy as np

SITE = Path(__file__).resolve().parents[1]
ROOT = SITE.parents[1]
OUT = SITE / '_local/pick_held_start_20260928_v1'
SOURCE = ROOT / 'icra_paper/videos/icra2027_submission_v11/prepared/pick_0'
ANCHOR = 36  # 1.2 s: visible grasp onset, after the 1.1 s approach requested.
KEY = 'm056_poses'


def record(path):
    return dict(path=str(path), bytes=path.stat().st_size,
                sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def save(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


prepared = OUT / 'prepared/pick_0'
assert not prepared.exists(), 'Preserve prior preparation and render outputs'
prepared.mkdir(parents=True)
baseline = OUT / 'baseline'
baseline.mkdir()
for name in ['index.html', 'README.md']:
    shutil.copy2(SITE / name, baseline / name)
save(baseline / 'static_inventory.json', [record(p) for p in sorted((SITE / 'static').rglob('*')) if p.is_file()])

source_scene = record(SOURCE / 'scene.npz')
assert source_scene['sha256'] == 'c6109fdd26c012c4e015e199715eaa8d8c9b1214bcbd39815e8a3e0d77cd6632'
manifest = json.loads((SOURCE / 'manifest.json').read_text())
assert manifest['fps'] == 30 and manifest['frames'] == 126
assert next(p for p in manifest['parts'] if p['prefix'] == 'm056')['role'] == 'object_stapler'
with np.load(SOURCE / 'scene.npz', allow_pickle=False) as archive:
    original = {k: archive[k] for k in archive.files}
edited = dict(original)
edited[KEY] = original[KEY].copy()
edited[KEY][:ANCHOR] = original[KEY][ANCHOR]
np.savez_compressed(prepared / 'scene.npz', **edited)

# Check the serialized payload, including every hand/geometry array and the
# unchanged original trajectory at and after the selected contact frame.
with np.load(prepared / 'scene.npz', allow_pickle=False) as saved:
    changed = [k for k in original if not np.array_equal(saved[k], original[k])]
    assert changed == [KEY], changed
    poses = saved[KEY]
    assert np.array_equal(poses[ANCHOR:], original[KEY][ANCHOR:])
    assert np.all(poses[:ANCHOR + 1] == original[KEY][ANCHOR])
    assert not np.array_equal(saved['m028_poses'][0], saved['m028_poses'][30])
    handoff_error = float(np.max(np.abs(poses[ANCHOR - 1] - poses[ANCHOR])))
    assert handoff_error == 0

edit = dict(
    kind='user_requested_presentation_hold', object='stapler', array=KEY,
    requested_minimum_hold_s=1.1, anchor_frame_zero_based=ANCHOR,
    anchor_time_s=ANCHOR / manifest['fps'], overwritten_frames_zero_based=[0, ANCHOR - 1],
    original_trajectory_resumes_at_frame=ANCHOR,
    rule='object poses before frame 36 equal the complete frame-36 transform; frames 36+ are original',
    selection='visible grasp onset; nearest hand/object visual vertices are about 2.7 mm apart; not a physics contact test',
    hold_includes_orientation=True, hand_motion_unchanged=True,
    camera_and_materials_unchanged=True, rendered_frame_range_zero_based=[0, 89],
    rendered_fps=30, rendered_duration_s=3.0, source_frame_count=126,
    changed_arrays=changed, unmodified_arrays=len(original) - 1,
    handoff_transform_error=handoff_error,
    source_manifest=record(SOURCE / 'manifest.json'), source_scene=source_scene,
    edited_scene=record(prepared / 'scene.npz'), prepare_script=record(Path(__file__)),
    solver_runs=0, physics_steps=0, public_deployment=False,
)
manifest.update(scene=record(prepared / 'scene.npz'), pose_edits=True, presentation_edit=edit)
save(prepared / 'manifest.json', manifest)
save(OUT / 'edit_manifest.json', edit)
print(json.dumps(dict(prepared=str(prepared), changed_arrays=changed,
                      anchor_frame=ANCHOR, handoff_error=handoff_error), indent=2))
