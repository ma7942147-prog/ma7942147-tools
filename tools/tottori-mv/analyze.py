import wave, numpy as np
w=wave.open('song.wav'); sr=w.getframerate(); n=w.getnframes()
x=np.frombuffer(w.readframes(n),dtype=np.int16).astype(np.float32)/32768
dur=len(x)/sr; print(f"sr={sr} dur={dur:.2f}s")
hop=512; win=1024
frames=1+(len(x)-win)//hop
S=np.abs(np.fft.rfft(np.lib.stride_tricks.as_strided(x,(frames,win),(x.strides[0]*hop,x.strides[0]))*np.hanning(win),axis=1))
t=np.arange(frames)*hop/sr
rms=np.sqrt((S**2).mean(1))
# spectral flux
flux=np.maximum(0,np.diff(S,axis=0)).sum(1); flux=np.concatenate([[0],flux])
# smoothed rms in dB
def smooth(a,k):
    return np.convolve(a,np.ones(k)/k,mode='same')
db=20*np.log10(smooth(rms,43)+1e-9)
np.save('t.npy',t); np.save('db.npy',db); np.save('flux.npy',flux); np.save('rms.npy',rms)
# print energy profile every 2s
for i in range(0,int(dur),2):
    j=np.argmin(np.abs(t-i)); print(f"{i//60}:{i%60:02d} {db[j]:6.1f} {'#'*max(0,int(db[j]+60))}")
