# -*- coding: utf-8 -*-
import numpy as np, soundfile as sf, json
V,sr=sf.read('vrout/song_Vocals.wav'); V=V.mean(1) if V.ndim>1 else V
I,_=sf.read('vrout/song_Instruments.wav'); I=I.mean(1) if I.ndim>1 else I
n=min(len(V),len(I)); V=V[:n].astype(np.float32); I=I[:n].astype(np.float32)
hop,win=512,2048; fr=1+(n-win)//hop; w=np.hanning(win).astype(np.float32)
def sp(x): return np.abs(np.fft.rfft(np.lib.stride_tricks.as_strided(x,(fr,win),(x.strides[0]*hop,x.strides[0]))*w,axis=1))
SV,SI=sp(V),sp(I); f=np.fft.rfftfreq(win,1/sr); t=np.arange(fr)*hop/sr
bd=(f>=200)&(f<=4500)
ev=SV[:,bd].sum(1); ei=SI[:,bd].sum(1)
lvl=ev/np.percentile(ev,99.5); ratio=ev/(ev+ei+1e-9)
def sm(a,k):
    k=int(k)|1; return np.convolve(a,np.hanning(k)/np.hanning(k).sum(),'same')
fps=sr/hop
lvl=sm(lvl,fps*0.10); ratio=sm(ratio,fps*0.12)
np.save('lvl.npy',lvl); np.save('ratio.npy',ratio); np.save('t.npy',t)

def score(x):
    j0=np.searchsorted(t,x); j1=np.searchsorted(t,x+1.0)
    if j1<=j0: return 0,0
    return float(lvl[j0:j1].max()), float(ratio[j0:j1].max())

T=json.load(open('tapped.json')); C=json.load(open('current_times.json'))
ok_t=ok_c=0
print(f"{'#':>3}  你打點  聲量/把握   影片現有  聲量/把握")
for i,(a,b) in enumerate(zip(T,C),1):
    la,ra=score(a); lb,rb=score(b)
    ga = la>0.10 and ra>0.55; gb = lb>0.10 and rb>0.55
    ok_t+=ga; ok_c+=gb
    if i<=3 or 18<=i<=30 or i>=41:
        print(f"{i:3d}  {a:7.2f} {la:5.2f}/{ra:4.2f} {'OK' if ga else '--'}   {b:7.2f} {lb:5.2f}/{rb:4.2f} {'OK' if gb else '--'}")
print(f"\n落在人聲上的比例：你的打點 {ok_t}/45，影片現有 {ok_c}/45")

# 105-135 秒に句がいくつあるか
on=(lvl>0.10)&(ratio>0.55)
runs=[];s=None
for i,v in enumerate(on):
    if v and s is None: s=i
    elif not v and s is not None: runs.append((s,i)); s=None
segs=[(round(float(t[a]),2),round(float(t[b-1]),2)) for a,b in runs if t[b-1]-t[a]>0.30]
mg=[]
for a,b in segs:
    if mg and a-mg[-1][1]<0.45: mg[-1]=(mg[-1][0],b)
    else: mg.append((a,b))
print(f"\n1:45-2:15 のあいだの歌唱句：")
k=0
for a,b in mg:
    if 105<=a<=136:
        k+=1; print(f"  {int(a//60)}:{a%60:05.2f} -> {int(b//60)}:{b%60:05.2f} ({b-a:.1f}s)")
print(f"  合計 {k} 句（この区間に歌詞は 20-28 の 9 行を割り当てている）")
last=mg[-1]
print(f"\n最後の歌唱：{int(last[0]//60)}:{last[0]%60:05.2f} -> {int(last[1]//60)}:{last[1]%60:05.2f}")
