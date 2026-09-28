"""Prepare exact archived before/after poses for presentation, without solving."""
from pathlib import Path
import hashlib,importlib.util,json,sys
import numpy as np

SITE=Path(__file__).resolve().parents[1]
ROOT=SITE.parents[1]
OUT=SITE/'_local/upgrade_20260928_v1'
SOURCE=ROOT/'icra_paper/videos/icra2027_submission_v11'
spec=importlib.util.spec_from_file_location('archived_sharpa_robot',ROOT/'final_full_pipeline/sharpa_contact_retarget/robot.py')
robot_module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=robot_module;spec.loader.exec_module(robot_module)
SharpaHandModel=robot_module.SharpaHandModel

CASES=[('pour','gallery_pour_0','Pouring',90),('lint','gallery_lint_1','Lint rolling',150),
       ('sweep','sweep_test_2','Sweeping',150),('scoop','scoop_1018','Scooping',45),
       ('pick','pick_0','Pick & place',45),('taco-pour','taco_00','Pouring · TACO',96),
       ('taco-ladle','taco_16','Bowl & ladle · TACO',116),
       ('taco-pick','taco_20','Container manipulation · TACO',66)]

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def record(p):return dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size)

def main():
    OUT.mkdir(parents=True,exist_ok=True);rows=[]
    for name,cid,title,frame in CASES:
        src=SOURCE/'prepared'/cid;meta=json.loads((src/'manifest.json').read_text())
        assert sha(src/'scene.npz')==meta['scene']['sha256']
        data=np.load(src/'scene.npz',allow_pickle=False)
        cand=next((r for r in meta['inputs'] if Path(r['path']).name=='reference_episode_candidate.npz'),None)
        if cand is None:
            receipt=json.loads(Path(meta['inputs'][0]['path']).read_text())
            cand=next(r for r in receipt['originals'] if Path(r['path']).name=='reference_episode_candidate.npz')
        cp=Path(cand['path']);assert sha(cp)==cand['sha256']
        candidate=np.load(cp,allow_pickle=False)
        before={};maximum_error=0.;inputs=[record(src/'manifest.json'),record(src/'scene.npz'),record(cp)]
        basis=np.array(meta['display_basis'])
        for hand,side in enumerate(['left','right']):
            parts=[p for p in meta['parts'] if p['role']==side]
            urdf_root=Path(parts[0]['source']).parents[2]
            robot=SharpaHandModel(side,urdf_root,load_visuals=True)
            assert len(parts)==len(robot.visual_geometry.mesh_paths)
            assert [Path(p['source']).name for p in parts]==[p.name for p in robot.visual_geometry.mesh_paths]
            inputs.append(record(robot.urdf_path))
            for phase in ['repaired','pre_episode']:
                poses=basis[None]@candidate['T_world_wrist_'+phase][frame,hand][None]@robot.visual_poses(candidate['q_official_'+phase][frame,hand])
                for part,pose in zip(parts,poses):
                    key=part['prefix']+'_poses'
                    if phase=='repaired':maximum_error=max(maximum_error,float(np.max(np.abs(pose-data[key][frame]))))
                    else:before[part['prefix']]=pose
        assert maximum_error<1e-7,(cid,maximum_error)
        d=OUT/'prepared'/cid;d.mkdir(parents=True,exist_ok=True)
        for file in src.iterdir():
            if file.is_file() and not (d/file.name).exists():(d/file.name).symlink_to(file.resolve())
        np.savez_compressed(d/'before_poses.npz',**before)
        row=dict(name=name,id=cid,title=title,frame=frame,frames=90 if name=='pick' else meta['frames'],
                 fps=meta['fps'],inputs=inputs,before='saved q_official_pre_episode and T_world_wrist_pre_episode',
                 after='archived accepted render-scene poses',fk_max_error=maximum_error,
                 objects_unchanged=True,physics_steps=0,solver_runs=0,poses=record(d/'before_poses.npz'))
        rows.append(row);print(cid,'verified FK',maximum_error,flush=True)
    (OUT/'comparison_plan.json').write_text(json.dumps(rows,indent=2)+'\n')

if __name__=='__main__':main()
