# -*- coding: utf-8 -*-
"""人声トラックと伴奏トラックの比＝分離モデル自身の「ここは声だ」という確信度。
これで歌唱区間を決める（絶対音量のしきい値より遥かに堅い）。
"""
import numpy as np, soundfile as sf
V,sr = sf.read('vrout/song_Vocals.wav');  V = V.mean(1) if V.ndim>1 else V
I,_  = sf.read('vrout/song_Instruments.wav'); I = I.mean(1) if I.ndim>1 else I
n = min(len(V),len(I)); V=V[:n].astype(np.float32); I=I[:n].astype(np.float32)
hop, win = 512, 2048
fr = 1+(n-win)//hop
w = np.hanning(win).astype(np.float32)
def sp(x):
    return np.abs(np.fft.rfft(np.lib.stride_tricks.as_strided(x,(fr,win),(x.strides[0]*hop,x.strides[0]))*w,axis=1))
SV, SI = sp(V), sp(I)
f = np.fft.rfftfreq(win,1/sr); t = np.arange(fr)*hop/sr
bd = (f>=200)&(f<=4500)
ev = SV[:,bd].sum(1); ei = SI[:,bd].sum(1)
ratio = ev/(ev+ei+1e-9)                       # モデルの確信度 0..1
lvl   = ev/np.percentile(ev,99.5)             # 声の大きさ
def sm(a,k):
    k=int(k)|1; return np.convolve(a,np.hanning(k)/np.hanning(k).sum(),'same')
fps = sr/hop
ratio_s = sm(ratio, fps*0.12); lvl_s = sm(lvl, fps*0.10)
np.save('vad_ratio.npy',ratio_s.astype(np.float32)); np.save('vad_lvl.npy',lvl_s.astype(np.float32))
np.save('vad_t.npy',t.astype(np.float32))
print(f"ratio 中央値={np.median(ratio_s):.3f}  90%点={np.percentile(ratio_s,90):.3f}")
print("\n時刻     確信度 音量")
for i in range(0,int(t[-1]),2):
    j0=np.searchsorted(t,i); j1=np.searchsorted(t,i+2)
    r=ratio_s[j0:j1].max(); l=lvl_s[j0:j1].max()
    bar = '#'*int(r*50)
    print(f"{i//60}:{i%60:02d} {r:5.2f} {l:5.2f} {bar}")
