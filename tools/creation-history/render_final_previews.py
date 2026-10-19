"""Render preview-only artifacts from the final encoded pet atlas."""
import argparse
import importlib.util
from pathlib import Path

from PIL import Image, ImageDraw

parser = argparse.ArgumentParser()
parser.add_argument('atlas')
parser.add_argument('output')
parser.add_argument('--scripts', required=True)
parser.add_argument('--frames-root')
args = parser.parse_args()
out = Path(args.output)
out.mkdir(parents=True, exist_ok=True)
atlas = Image.open(args.atlas).convert('RGBA')
spec = importlib.util.spec_from_file_location('pet_previews', Path(args.scripts) / 'render_animation_previews.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
frames_root = Path(args.frames_root) if args.frames_root else out / 'frames'
states = list(module.ROW_DURATIONS)
all_frames, all_durations = [], []
state_frames = {}
for row, (state, durations) in enumerate(module.ROW_DURATIONS.items()):
    frames = []
    for col in range(len(durations)):
        frame = atlas.crop((col*192, row*208, (col+1)*192, (row+1)*208))
        target = frames_root / state / f'{col:02}.png'
        target.parent.mkdir(parents=True, exist_ok=True)
        frame.save(target)
        frames.append(frame)
    state_frames[state] = frames
    module.save_preview(frames, durations, out / f'{state}.gif')
    all_frames.extend(frames)
    all_durations.extend(durations)
module.save_preview(all_frames, all_durations, out / 'all-states.gif')
transition = state_frames['idle'] + state_frames['jumping'] + state_frames['idle']
transition_durations = module.ROW_DURATIONS['idle'] + module.ROW_DURATIONS['jumping'] + module.ROW_DURATIONS['idle']
module.save_preview(transition, transition_durations, out / 'idle-jump-idle.gif')
looks = [atlas.crop((col*192, row*208, (col+1)*192, (row+1)*208)) for row in (9,10) for col in range(8)]
module.save_preview(looks, [180]*16, out / 'look-loop.gif')
stills = Image.new('RGB', (192*4, 238), '#f3f4f6')
draw = ImageDraw.Draw(stills)
for index, (label, frame) in enumerate([
    ('Idle', state_frames['idle'][0]),
    ('Wave', state_frames['waving'][2]),
    ('Jump', state_frames['jumping'][2]),
    ('Review', state_frames['review'][2]),
]):
    stills.paste(frame, (index*192, 30), frame)
    draw.text((index*192+10, 8), label, fill='black')
stills.save(out / 'motion-stills.png')

# Encode the same frames into a standard H.264 MP4, when the encoder is installed.
import imageio_ffmpeg
import numpy as np
writer = imageio_ffmpeg.write_frames(str(out / 'all-states.mp4'), (192, 208), fps=25, codec='libx264', pix_fmt_out='yuv420p', macro_block_size=1)
writer.send(None)
for frame, duration in zip(all_frames, all_durations):
    bg = Image.new('RGBA', frame.size, '#f3f4f6')
    bg.alpha_composite(frame)
    rgb = np.asarray(bg.convert('RGB'))
    for _ in range(max(1, round(duration/40))):
        writer.send(rgb)
writer.close()
print(out.resolve())
