import numpy as np
vs=np.load('vs.npy'); tv=np.load('tv.npy')
# adaptive threshold: local median over 12s
k=int(12/(tv[1]-tv[0]))|1
loc=np.convolve(vs,np.ones(k)/k,mode='same')
r=vs/(loc+1e-9)
on=r>1.12
# fill short gaps
def runs(mask):
    out=[];s=None
    for i,v in enumerate(mask):
        if v and s is None: s=i
        elif not v and s is not None: out.append((s,i)); s=None
    if s is not None: out.append((s,len(mask)))
    return out
R=runs(on)
merged=[]
for s,e in R:
    if merged and tv[s]-tv[merged[-1][1]-1]<0.45: merged[-1]=(merged[-1][0],e)
    else: merged.append((s,e))
ph=[(tv[s],tv[e-1]) for s,e in merged if tv[e-1]-tv[s]>0.7]
print(len(ph),"phrases")
prev=0
for a,b in ph:
    print(f"{int(a//60)}:{a%60:05.2f} -> {int(b//60)}:{b%60:05.2f}  len={b-a:4.1f}  gap_before={a-prev:4.1f}")
    prev=b
