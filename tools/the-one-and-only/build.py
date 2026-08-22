# -*- coding: utf-8 -*-
"""素材（画像9・動画4）を 1920x1080 24fps の断片に正規化 → xfade で繋ぐ → 歌詞を焼く"""
import subprocess, os, json, math
FF=open('ffpath.txt').read().strip()
XF=0.8; FPS=24; W,H=1920,1080
B=[0.0,16.54,30.78,44.5,54.7,68.94,84.9,100.0,116.0,131.0,145.24,163.5,178.0,192.24,207.4,222.0,236.0,248.0,272.64]
A=['img1','clip2','img7','img8','clip3','img3','img5','img6','img2','clip1','img9','img4','clip4','img6','img5','img1','img3','img8']
assert len(A)==len(B)-1
BG=("[0:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,"
    "boxblur=34:2,eq=brightness=-0.10:saturation=0.82[bg];"
    "[0:v]scale=1920:1080:force_original_aspect_ratio=decrease[fg];"
    "[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1")
PANS=[( 0.06, 0.02),(-0.05, 0.03),( 0.04,-0.03),(-0.04,-0.02),( 0.05, 0.04),(-0.06, 0.02)]
os.makedirs('seg',exist_ok=True)
segs=[]
for i,name in enumerate(A):
    nominal=B[i+1]-B[i]
    dur=nominal+(XF if i<len(A)-1 else 0)
    out=f'seg/s{i:02d}.mp4'; segs.append((out,dur))
    if os.path.exists(out): continue
    if name.startswith('clip'):
        vf=BG+f",fps={FPS},trim=0:{dur:.3f},setpts=PTS-STARTPTS"
        cmd=[FF,'-y','-v','error','-i',f'{name}.mp4','-filter_complex',vf,'-map','[out]'] if False else \
            [FF,'-y','-v','error','-i',f'{name}.mp4','-filter_complex',BG+f",fps={FPS}",'-t',f'{dur:.3f}','-an',
             '-c:v','libx264','-preset','veryfast','-crf','19','-pix_fmt','yuv420p',out]
    else:
        n=int(round(dur*FPS))
        zin = (i%2==0)
        z = f"1+0.14*on/{n}" if zin else f"1.14-0.14*on/{n}"
        px,py=PANS[i%len(PANS)]
        x=f"(iw-iw/zoom)/2+({px})*iw*0.5*on/{n}"
        y=f"(ih-ih/zoom)/2+({py})*ih*0.5*on/{n}"
        vf=(BG+f",zoompan=z='{z}':x='{x}':y='{y}':d={n}:s={W}x{H}:fps={FPS}")
        cmd=[FF,'-y','-v','error','-i',f'{name}.jpg','-filter_complex',vf,'-t',f'{dur:.3f}','-an',
             '-c:v','libx264','-preset','veryfast','-crf','19','-pix_fmt','yuv420p',out]
    r=subprocess.run(cmd,capture_output=True,text=True)
    if r.returncode: print('FAIL',name,r.stderr[-600:]); raise SystemExit(1)
    print(f'{i:02d} {name:6s} {dur:6.2f}s -> {out}',flush=True)
json.dump([{'f':f,'d':d} for f,d in segs],open('segs.json','w'),indent=1)
print('segments done')
