import wave, numpy as np
w=wave.open('song.wav'); sr=w.getframerate(); n=w.getnframes()
x=np.frombuffer(w.readframes(n),dtype=np.int16).astype(np.float32)/32768
hop=512; win=2048
frames=1+(len(x)-win)//hop
St=np.lib.stride_tricks.as_strided(x,(frames,win),(x.strides[0]*hop,x.strides[0]))*np.hanning(win)
S=np.abs(np.fft.rfft(St,axis=1))
freqs=np.fft.rfftfreq(win,1/sr)
t=np.arange(frames)*hop/sr
# log-mel-ish bands
edges=np.geomspace(60,10000,41)
idx=[np.where((freqs>=edges[i])&(freqs<edges[i+1]))[0] for i in range(40)]
M=np.array([S[:,ix].mean(1) if len(ix) else np.zeros(frames) for ix in idx]).T
L=np.log1p(M*100)
# normalize frames
Ln=(L-L.mean(0))/(L.std(0)+1e-9)
# downsample to 1 fps for SSM
fps=int(round(sr/hop))
K=frames//fps
D=np.array([Ln[i*fps:(i+1)*fps].mean(0) for i in range(K)])
Dn=D/ (np.linalg.norm(D,axis=1,keepdims=True)+1e-9)
SSM=Dn@Dn.T
# checkerboard novelty
def kernel(N):
    g=np.outer(np.hanning(2*N),np.hanning(2*N))
    c=np.ones((2*N,2*N)); c[:N,N:]=-1; c[N:,:N]=-1
    return g*c
N=8; k=kernel(N); nov=np.zeros(K)
for i in range(N,K-N):
    nov[i]=(SSM[i-N:i+N,i-N:i+N]*k).sum()
nov=(nov-nov.min())/(nov.max()-nov.min()+1e-9)
peaks=[i for i in range(2,K-2) if nov[i]==max(nov[max(0,i-6):i+7]) and nov[i]>0.35]
print("boundaries(s):",peaks)
# mid-band (vocal) energy envelope, 
vb=(freqs>=250)&(freqs<=4000)
voc=S[:,vb].mean(1)
np.save('voc.npy',voc); np.save('t2.npy',t)
# onset envelope + tempo
flux=np.maximum(0,np.diff(np.log1p(M*100),axis=0)).sum(1); flux=np.concatenate([[0],flux])
f=flux-np.convolve(flux,np.ones(43)/43,mode='same'); f=np.maximum(f,0)
ac=np.correlate(f,f,'full')[len(f)-1:]
lags=np.arange(len(ac))*hop/sr
mask=(lags>0.3)&(lags<1.2)
best=lags[mask][np.argmax(ac[mask])]
print(f"beat period ~{best:.3f}s -> {60/best:.1f} BPM")
np.save('flux2.npy',f)
