# -*- coding: utf-8 -*-
import numpy as np
r=np.load('vad_ratio.npy'); l=np.load('vad_lvl.npy'); t=np.load('vad_t.npy')
fps=1/(t[1]-t[0])
on = (r>0.82) & (l>0.18)
def runs(m):
    o=[];s=None
    for i,v in enumerate(m):
        if v and s is None: s=i
        elif not v and s is not None: o.append((s,i)); s=None
    if s is not None: o.append((s,len(m)))
    return o
R=[(a,b) for a,b in runs(on) if t[b-1]-t[a]>0.20]
mg=[]
for a,b in R:
    if mg and t[a]-t[mg[-1][1]-1] < 0.40: mg[-1]=(mg[-1][0],b)
    else: mg.append((a,b))
seg=[(round(float(t[a]),2),round(float(t[b-1]),2)) for a,b in mg if t[b-1]-t[a]>0.35]
np.save('vseg.npy', np.array(seg))
tot=sum(b-a for a,b in seg)
print(f"{len(seg)} 句 / 合計歌唱 {tot:.1f}s / 41行なら 1行 {tot/41:.1f}s\n")
prev=0
for a,b in seg:
    mk='   <=== 長い休符' if a-prev>3.5 else ''
    print(f"{int(a//60)}:{a%60:05.2f} -> {int(b//60)}:{b%60:05.2f} len={b-a:4.1f} gap={a-prev:5.1f}{mk}")
    prev=b
