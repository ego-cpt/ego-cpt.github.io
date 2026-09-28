"""Render archived trajectories and paired contact views at 1920 x 1080."""
from pathlib import Path
import sys

SITE=Path(__file__).resolve().parents[1]
ROOT=SITE.parents[1]
OUT=SITE/'_local/upgrade_20260928_v1'
SOURCE=ROOT/'icra_paper/figures/benchmark_isaac_success_examples_v1/render_isaac.py'
code=SOURCE.read_text()

def change(a,b):
    global code
    assert code.count(a)==1,(a,code.count(a))
    code=code.replace(a,b,1)

change('HERE = Path(__file__).resolve().parent',f'HERE = Path({str(OUT)!r})')
change('count = manifest["frames"]','count = min(manifest["frames"], 90) if case_id=="pick_0" else manifest["frames"]')
change('background = np.array([58,68,82], dtype=np.float32)','background = np.array([98,103,109], dtype=np.float32)')
change('"--/app/asyncRendering=false",','"--/app/asyncRendering=false", "--/app/extensions/fsWatcherEnabled=false",')
insert='''
    # Same recorded time, objects, camera, materials and lighting in both views.
    plan=next(r for r in json.loads((HERE/'comparison_plan.json').read_text()) if r['id']==case_id)
    frame=plan['frame']
    with np.load(inp/'before_poses.npz',allow_pickle=False) as before:
        before=dict(before)
    points=[]
    for part,(_,poses) in zip(manifest['parts'],operations):
        pre=part['prefix'];vertices=data[pre+'_vertices']
        low,high=vertices.min(0),vertices.max(0)
        corners=np.array([[x,y,z] for x in [low[0],high[0]] for y in [low[1],high[1]] for z in [low[2],high[2]]])
        for pose in [poses[frame],before.get(pre,poses[frame])]:
            points.append(corners@pose[:3,:3].T+pose[:3,3])
    points=np.concatenate(points)
    comparison_meta=dict(manifest,bounds=[points.min(0).tolist(),points.max(0).tolist()])
    pair_camera,_,_,_=camera_pose(comparison_meta)
    cam.GetOrderedXformOps()[0].Set(Gf.Matrix4d(pair_camera.T.tolist()))
    for variant in ['before','after']:
        for part,(op,poses) in zip(manifest['parts'],operations):
            pose=before.get(part['prefix'],poses[frame]) if variant=='before' else poses[frame]
            op.Set(Gf.Matrix4d(pose.T.tolist()))
            assert np.max(np.abs(np.array(op.Get()).T-pose))<1e-12
        rep.orchestrator.step(rt_subframes=12,delta_time=0.,pause_timeline=True)
        rgba=np.asarray(annotator.get_data(),dtype=np.uint8)
        assert rgba.shape==(1080,1920,4)
        alpha=rgba[...,3:4].astype(np.float32)/255.
        rgb=np.rint(rgba[...,:3]*alpha+background*(1-alpha)).astype(np.uint8)
        Image.fromarray(rgb).save(output/f'{variant}.png')
    (output/'comparison.json').write_text(json.dumps(dict(plan,camera=pair_camera.tolist(),
        before_sha256=digest(output/'before.png'),after_sha256=digest(output/'after.png'),
        width=1920,height=1080,pose_edits=False,physics_steps=0),indent=2)+'\\n')
'''
change('    assert maximum_error < 1e-12',insert+'\n    assert maximum_error < 1e-12')
sys.argv=[str(SOURCE),*sys.argv[1:],'--width','1920','--height','1080']
exec(compile(code,str(SOURCE),'exec'),{'__name__':'__main__','__file__':str(SOURCE)})
