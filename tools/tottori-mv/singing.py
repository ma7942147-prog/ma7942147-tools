# -*- coding: utf-8 -*-
"""歌声区間の検出（打楽器を除去 → 中央定位 → 諧波 → 音節レートの変調）。
出力: sing.npy（0..1 の歌声らしさ）, tsing.npy
"""
import wave, numpy as np

w = wave.open('stereo.wav'); sr = w.getframerate()
d = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
d = d.reshape(-1, 2); L, R = d[:, 0], d[:, 1]

hop, win = 256, 2048
H = np.hanning(win).astype(np.float32)
def spec(x):
    fr = 1 + (len(x) - win) // hop
    st = np.lib.stride_tricks.as_strided(x, (fr, win), (x.strides[0]*hop, x.strides[0])) * H
    return np.fft.rfft(st, axis=1)
SL, SR = spec(L), spec(R)
f = np.fft.rfftfreq(win, 1/sr)
t = np.arange(SL.shape[0]) * hop / sr

# 1) 中央定位のみ残す：mid から side 分を引く（両端に振られた音を落とす）
mid = np.abs((SL + SR) / 2); side = np.abs((SL - SR) / 2)
C = np.maximum(0, mid - 1.15 * side)

# 2) HPSS：時間方向メディアン=諧波、周波数方向メディアン=打楽器
def medfilt(A, k, axis):
    pad = [(0,0),(0,0)]; pad[axis] = (k//2, k//2)
    P = np.pad(A, pad, mode='edge')
    sl = [slice(None)]*2
    out = np.empty((k,)+A.shape, dtype=A.dtype)
    for i in range(k):
        sl[axis] = slice(i, i+A.shape[axis])
        out[i] = P[tuple(sl)]
    return np.median(out, axis=0)
Harm = medfilt(C, 17, 0)     # 時間方向 → 持続音（声・パッド）
Perc = medfilt(C, 17, 1)     # 周波数方向 → 打撃音
Hmask = Harm**2 / (Harm**2 + Perc**2 + 1e-9)
V = C * Hmask

# 3) 声の帯域
band = (f >= 250) & (f <= 3800)
env = V[:, band].sum(1)
fps = sr / hop

# 4) 音節レート（3–8 Hz）の変調が強いところが歌
e = env / (np.percentile(env, 99) + 1e-9)
def bandpass(x, lo, hi, fs):
    X = np.fft.rfft(x); fr = np.fft.rfftfreq(len(x), 1/fs)
    X[(fr < lo) | (fr > hi)] = 0
    return np.fft.irfft(X, n=len(x))
mod = np.abs(bandpass(e - e.mean(), 3.0, 8.0, fps))
def sm(x, k):
    k = int(k) | 1
    return np.convolve(x, np.hanning(k)/np.hanning(k).sum(), 'same')
mod_s = sm(mod, fps*0.35)
env_s = sm(e, fps*0.20)
sing = env_s * (0.35 + mod_s / (np.percentile(mod_s, 92) + 1e-9))
sing = sing / (np.percentile(sing, 97) + 1e-9)
np.save('sing.npy', sing.astype(np.float32)); np.save('tsing.npy', t.astype(np.float32))
print(f"frames={len(sing)} fps={fps:.1f} dur={t[-1]:.1f}s")

# 歌区間：しきい値を超えて 0.45 秒以上続くところ
th = 0.30
on = sing > th
runs = []; s0 = None
for i, v in enumerate(on):
    if v and s0 is None: s0 = i
    elif not v and s0 is not None: runs.append((s0, i)); s0 = None
if s0 is not None: runs.append((s0, len(on)))
merged = []
for a, b in runs:
    if merged and t[a] - t[merged[-1][1]-1] < 0.40: merged[-1] = (merged[-1][0], b)
    else: merged.append((a, b))
seg = [(float(t[a]), float(t[b-1])) for a, b in merged if t[b-1]-t[a] > 0.45]
np.save('sing_seg.npy', np.array(seg))
print(f"{len(seg)} singing segments")
prev = 0.0
for a, b in seg:
    print(f"{int(a//60)}:{a%60:05.2f} -> {int(b//60)}:{b%60:05.2f}  len={b-a:4.1f}  gap={a-prev:5.1f}")
    prev = b
