import subprocess, sys, numpy as np
W,H,FPS=64,36,10          # 10fps 取樣就夠抓爆點
def luma(path):
    p=subprocess.run(["ffmpeg","-v","error","-i",path,"-vf",
                      f"fps={FPS},scale={W}:{H}","-pix_fmt","gray","-f","rawvideo","-"],
                     capture_output=True)
    a=np.frombuffer(p.stdout,dtype=np.uint8)
    n=len(a)//(W*H)
    return a[:n*W*H].reshape(n,W*H).mean(1), n
for f in sys.argv[1:]:
    m,n=luma(f)
    t=np.arange(n)/FPS
    base=np.percentile(m,20)
    score=m-base
    # 找峰值：0.8 秒內最大且超過門檻
    w=int(0.8*FPS)
    thr=np.percentile(score,82)
    peaks=[]
    for i in range(w,len(score)-w):
        if score[i]==score[i-w:i+w+1].max() and score[i]>thr:
            if not peaks or t[i]-peaks[-1][0]>1.5:
                peaks.append((round(float(t[i]),1), round(float(score[i]),1)))
    peaks.sort(key=lambda x:-x[1])
    print(f"\n{f}  長度 {n/FPS:.1f}s  平均亮度 {m.mean():.1f}  最亮 {m.max():.1f}")
    print(f"  最亮的 8 個爆點(秒,強度): {peaks[:8]}")
    # 每 5 秒的平均強度，看整體節奏
    seg=[(s, round(float(score[(t>=s)&(t<s+5)].mean()),1)) for s in range(0,int(t[-1]),5)]
    print("  每5秒強度:", seg)
