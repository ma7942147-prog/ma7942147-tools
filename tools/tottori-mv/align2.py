# -*- coding: utf-8 -*-
"""歌詞を「累積歌唱時間」で配る。
壁時計の時間ではなく、実際に声が出ている時間だけを進める。
間奏では歌詞が進まないので、先走りが原理的に起きない。
"""
import numpy as np, json

r = np.load('vad_ratio.npy'); l = np.load('vad_lvl.npy'); t = np.load('vad_t.npy')
fps = 1/(t[1]-t[0])

# ヒステリシス VAD：入るのは厳しく、抜けるのは緩く（語尾で切れないように）
HI_R, HI_L = 0.80, 0.16
LO_R, LO_L = 0.62, 0.07
voiced = np.zeros(len(t), bool); st = False
for i in range(len(t)):
    if st:
        st = (r[i] > LO_R) and (l[i] > LO_L)
    else:
        st = (r[i] > HI_R) and (l[i] > HI_L)
    voiced[i] = st

# 主唱の開始：モデルの確信度が 0.94 以上で安定する最初の点
LEAD_IN = 48.46
voiced[t < LEAD_IN] = False
END = 286.0
voiced[t > END] = False

# 短い穴を埋め、短い島を捨てる
def close(mask, sec):
    k = int(sec*fps); out = mask.copy(); n = len(mask); i = 0
    while i < n:
        if not out[i]:
            j = i
            while j < n and not out[j]: j += 1
            if i > 0 and j < n and (j-i) <= k: out[i:j] = True
            i = j
        else: i += 1
    return out
voiced = close(voiced, 0.45)

runs = []; s = None
for i, v in enumerate(voiced):
    if v and s is None: s = i
    elif not v and s is not None: runs.append((s, i)); s = None
if s is not None: runs.append((s, len(voiced)))
runs = [(a, b) for a, b in runs if t[b-1]-t[a] > 0.30]
onsets = [float(t[a]) for a, b in runs]
total = sum(t[b-1]-t[a] for a, b in runs)
print(f"歌唱句 {len(runs)} 個 / 実歌唱 {total:.1f}s / 範囲 {onsets[0]:.2f}-{t[runs[-1][1]-1]:.2f}s")

# 累積歌唱時間の関数
cum_t, cum_v = [], []
acc = 0.0
for a, b in runs:
    cum_t.append(float(t[a])); cum_v.append(acc)
    acc += float(t[b-1]-t[a])
    cum_t.append(float(t[b-1])); cum_v.append(acc)
def time_at(v):
    return float(np.interp(v, cum_v, cum_t))

LYR = json.load(open('lyrics.json', encoding='utf-8'))
# 文字数で重み付け（長い行ほど長く歌う）
wt = np.array([len(x.replace('　','')) for x in LYR], float)
wt = wt/wt.sum()
edges = np.concatenate([[0], np.cumsum(wt)])*total

out = []
for i in range(len(LYR)):
    tt = time_at(edges[i])
    # 近くに歌い出しがあればそこへ吸着（1.6 秒以内）
    near = min(onsets, key=lambda o: abs(o-tt))
    if abs(near-tt) < 1.6: tt = near
    if out and tt <= out[-1]+1.3: tt = out[-1]+1.3
    out.append(round(tt, 2))
json.dump(out, open('line_times.json','w'), indent=0)
for i,(x,tx) in enumerate(zip(out,LYR)):
    print(f"{i+1:2d} {int(x//60)}:{x%60:05.2f}  {tx}")
d=np.diff(out); print(f"\n間隔 最小{d.min():.2f} 最大{d.max():.2f} 中央{np.median(d):.2f}")
