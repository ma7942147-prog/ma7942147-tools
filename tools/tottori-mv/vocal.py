import wave, numpy as np
w=wave.open('stereo.wav'); sr=w.getframerate()
d=np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(np.float32)/32768
d=d.reshape(-1,2); L,R=d[:,0],d[:,1]
hop=512; win=2048; H=np.hanning(win)
def spec(x):
    fr=1+(len(x)-win)//hop
    st=np.lib.stride_tricks.as_strided(x,(fr,win),(x.strides[0]*hop,x.strides[0]))*H
    return np.abs(np.fft.rfft(st,axis=1))
SL,SR=spec(L),spec(R)
f=np.fft.rfftfreq(win,1/sr)
mid=(SL+SR)/2; side=np.abs(SL-SR)/2
band=(f>=200)&(f<=3500)
v=np.maximum(0,(mid[:,band]-1.0*side[:,band])).mean(1)
t=np.arange(len(v))*hop/sr
def sm(a,k): 
    k=k|1; return np.convolve(a,np.hanning(k)/np.hanning(k).sum(),mode='same')
vs=sm(v,21)
np.save('vs.npy',vs); np.save('tv.npy',t)
vn=vs/np.percentile(vs,98)
# print 0.25s resolution bars
for i in range(0,int(t[-1]*4)):
    ti=i/4; j=np.argmin(np.abs(t-ti))
    lvl=vn[j]
    print(f"{int(ti//60)}:{ti%60:05.2f} {lvl:5.2f} {'*'*int(lvl*40)}")
