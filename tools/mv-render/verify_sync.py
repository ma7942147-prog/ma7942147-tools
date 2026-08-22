# -*- coding: utf-8 -*-
"""檢查每一句字幕有沒有跟上人聲：算出「字幕出現」與「該句實際起唱」的落差。

判定方式：用同一組人聲活動偵測（HPSS + 音節速率調變）取得演唱區間，
對每一句字幕，找出它附近最接近的一個「起唱點」（沉默→演唱的轉折），
再比較字幕出現時間與該起唱點。
  offset > 0  = 字幕晚於人聲（使用者最不想要的狀況）
  offset < 0  = 字幕早於人聲
"""
import subprocess
import sys

import numpy as np

import timeline as T

SR, N, H = 22050, 2048, 256
FPS = SR / H


def modulation_envelope(path="assets/song.mp3"):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "2",
                          "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True).stdout
    x = np.frombuffer(raw, dtype=np.float32).reshape(-1, 2).astype(np.float64)
    w = np.hanning(N)

    def mag(s):
        n = (len(s) - N) // H
        fr = np.lib.stride_tricks.sliding_window_view(s, N)[::H][:n] * w
        return np.abs(np.fft.rfft(fr, axis=1))

    S = (mag(x[:, 0]) + mag(x[:, 1])) / 2
    f = np.fft.rfftfreq(N, 1 / SR)

    def med_time(A, k):
        p = k // 2
        Ap = np.pad(A, ((p, p), (0, 0)), mode="edge")
        return np.array([np.median(Ap[i:i + k], axis=0) for i in range(A.shape[0])])

    def med_freq(A, k):
        p = k // 2
        Ap = np.pad(A, ((0, 0), (p, p)), mode="edge")
        return np.median(np.lib.stride_tricks.sliding_window_view(Ap, k, axis=1), axis=2)

    Hh, Pp = med_time(S, 31), med_freq(S, 31)
    Sh = S * (Hh ** 2 / (Hh ** 2 + Pp ** 2 + 1e-12))
    band = (f >= 300) & (f <= 4000)
    E = np.log1p(Sh[:, band].sum(1) * 20)

    spec = np.fft.rfft(E - E.mean())
    mf = np.fft.rfftfreq(len(E), 1 / FPS)
    spec[(mf < 1.8) | (mf > 9)] = 0
    mo = np.fft.irfft(spec, n=len(E))
    k = int(0.30 * FPS)
    env = np.sqrt(np.convolve(mo ** 2, np.ones(k) / k, "same"))
    return env / np.percentile(env, 97), np.arange(len(env)) / FPS


def sung_onsets(m, t, hi=0.34, lo=0.235):
    on, state = np.zeros(len(m), bool), False
    for i, v in enumerate(m):
        if not state and v > hi:
            state = True
        elif state and v < lo:
            state = False
        on[i] = state
    onsets, i = [], 0
    while i < len(on):
        if on[i] and (i == 0 or not on[i - 1]):
            onsets.append(t[i])
        i += 1
    return np.array(onsets)


if __name__ == "__main__":
    m, t = modulation_envelope()
    onsets = sung_onsets(m, t)
    lines = T.build_lines()

    def voiced(a, b):
        """[a,b] 之間有沒有偵測到人聲。"""
        i0, i1 = int(max(a, 0) * FPS), int(min(b, t[-1]) * FPS)
        return bool((m[i0:i1] > 0.28).any())

    print(f"{'字幕出現':>9} {'最近起唱':>9} {'落差':>7}  狀態   歌詞")
    late = miss = 0
    for s, e, text in lines:
        near = onsets[np.argmin(np.abs(onsets - s))]
        off = s - near
        # 連續演唱的段落內部量不到起唱點，這時比對最近起唱點沒有意義
        cmp_ok = abs(off) <= 3.0
        state = "OK  "
        if cmp_ok and off > 0.8:
            state = "偏晚"; late += 1
        elif not voiced(s + 0.15, s + 1.3):
            state = "無聲"; miss += 1
        shown = f"{off:+7.2f}" if cmp_ok else "      -"
        print(f"{s:9.2f} {near:9.2f} {shown}  {state}   {text}")

    print(f"\n字幕晚於起唱點超過 0.8s：{late} / {len(lines)}")
    print(f"字幕出現後 1.3s 內偵測不到人聲：{miss} / {len(lines)}")
