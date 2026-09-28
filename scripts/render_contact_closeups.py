"""Refine paired still framing using the union of both states in camera space.

The trajectories and recorded 1080p videos stay unchanged. Both comparison
states share one camera fitted to all their mesh bounds, with 10% padding.
"""
from pathlib import Path
import sys

DRIVER = Path(__file__).with_name('render_hd_comparisons.py')
driver = DRIVER.read_text()
fit = '''pair_camera, focal, aperture, _ = camera_pose(comparison_meta)
    basis = pair_camera[:3,:3]
    projected = points @ basis
    center_projected = (projected.min(0)+projected.max(0))/2
    centered = projected-center_projected
    tan_h = aperture/(2*focal)
    tan_v = tan_h*args.height/args.width
    distance = max(np.max(np.abs(centered[:,0])/tan_h+centered[:,2]),
                   np.max(np.abs(centered[:,1])/tan_v+centered[:,2]))*1.10
    pair_camera[:3,3] = basis@center_projected + basis[:,2]*distance'''
extra = f'''
change('indices = np.unique(np.rint(np.linspace(0,count-1,8)).astype(int)).tolist() if args.preview else list(range(count))', 'indices = []')
change('if not args.preview:', 'if False:  # paired stills only; preserve existing videos')
change('pair_camera,_,_,_=camera_pose(comparison_meta)', {fit!r})
'''
marker = 'sys.argv=[str(SOURCE)'
assert driver.count(marker) == 1
driver = driver.replace(marker, extra + '\n' + marker)
sys.argv += ['--output-name', 'closeups']
exec(compile(driver, str(DRIVER), 'exec'), {'__name__': '__main__', '__file__': str(DRIVER)})
