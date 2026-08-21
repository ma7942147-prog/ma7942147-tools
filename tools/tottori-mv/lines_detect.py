# -*- coding: utf-8 -*-
"""歌声区間の検出 → 句の切り出し。
絶対値のしきい値で「そもそも歌っているか」を判定（前奏を除外）し、
その中でだけ局所正規化して句に割る。
"""
import numpy as np
sing = np.load('sing.npy'); t = np.load('tsing.npy')
fps = 1/(t[1]-t[0])

def movq(x, win, q):
    w = int(win*fps)|1; pad = np.pad(x, w//2, mode='edge')
    step = max(1, w//24); idx = np.arange(0, len(x), step)
    vals = np.array([np.percentile(pad[i:i+w], q) for i in idx])
    return np.interp(np.arange(len(x)), idx, vals)

ABS = 0.26                      # 歌っている / いない のゲート
gate = sing > ABS
loc = movq(sing, 14.0, 88)
rel = sing/(loc+1e-9)
on = gate & (rel > 0.50)

def runs(mask):
    out=[]; s=None
    for i,v in enumerate(mask):
        if v and s is None: s=i
        elif not v and s is not None: out.append((s,i)); s=None
    if s is not None: out.append((s,len(mask)))
    return out
R=[(a,b) for a,b in runs(on) if t[b-1]-t[a] > 0.25]
merged=[]
for a,b in R:
    if merged and t[a]-t[merged[-1][1]-1] < 0.55: merged[-1]=(merged[-1][0],b)
    else: merged.append((a,b))
seg=[(float(t[a]),float(t[b-1])) for a,b in merged if t[b-1]-t[a]>0.45]
np.save('phr.npy', np.array(seg))
print(f"{len(seg)} phrases  (歌い出し {seg[0][0]:.2f}s / 歌い終わり {seg[-1][1]:.2f}s)\n")
prev=0.0
for a,b in seg:
    mark = '  <== 段落の頭' if a-prev > 4.5 else ''
    print(f"{int(a//60)}:{a%60:05.2f} -> {int(b//60)}:{b%60:05.2f} len={b-a:4.1f} gap={a-prev:5.1f}{mark}")
    prev=b
