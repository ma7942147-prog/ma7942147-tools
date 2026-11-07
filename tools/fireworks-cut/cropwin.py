# -*- coding: utf-8 -*-
"""算出每個鏡頭「放大裁成 16:9」時，視窗該落在畫面的哪個高度。

直式 1080x1920 裁成 16:9 只留得下 31.6% 的高度，固定置中會切掉爆點。

作法：把鏡頭區間內的畫面降成 36x64 灰階取樣，算每一列「沿時間的標準差」，
再用一個 31.6% 高的滑動視窗找出變異度總和最大的位置。

用標準差而不是平均亮度，是因為地面的發射火光、路燈、廟埕燈是持續亮著的，
比平均亮度會贏過空中短暫的爆開，視窗就會被拉到畫面下緣、把主體切掉。
持續亮的東西變異小，爆開的煙火變異大——變異度才對得上「煙火在哪」。

即使如此，畫面最下緣的發射尾焰與翻騰的亮煙變異也很大，還是會把視窗往下拉、
切掉爆開的頂端。所以再把底部 GROUND 比例（廟簷、人群、發射區）排除在外，
只在天空的範圍裡找視窗。

用法： python3 cropwin.py <素材資料夾>
"""
import subprocess
import sys

import numpy as np

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import edl

GW, GH, FPS = 36, 64, 5
RATIO = 9 / 16          # 16:9 視窗在直式畫面裡佔的高度比例
GROUND = 0.18           # 底部這個比例視為地面雜訊，不納入計算


def profile(path, a, b):
    p = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", f"{a:.3f}", "-t", f"{b - a:.3f}",
         "-i", path, "-vf", f"fps={FPS},scale={GW}:{GH}", "-pix_fmt", "gray",
         "-f", "rawvideo", "-"], capture_output=True)
    a_ = np.frombuffer(p.stdout, dtype=np.uint8)
    n = len(a_) // (GW * GH)
    if n == 0:
        return None
    fr = a_[:n * GW * GH].reshape(n, GH, GW).astype(np.float32)
    rows = fr.mean(axis=2)                   # (時間, 列) 每列沿寬度的平均亮度
    return rows.std(axis=0)                  # 每一列沿時間的變異度


def best_window(rows):
    h = max(1, int(round(GH * RATIO)))
    s = np.maximum(rows.copy(), 0)
    s[int(GH * (1 - GROUND)):] = 0           # 排除地面
    best, bi = -1, 0
    for i in range(0, GH - h + 1):
        v = s[i:i + h].sum()
        if v > best:
            best, bi = v, i
    return (bi + h / 2) / GH                 # 視窗中心佔全高的比例


if __name__ == "__main__":
    srcdir = sys.argv[1]
    out = []
    for i, (src, a, b, speed, _) in enumerate(edl.SHOTS):
        rows = profile(f"{srcdir}/{src}.mp4", a, b)
        c = 0.5 if rows is None else best_window(rows)
        c = min(max(c, RATIO / 2), 1 - RATIO / 2)   # 不能超出畫面
        out.append(round(float(c), 3))
        print(f"  鏡頭 {i:02d}  {src}  {a:5.1f}-{b:5.1f}  裁切中心 {c:.3f}"
              f"  ({'偏上' if c < 0.45 else '偏下' if c > 0.55 else '接近置中'})")
    print("\nCROP_Y =", out)
