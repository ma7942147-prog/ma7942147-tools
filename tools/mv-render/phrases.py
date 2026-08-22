# -*- coding: utf-8 -*-
"""從 demucs 分離出的人聲軌抓出每一句的實際起唱／收尾時間。"""
import subprocess
import sys

import numpy as np

SR = 22050
HOP = 256
VOC = "build/stems/htdemucs/song/vocals.wav"


def load(path=VOC):
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR),
         "-f", "f32le", "-"], capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32)


def envelope(x):
    n = len(x) // HOP
    fr = x[:n * HOP].reshape(n, HOP)
    rms = np.sqrt((fr.astype(np.float64) ** 2).mean(1))
    # 3 frame (~35ms) 平滑，去掉單點雜訊
    k = np.ones(3) / 3
    return np.convolve(rms, k, "same"), np.arange(n) * HOP / SR


def segments(rms, t, thr_ratio=0.055, merge_gap=0.42, min_len=0.35):
    thr = np.percentile(rms, 99.5) * thr_ratio
    on = rms > thr
    segs = []
    i = 0
    while i < len(on):
        if on[i]:
            j = i
            while j < len(on) and on[j]:
                j += 1
            segs.append([t[i], t[min(j, len(t) - 1)]])
            i = j
        else:
            i += 1
    # 合併間隔很短的片段（同一句裡的換氣）
    out = []
    for s in segs:
        if out and s[0] - out[-1][1] < merge_gap:
            out[-1][1] = s[1]
        else:
            out.append(s)
    return [s for s in out if s[1] - s[0] >= min_len]


if __name__ == "__main__":
    rms, t = envelope(load())
    segs = segments(rms, t)
    print(f"# {len(segs)} phrases")
    prev = 0.0
    for k, (a, b) in enumerate(segs):
        print(f"{k:3d}  {a:7.2f} → {b:7.2f}  len={b-a:5.2f}  gap_before={a-prev:5.2f}")
        prev = b
