# -*- coding: utf-8 -*-
"""焼き込まれた字幕の切り替わり点を見つけ、1 行につき代表フレームを 1 枚選ぶ。"""
import numpy as np, glob, os
from PIL import Image
fs = sorted(glob.glob('sub_*.jpg'))
FPS = 4.0
arr = []
for f in fs:
    im = Image.open(f).convert('L')
    a = np.asarray(im).astype(np.float32)/255
    arr.append(a)
arr = np.stack(arr)
print('frames', arr.shape)
# 文字は明るい。明るい画素の量と、その配置の変化を見る
txt = (arr > 0.72).astype(np.float32)
amount = txt.reshape(len(txt),-1).mean(1)
diff = np.concatenate([[1.0], np.abs(np.diff(txt,axis=0)).reshape(len(txt)-1,-1).mean(1)])
has = amount > 0.006
segs=[]; s=None
for i in range(len(txt)):
    if has[i] and s is None: s=i
    elif (not has[i]) and s is not None:
        if i-s >= 3: segs.append((s,i))
        s=None
if s is not None and len(txt)-s>=3: segs.append((s,len(txt)))
# 同じ区間の中でも字が変わることがあるので、内部の大きな変化で分割
out=[]
for a,b in segs:
    cut=[a]
    for i in range(a+2,b-1):
        if diff[i] > 0.020 and (i-cut[-1]) >= 4:
            cut.append(i)
    cut.append(b)
    for j in range(len(cut)-1):
        if cut[j+1]-cut[j] >= 3: out.append((cut[j], cut[j+1]))
print(f'{len(out)} 個の字幕区間')
reps=[]
for a,b in out:
    mid = a + (b-a)//2
    reps.append((round(a/FPS,2), round(b/FPS,2), fs[mid]))
with open('subs.txt','w') as fh:
    for i,(t0,t1,f) in enumerate(reps):
        fh.write(f'{i}\t{t0}\t{t1}\t{f}\n')
for i,(t0,t1,f) in enumerate(reps[:60]):
    print(f'{i:3d} {int(t0//60)}:{t0%60:05.2f} -> {int(t1//60)}:{t1%60:05.2f}  ({t1-t0:.1f}s)')
