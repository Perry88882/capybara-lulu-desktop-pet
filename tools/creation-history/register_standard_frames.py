"""Apply row-wide scale/ground registration to already extracted generated pixels.

The bundled scripts perform extraction, composition, and acceptance. This small
fit pass leaves enough space for the source jump, matching each row's head size
without independently scaling poses or destroying the jump's vertical motion.
"""
import argparse
import json
from pathlib import Path
from PIL import Image

p = argparse.ArgumentParser()
p.add_argument('frames_root')
p.add_argument('output')
args = p.parse_args()
root, out = Path(args.frames_root), Path(args.output)
manifest = json.loads((root / 'frames-manifest.json').read_text(encoding='utf-8-sig'))

def head_width(frame):
    box = frame.getbbox()
    upper = frame.crop((0, box[1], 192, box[1] + round((box[3]-box[1])*0.60)))
    head_box = upper.getbbox()
    return head_box[2]-head_box[0]

jump = Image.open(root / 'jumping' / '00.png').convert('RGBA')
target = head_width(jump)
report = {'method': 'uniform-row-scaling-about-shared-ground', 'target_head_width': target, 'rows': []}
for row in manifest['rows']:
    state = row['state']
    paths = sorted((root / state).glob('*.png'))
    first = Image.open(paths[0]).convert('RGBA')
    factor = min(1.0, target / head_width(first))
    old_ground = max(Image.open(path).convert('RGBA').getbbox()[3] for path in paths)
    scaled_size = (round(192*factor), round(208*factor))
    offset = (round(96 - 96*factor), round(203-old_ground*factor))
    new_paths = []
    for path in paths:
        frame = Image.open(path).convert('RGBA').resize(scaled_size, Image.Resampling.LANCZOS)
        canvas = Image.new('RGBA', (192,208))
        canvas.alpha_composite(frame, offset)
        dst = out / state / path.name
        dst.parent.mkdir(parents=True,exist_ok=True)
        canvas.save(dst)
        new_paths.append(str(dst.resolve()))
    row['frames'] = new_paths
    report['rows'].append({'state':state,'factor':factor,'source_ground':old_ground,'offset':offset})
out.mkdir(parents=True,exist_ok=True)
(out/'frames-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
(out/'registration.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
