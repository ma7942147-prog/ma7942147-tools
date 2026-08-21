# -*- coding: utf-8 -*-
"""分離した人声トラックから、実際に歌っている区間と歌い出しを取る。"""
import numpy as np, soundfile as sf

x, sr = sf.read('vrout/song_Vocals.wav')
if x.ndim > 1: x = x.mean(1)
x = x.astype(np.float32)
print(f"vocals: {len(x)/sr:.2f}s  sr={sr}")

hop = 512
n = 1 + (len(x)-2048)//hop
w = np.hanning(2048).astype(np.float32)
St = np.lib.stride_tricks.as_strided(x, (n,2048), (x.strides[0]*hop, x.strides[0]))*w
S = np.abs(np.fft.rfft(St, axis=1))
f = np.fft.rfftfreq(2048, 1/sr)
t = np.arange(n)*hop/sr
band = (f>=150)&(f<=4000)
e = S[:,band].sum(1)
e = e/ (np.percentile(e,99.5)+1e-9)
def sm(a,k):
    k=int(k)|1; return np.convolve(a, np.hanning(k)/np.hanning(k).sum(),'same')
fps = sr/hop
es = sm(e, fps*0.08)
np.save('vocal_env.npy', es.astype(np.float32)); np.save('vocal_t.npy', t.astype(np.float32))

floor = np.percentile(es, 20)
TH = 0.10        # 人声トラックは無歌唱時ほぼ 0.00 なので低く取れる
print(f"floor={floor:.4f} threshold={TH:.4f}")
on = es > TH
def runs(m):
    out=[];s=None
    for i,v in enumerate(m):
        if v and s is None: s=i
        elif not v and s is not None: out.append((s,i)); s=None
    if s is not None: out.append((s,len(m)))
    return out
R=[(a,b) for a,b in runs(on) if t[b-1]-t[a]>0.15]
merged=[]
for a,b in R:
    if merged and t[a]-t[merged[-1][1]-1] < 0.35: merged[-1]=(merged[-1][0],b)
    else: merged.append((a,b))
seg=[(round(float(t[a]),2), round(float(t[b-1]),2)) for a,b in merged if t[b-1]-t[a]>0.35]
np.save('vphr.npy', np.array(seg))
print(f"\n{len(seg)} 個の歌唱句   歌い出し {seg[0][0]}s   歌い終わり {seg[-1][1]}s\n")
prev=0.0
for a,b in seg:
    mk='   <=== 長い休符' if a-prev>3.5 else ''
    print(f"{int(a//60)}:{a%60:05.2f} -> {int(b//60)}:{b%60:05.2f}  len={b-a:4.1f}  gap={a-prev:5.1f}{mk}")
    prev=b
