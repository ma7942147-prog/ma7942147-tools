# -*- coding: utf-8 -*-
"""素材 5 本を 1920x1080 24fps の断片に。素材が足りない区間は速度を落として埋める
（この曲の雰囲気ではスローの方がむしろ合う）。縦素材はぼかした自分自身を背景に敷く。"""
import subprocess, os, json
FF=open('ffpath.txt').read().strip()
P=json.load(open('plan.json')); A=P['assets']; B=P['bounds']; XF=P['xfade']
LEN={'clip1':15.04,'clip2':15.04,'clip3':15.04,'clip4':10.04,'clip5':10.04}
BG=("[v0]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,"
    "boxblur=32:2,eq=brightness=-0.12:saturation=0.80[bg];"
    "[v1]scale=1920:1080:force_original_aspect_ratio=decrease[fg];"
    "[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1,fps=24")
os.makedirs('seg',exist_ok=True); segs=[]; used={}
for i,name in enumerate(A):
    dur=B[i+1]-B[i]+(XF if i<len(A)-1 else 0)
    out=f'seg/s{i:02d}.mp4'; segs.append({'f':out,'d':dur})
    if os.path.exists(out): continue
    Lc=LEN[name]; k=used.get(name,0); used[name]=k+1
    # 使い回すたびに切り出し位置をずらす
    start=min(k*1.6, max(0.0, Lc-min(dur,Lc)))
    take=min(Lc-start, dur)
    if dur/take > 2.0:                       # スローが効きすぎるなら頭から全部使う
        start=0.0; take=Lc
    slow=dur/take
    pre=(f"[0:v]trim={start:.3f}:{start+take:.3f},setpts={slow:.4f}*(PTS-STARTPTS),split=2[v0][v1];")
    cmd=[FF,'-y','-v','error','-i',f'{name}.mp4','-filter_complex',pre+BG,
         '-t',f'{dur:.3f}','-an','-c:v','libx264','-preset','veryfast','-crf','19',
         '-pix_fmt','yuv420p',out]
    r=subprocess.run(cmd,capture_output=True,text=True)
    if r.returncode: print('FAIL',name,r.stderr[-500:]); raise SystemExit(1)
    print(f'{i:02d} {name} {dur:6.2f}s  取{start:5.2f}-{start+take:5.2f}s  速度x{1/slow:.2f}',flush=True)
json.dump(segs,open('segs.json','w'),indent=1)
print('segments ready')
