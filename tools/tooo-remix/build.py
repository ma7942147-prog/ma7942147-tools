# -*- coding: utf-8 -*-
"""素材を 1920x1080 24fps に正規化。縦・横どの比率でも「拡大してぼかした自分自身」を背景に敷いて 16:9 を埋める。"""
import subprocess, os, json
FF=open('ffpath.txt').read().strip()
P=json.load(open('plan.json')); A=P['assets']; B=P['bounds']; XF=P['xfade']
FPS=24; W,H=1920,1080
BG=("[0:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,"
    "boxblur=34:2,eq=brightness=-0.10:saturation=0.82[bg];"
    "[0:v]scale=1920:1080:force_original_aspect_ratio=decrease[fg];"
    "[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1")
PANS=[(0.06,0.02),(-0.05,0.03),(0.04,-0.03),(-0.04,-0.02),(0.05,0.04),(-0.06,0.02)]
os.makedirs('seg',exist_ok=True); segs=[]
for i,name in enumerate(A):
    dur=B[i+1]-B[i]+(XF if i<len(A)-1 else 0)
    out=f'seg/s{i:02d}.mp4'; segs.append({'f':out,'d':dur})
    if os.path.exists(out): continue
    if name.startswith('clip'):
        cmd=[FF,'-y','-v','error','-i',f'{name}.mp4','-filter_complex',BG+f",fps={FPS}",
             '-t',f'{dur:.3f}','-an','-c:v','libx264','-preset','veryfast','-crf','19',
             '-pix_fmt','yuv420p',out]
    else:
        n=int(round(dur*FPS)); zin=(i%2==0)
        z=f"1+0.14*on/{n}" if zin else f"1.14-0.14*on/{n}"
        px,py=PANS[i%len(PANS)]
        vf=(BG+f",zoompan=z='{z}':x='(iw-iw/zoom)/2+({px})*iw*0.5*on/{n}':"
               f"y='(ih-ih/zoom)/2+({py})*ih*0.5*on/{n}':d={n}:s={W}x{H}:fps={FPS}")
        cmd=[FF,'-y','-v','error','-i',f'{name}.jpg','-filter_complex',vf,'-t',f'{dur:.3f}',
             '-an','-c:v','libx264','-preset','veryfast','-crf','19','-pix_fmt','yuv420p',out]
    r=subprocess.run(cmd,capture_output=True,text=True)
    if r.returncode: print('FAIL',name,r.stderr[-500:]); raise SystemExit(1)
    print(f'{i:02d} {name:6s} {dur:6.2f}s',flush=True)
json.dump(segs,open('segs.json','w'),indent=1)
print('segments ready')
