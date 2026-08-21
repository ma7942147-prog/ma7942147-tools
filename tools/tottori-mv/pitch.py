# -*- coding: utf-8 -*-
"""F0 の揺れ（ビブラート／グリッサンド）で「人の声」か「声っぽいシンセ」かを判定。"""
import numpy as np, soundfile as sf
V,sr = sf.read('vrout/song_Vocals.wav'); V = V.mean(1) if V.ndim>1 else V
V = V.astype(np.float32)
hop=int(sr*0.010); win=int(sr*0.040)
def f0_track(a,b):
    x=V[int(a*sr):int(b*sr)]
    n=1+(len(x)-win)//hop
    out=[]
    for i in range(n):
        s=x[i*hop:i*hop+win]
        if np.sqrt((s**2).mean())<0.004: out.append(0); continue
        s=s-s.mean()
        ac=np.correlate(s,s,'full')[len(s)-1:]
        ac/= (ac[0]+1e-9)
        lo,hi=int(sr/700),int(sr/110)          # 110-700 Hz
        seg=ac[lo:hi]
        if len(seg)==0 or seg.max()<0.30: out.append(0); continue
        out.append(sr/(lo+int(np.argmax(seg))))
    return np.array(out)
def report(a,b,label):
    f=f0_track(a,b); v=f[f>0]
    if len(v)<20: print(f"{label}: 有声フレーム不足"); return
    c=np.log2(v)
    d=np.diff(c)*1200                            # セント/10ms
    # ビブラート：4-8 Hz の揺れ
    seg=c-np.convolve(c,np.ones(31)/31,'same')
    sp=np.abs(np.fft.rfft(seg*np.hanning(len(seg))))
    fq=np.fft.rfftfreq(len(seg),0.010)
    vib=sp[(fq>3.5)&(fq<9)].sum()/(sp[(fq>0.3)].sum()+1e-9)
    print(f"{label:22s} 有声率={len(v)/len(f):4.2f}  音高変化={np.abs(d).mean():6.1f}cent/10ms  "
          f"ビブラート比={vib:5.3f}  F0中央={np.median(v):5.1f}Hz")
report(36.2,46.8,'0:36-0:47 争点')
report(48.5,58.0,'0:48-0:58 主唱(確定)')
report(68.0,80.0,'1:08-1:20 主唱')
report(8.3,13.1,'0:08-0:13 前奏')
report(23.3,24.5,'0:23 前奏の一声')
