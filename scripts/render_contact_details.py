"""Render complete-hand contact details with three candidate camera views."""
from pathlib import Path
import argparse
import sys

SITE = Path(__file__).resolve().parents[1]
ROOT = SITE.parents[1]
parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('--prepared-root', type=Path, default=SITE / '_local/contact_revision_20260928_v4')
detail_args, render_args = parser.parse_known_args()
OUT = detail_args.prepared_root.resolve()
SOURCE = ROOT / 'icra_paper/figures/benchmark_isaac_success_examples_v1/render_isaac.py'
code = SOURCE.read_text()


def change(old, new):
    global code
    assert code.count(old) == 1, (old, code.count(old))
    code = code.replace(old, new, 1)


change('HERE = Path(__file__).resolve().parent', f'HERE = Path({str(OUT)!r})')
change('"--/app/asyncRendering=false",', '"--/app/asyncRendering=false", "--/app/extensions/fsWatcherEnabled=false",')
change('    material = UsdShade.Material.Define(stage, path)', '''    part = dict(part)
    if part['role'] == 'left': part['color'] = [.22, .52, .84]
    if part['role'] == 'right': part['color'] = [.91, .31, .34]
    material = UsdShade.Material.Define(stage, path)''')
change('0.12 if part["role"] in ("left", "right") else 0.0', '0.06 if part["role"] in ("left", "right") else 0.0')
change('dome.CreateIntensityAttr(550.0)', 'dome.CreateIntensityAttr(650.0)')
change('key.CreateIntensityAttr(650.0)', 'key.CreateIntensityAttr(750.0)')
change('background = np.array([58,68,82], dtype=np.float32)', 'background = np.array([212,213,214], dtype=np.float32)')
change('indices = np.unique(np.rint(np.linspace(0,count-1,8)).astype(int)).tolist() if args.preview else list(range(count))', 'indices = []')
change('if not args.preview:', 'if False:  # paired details only; no video or physics')
capture = '''
    plan = next(r for r in json.loads((HERE/'comparison_plan.json').read_text()) if r['id']==case_id)
    assert digest(inp/'before_poses.npz') == plan['before_poses_sha256']
    before = dict(np.load(inp/'before_poses.npz', allow_pickle=False))
    points = []
    for part, (_, poses) in zip(manifest['parts'], operations):
        pre = part['prefix']; vertices = data[pre+'_vertices']
        low, high = vertices.min(0), vertices.max(0)
        corners = np.array([[x,y,z] for x in [low[0],high[0]] for y in [low[1],high[1]] for z in [low[2],high[2]]])
        for pose in [poses[0], before.get(pre, poses[0])]:
            points.append(corners@pose[:3,:3].T+pose[:3,3])
    points = np.concatenate(points)
    views = []
    for angle in [0, 70, -70]:
        theta = np.deg2rad(angle)
        rotation = np.array([[np.cos(theta),-np.sin(theta),0], [np.sin(theta),np.cos(theta),0], [0,0,1]])
        direction = rotation @ np.asarray(manifest['camera_direction'])
        meta = dict(manifest, bounds=[points.min(0).tolist(),points.max(0).tolist()], camera_direction=direction.tolist())
        camera, focal, aperture, _ = camera_pose(meta)
        basis = camera[:3,:3]; projected = points @ basis
        center = (projected.min(0)+projected.max(0))/2; local = projected-center
        tan_h = aperture/(2*focal); tan_v = tan_h*args.height/args.width
        distance = max(np.max(np.abs(local[:,0])/tan_h+local[:,2]), np.max(np.abs(local[:,1])/tan_v+local[:,2]))*1.07
        camera[:3,3] = basis@center + basis[:,2]*distance
        cam.GetOrderedXformOps()[0].Set(Gf.Matrix4d(camera.T.tolist()))
        item = dict(angle=angle, camera=camera.tolist(), images={})
        for variant in ['before', 'after']:
            for part, (op, poses) in zip(manifest['parts'], operations):
                pose = before.get(part['prefix'],poses[0]) if variant=='before' else poses[0]
                op.Set(Gf.Matrix4d(pose.T.tolist()))
                maximum_error = max(maximum_error, float(np.max(np.abs(np.array(op.Get()).T-pose))))
            rep.orchestrator.step(rt_subframes=12, delta_time=0., pause_timeline=True)
            rgba = np.asarray(annotator.get_data(), dtype=np.uint8)
            assert rgba.shape == (1080,1920,4)
            alpha = rgba[...,3:4].astype(np.float32)/255.
            rgb = np.rint(rgba[...,:3]*alpha+background*(1-alpha)).astype(np.uint8)
            filename = f'{variant}_{angle}.png'
            Image.fromarray(rgb).save(output/filename)
            item['images'][variant] = dict(path=str(output/filename), sha256=digest(output/filename))
        views.append(item)
        print('CONTACT_VIEW', case_id, angle, flush=True)
    (output/'detail_report.json').write_text(json.dumps(dict(plan, views=views,
        pose_edits=False, physics_steps=0, complete_hand_parts=28,
        render_script_sha256=digest(__file__), maximum_pose_error=maximum_error), indent=2)+'\\n')
'''
change('    assert maximum_error < 1e-12', capture+'\n    assert maximum_error < 1e-12')
sys.argv = [str(SOURCE), *render_args, '--width', '1920', '--height', '1080']
exec(compile(code, str(SOURCE), 'exec'), globals())
