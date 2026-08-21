import numpy as np
f=np.load('flux2.npy') if False else None
import wave
w=wave.open('song.wav'); sr=w.getframerate()
x=np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(np.float32)/32768
hop=256; win=1024; H=np.hanning(win)
fr=1+(len(x)-win)//hop
S=np.abs(np.fft.rfft(np.lib.stride_tricks.as_strided(x,(fr,win),(x.strides[0]*hop,x.strides[0]))*H,axis=1))
M=np.log1p(S*100)
flux=np.concatenate([[0],np.maximum(0,np.diff(M,axis=0)).sum(1)])
flux=flux-np.convolve(flux,np.ones(87)/87,mode='same'); flux=np.maximum(flux,0)
t=np.arange(fr)*hop/sr
# search tempo & phase
best=None
for bpm in np.arange(100,130,0.05):
    per=60/bpm
    for ph in np.arange(0,per,0.01):
        bt=np.arange(ph,t[-1],per)
        idx=np.clip((bt/ (hop/sr)).astype(int),0,fr-1)
        sc=flux[idx].sum()/len(bt)
        if best is None or sc>best[0]: best=(sc,bpm,ph)
print("best bpm/phase",best)
sc,bpm,ph=best; per=60/bpm
beats=np.arange(ph,t[-1],per)
np.save('beats.npy',beats); print("beats",len(beats),"per",per)
# downbeat: 4-beat grouping, pick offset maximizing flux
vs=np.load('vs.npy'); tv=np.load('tv.npy')
scores=[]
for o in range(4):
    idx=np.clip((beats[o::4]/(hop/sr)).astype(int),0,fr-1)
    scores.append(flux[idx].mean())
o=int(np.argmax(scores)); print("downbeat offset",o,scores)
bars=beats[o::4]
np.save('bars.npy',bars)
vn=vs/np.percentile(vs,98)
print("\nbar  time     vocal-level")
for i,b in enumerate(bars):
    j0=np.argmin(np.abs(tv-b)); j1=np.argmin(np.abs(tv-(b+per*4)))
    seg=vn[j0:j1] if j1>j0 else vn[j0:j0+1]
    print(f"{i:3d} {int(b//60)}:{b%60:05.2f} {seg.mean():5.2f} {'*'*int(seg.mean()*30)}")
