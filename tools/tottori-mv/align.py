# -*- coding: utf-8 -*-
"""検出した歌声の句 → 41 行の歌詞に割り当てる。
長い句は内部の谷（息継ぎ）で分割し、行数に合わせて候補を選ぶ。
"""
import numpy as np, json
sing = np.load('sing.npy'); t = np.load('tsing.npy'); phr = np.load('phr.npy')
fps = 1/(t[1]-t[0])

def idx(x): return int(np.clip(round(x*fps), 0, len(sing)-1))

cands = []
for a, b in phr:
    dur = b - a
    n = max(1, int(round(dur / 3.1)))          # 1行あたり歌唱 ≒3秒
    if n == 1:
        cands.append(a); continue
    # 内部の谷（息継ぎ）を n-1 個ひろう
    i0, i1 = idx(a), idx(b)
    seg = sing[i0:i1]
    pts = []
    for k in range(1, n):
        c = int(len(seg)*k/n)
        w = int(0.9*fps)
        lo, hi = max(1, c-w), min(len(seg)-1, c+w)
        pts.append(i0 + lo + int(np.argmin(seg[lo:hi])))
    starts = [a] + [float(t[p]) for p in pts]
    cands.extend(starts)
cands = sorted(cands)
# 0:23.7 の一声は 0.67 秒しかなく、その後 11.7 秒の空白 —— 11 文字の歌詞 1 行ではなく
# 句前のひと声。歌詞は歌が続けて出てくる 36.1s から並べる。
VOCAL_IN = 36.0
cands = [c for c in cands if c >= VOCAL_IN]
print(f"候補 {len(cands)} 個  ({cands[0]:.2f}s – {cands[-1]:.2f}s)")

LYR = json.load(open('lyrics.json', encoding='utf-8'))
N = len(LYR)
print(f"歌詞 {N} 行")
sel = [cands[min(len(cands)-1, int(round(i*(len(cands)-1)/(N-1))))] for i in range(N)]
# 単調＆最小間隔 1.2s を保証
out = []
for i, x in enumerate(sel):
    if out and x <= out[-1] + 1.2: x = out[-1] + 1.2
    out.append(round(x, 2))
for i, (x, tx) in enumerate(zip(out, LYR)):
    print(f"{i+1:2d} {int(x//60)}:{x%60:05.2f}  {tx}")
json.dump(out, open('line_times.json','w'), indent=0)
d = np.diff(out)
print(f"\n間隔: 最小 {d.min():.2f}s 最大 {d.max():.2f}s 中央 {np.median(d):.2f}s")
print(f"最終行 {out[-1]:.2f}s / 歌い終わり {phr[-1][1]:.2f}s")
