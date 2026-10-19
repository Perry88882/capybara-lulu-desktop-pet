"""Portable atlas/preview tools for the finished Lulu frames (MIT licensed)."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
STATES = [
    ('idle',[280,110,110,140,140,320]),
    ('running-right',[120]*7+[220]),
    ('running-left',[120]*7+[220]),
    ('waving',[140,140,140,280]),
    ('jumping',[140,140,140,140,280]),
    ('failed',[140]*7+[240]),
    ('waiting',[150]*5+[260]),
    ('running',[120]*5+[220]),
    ('review',[150]*5+[280]),
    ('look-a',[180]*8),('look-b',[180]*8),
]
CELL=(192,208)
SIZE=(1536,2288)

def cell(atlas,row,col):
    return atlas.crop((col*192,row*208,(col+1)*192,(row+1)*208))

def check(path):
    data=path.read_bytes()
    if not 0<len(data)<=20*1024*1024: raise ValueError('Image must be at most 20 MiB')
    with Image.open(path) as opened:
        if opened.format not in {'PNG','WEBP'}: raise ValueError('Expected PNG/WebP')
        if 'A' not in opened.getbands(): raise ValueError('Expected alpha channel')
        atlas=opened.convert('RGBA')
    if atlas.size!=SIZE: raise ValueError(f'Expected {SIZE}, got {atlas.size}')
    for row,(_,durations) in enumerate(STATES):
        for col in range(8):
            alpha=cell(atlas,row,col).getchannel('A')
            if (alpha.getbbox() is not None)!=(col<len(durations)):
                raise ValueError(f'Incorrect populated cell at row {row}, col {col}')
    if atlas.getchannel('A').getextrema()[0]!=0: raise ValueError('Expected transparent padding')
    result={'ok':True,'width':1536,'height':2288,'frames':73,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
    print(json.dumps(result,indent=2))
    return atlas

def build(frames,out):
    atlas=Image.new('RGBA',SIZE)
    for row,(state,durations) in enumerate(STATES):
        files=sorted((frames/state).glob('*.png'))
        if len(files)!=len(durations): raise ValueError(f'{state}: expected {len(durations)} frames, found {len(files)}')
        for col,path in enumerate(files):
            with Image.open(path) as opened: frame=opened.convert('RGBA')
            if frame.size!=CELL: raise ValueError(f'{path}: expected {CELL}')
            atlas.paste(frame,(col*192,row*208))
    out.parent.mkdir(parents=True,exist_ok=True)
    atlas.save(out)
    check(out)

def gif(frames,durations,out):
    frames[0].save(out,save_all=True,append_images=frames[1:],duration=durations,loop=0,disposal=2,optimize=False)

def render(path,out,mp4):
    atlas=check(path)
    out.mkdir(parents=True,exist_ok=True)
    all_frames,all_durations,look_frames=[],[],[]
    grouped={}
    for row,(state,durations) in enumerate(STATES):
        frames=[cell(atlas,row,col) for col in range(len(durations))]
        grouped[state]=frames
        gif(frames,durations,out/f'{state}.gif')
        if row<9:
            all_frames.extend(frames)
            all_durations.extend(durations)
        else: look_frames.extend(frames)
    gif(all_frames,all_durations,out/'all-states.gif')
    gif(look_frames,[180]*16,out/'look-loop.gif')
    transition=grouped['idle']+grouped['jumping']+grouped['idle']
    durations=STATES[0][1]+STATES[4][1]+STATES[0][1]
    gif(transition,durations,out/'idle-jump-idle.gif')
    if mp4:
        import imageio_ffmpeg
        import numpy as np
        writer=imageio_ffmpeg.write_frames(str(out/'all-states.mp4'),CELL,fps=25,codec='libx264',pix_fmt_out='yuv420p',macro_block_size=1)
        writer.send(None)
        try:
            for frame,duration in zip(all_frames,all_durations):
                bg=Image.new('RGBA',CELL,'#f3f4f6')
                bg.alpha_composite(frame)
                rgb=np.asarray(bg.convert('RGB'))
                for _ in range(max(1,round(duration/40))): writer.send(rgb)
        finally: writer.close()
    print(out)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('check',help='Check atlas geometry/occupancy, not full animation semantics')
    p.add_argument('--atlas',type=Path,default=ROOT/'assets/spritesheet.png')
    p=sub.add_parser('build',help='Rebuild atlas from the included final 73 frames')
    p.add_argument('--frames',type=Path,default=ROOT/'assets/frames')
    p.add_argument('--out',type=Path,default=ROOT/'build/spritesheet.png')
    p=sub.add_parser('render',help='Render state GIFs and optional H.264 MP4')
    p.add_argument('--atlas',type=Path,default=ROOT/'assets/spritesheet.png')
    p.add_argument('--out',type=Path,default=ROOT/'build/previews')
    p.add_argument('--mp4',action='store_true')
    args=parser.parse_args()
    if args.command=='check': check(args.atlas)
    elif args.command=='build': build(args.frames,args.out)
    else: render(args.atlas,args.out,args.mp4)

if __name__=='__main__': main()
