"""Render the presentation-only stapler hold using the original HD setup."""
from pathlib import Path
import sys

SITE = Path(__file__).resolve().parents[1]
ROOT = SITE.parents[1]
OUT = SITE / '_local/pick_held_start_20260928_v1'
SOURCE = ROOT / 'icra_paper/figures/benchmark_isaac_success_examples_v1/render_isaac.py'
code = SOURCE.read_text()


def change(before, after):
    global code
    assert code.count(before) == 1, (before, code.count(before))
    code = code.replace(before, after, 1)


change('HERE = Path(__file__).resolve().parent', f'HERE = Path({str(OUT)!r})')
change('count = manifest["frames"]', 'count = 90')
change('background = np.array([58,68,82], dtype=np.float32)',
       'background = np.array([98,103,109], dtype=np.float32)')
change('"--/app/asyncRendering=false",',
       '"--/app/asyncRendering=false", "--/app/extensions/fsWatcherEnabled=false",')
change('preview_ids = set(np.rint(np.linspace(0,count-1,8)).astype(int).tolist())',
       'preview_ids = set([0, 15, 30, 32, 33, 34, 35, 36, 37, 38, 45, 60, 89])')
change('mode="exact_visual_link_FK_and_object_kinematic_replay", pose_edits=False,',
       'mode="kinematic_presentation_with_stapler_prefix_hold", pose_edits=True,\n'
       '                  presentation_edit=manifest["presentation_edit"],\n'
       f'                  render_driver_sha256=digest({str(Path(__file__).resolve())!r}),')
sys.argv = [str(SOURCE), 'pick_0', *sys.argv[1:], '--width', '1920', '--height', '1080']
exec(compile(code, str(SOURCE), 'exec'), {'__name__': '__main__', '__file__': str(SOURCE)})
