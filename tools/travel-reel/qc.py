# -*- coding: utf-8 -*-
"""照片客觀品質檢查：清晰度（Laplacian 變異）、曝光、對比。"""
import subprocess, sys, glob, os
import numpy as np

W, H = 512, 683          # 降到這個大小算就夠，比例接近 3:4


def gray(path):
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", path,
                        "-vf", f"scale={W}:{H}", "-pix_fmt", "gray",
                        "-frames:v", "1", "-f", "rawvideo", "-"],
                       capture_output=True)
    if len(p.stdout) < W * H:
        return None
    return np.frombuffer(p.stdout[:W * H], dtype=np.uint8).reshape(H, W).astype(np.float32)


def lap_var(g):
    k = (g[:-2, 1:-1] + g[2:, 1:-1] + g[1:-1, :-2] + g[1:-1, 2:] - 4 * g[1:-1, 1:-1])
    return float(k.var())


rows = []
for f in sorted(glob.glob(os.path.join(sys.argv[1], "*.jpg"))):
    g = gray(f)
    if g is None:
        continue
    # 中央 60% 的清晰度最能代表主體是否對到焦
    c = g[int(H*.2):int(H*.8), int(W*.2):int(W*.8)]
    rows.append((os.path.basename(f)[:-4], lap_var(g), lap_var(c),
                 float(g.mean()), float(g.std()),
                 float((g > 250).mean()*100), float((g < 8).mean()*100)))

sharp = np.array([r[2] for r in rows])
med = np.median(sharp)
print(f"{'檔名':>8} {'全幅銳利':>9} {'中央銳利':>9} {'亮度':>6} {'對比':>6} {'過曝%':>6} {'死黑%':>6}  判定")
for n, lv, cv, m, s, hi, lo in rows:
    flag = []
    if cv < med * 0.45: flag.append("失焦")
    if m < 28: flag.append("太暗")
    if hi > 12: flag.append("過曝")
    if s < 32: flag.append("平淡")
    print(f"{n:>8} {lv:9.1f} {cv:9.1f} {m:6.1f} {s:6.1f} {hi:6.1f} {lo:6.1f}  "
          + ("、".join(flag) if flag else "OK"))
print(f"\n中央銳利度中位數 {med:.1f}")
