# -*- coding: utf-8 -*-
"""MV 合成：Ken Burns + 交叉溶接 + 對拍歌詞字幕 + 音訊亮度脈動 -> mp4"""
import json, os, subprocess, sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import imageio_ffmpeg

CFG = json.load(open('timings.json', encoding='utf-8'))
FPS = CFG['fps']; OW, OH = CFG['size']
DUR = CFG['duration']
FONT = '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'
SRC = os.environ.get('SCENES', 'frames')
OUT = sys.argv[1] if len(sys.argv) > 1 else 'tottori_mv.mp4'
PREVIEW = os.environ.get('PREVIEW')  # "start,end" seconds
# 歌詞全体を後ろへずらす秒数。歌い出しより前に字が出るときはここを増やす。
OFFSET = float(os.environ.get('OFFSET', CFG.get('lyric_offset', 0.0)))

# ---- audio envelope for light pulsing ----
if os.path.exists('t.npy') and os.path.exists('db.npy'):
    t_env = np.load('t.npy'); db = np.load('db.npy')
    env = np.clip((db - np.percentile(db, 5)) / (np.percentile(db, 98) - np.percentile(db, 5) + 1e-9), 0, 1)
    def energy(t): return float(np.interp(t, t_env, env))
else:   # analyze.py を先に走らせると音圧に合わせて画面が脈打つ
    def energy(t): return 0.5

# ---- scenes ----
scenes = []
for i, (st, key, jp, en) in enumerate(CFG['scenes']):
    end = CFG['scenes'][i + 1][0] if i + 1 < len(CFG['scenes']) else DUR
    scenes.append(dict(start=st, end=end, key=key, jp=jp, en=en))
imgs = {}
for s in scenes:
    p = os.path.join(SRC, s['key'] + '.jpg')
    imgs[s['key']] = Image.open(p).convert('RGB')
SW, SH = imgs[scenes[0]['key']].size

XFADE = 1.3  # 秒

def ken_burns(im, i, p):
    """p: 0..1 progress within scene. 交替 zoom in / out + 平移。"""
    z0, z1 = (1.00, 0.86) if i % 2 == 0 else (0.86, 1.00)
    e = p * p * (3 - 2 * p)                      # smoothstep
    z = z0 + (z1 - z0) * e
    dirs = [(0.5, 0.45), (0.42, 0.5), (0.58, 0.52), (0.5, 0.58)][i % 4]
    tx, ty = dirs
    cx = 0.5 + (tx - 0.5) * e * 2
    cy = 0.5 + (ty - 0.5) * e * 2
    cw, ch = SW * z, SH * z
    x0 = min(max(cx * SW - cw / 2, 0), SW - cw)
    y0 = min(max(cy * SH - ch / 2, 0), SH - ch)
    return im.resize((OW, OH), Image.BICUBIC, box=(x0, y0, x0 + cw, y0 + ch))

# ---- text layers (cached) ----
f_lyric = ImageFont.truetype(FONT, 58)
f_place_jp = ImageFont.truetype(FONT, 34)
f_place_en = ImageFont.truetype(FONT, 22)
f_title = ImageFont.truetype(FONT, 96)
f_sub = ImageFont.truetype(FONT, 30)

def text_layer(items):
    """文字を描き、bbox に切り詰めた (y0, y1, alpha, glow, shadow) を返す。
    全画面ではなく帯だけ合成するので数倍速い。"""
    base = Image.new('L', (OW, OH), 0)
    d = ImageDraw.Draw(base)
    for txt, font, y, x in items:
        if not txt: continue
        x_ = (OW - d.textlength(txt, font=font)) / 2 if x is None else x
        d.text((x_, y), txt, font=font, fill=255)
    bb = base.getbbox()
    if bb is None: return None
    y0 = max(0, bb[1] - 60); y1 = min(OH, bb[3] + 60)
    a = np.asarray(base).astype(np.float32)[y0:y1] / 255
    glow = np.asarray(base.filter(ImageFilter.GaussianBlur(14))).astype(np.float32)[y0:y1] / 255
    shadow = np.asarray(base.filter(ImageFilter.GaussianBlur(4))).astype(np.float32)[y0:y1] / 255
    return y0, y1, a, glow, shadow

lines = CFG['lines']
lyr_cache = {}
def lyric_layer(idx):
    if idx not in lyr_cache:
        txt = lines[idx][1]
        lyr_cache[idx] = text_layer([(txt, f_lyric, OH * 0.795, None)])
    return lyr_cache[idx]

place_cache = {}
def place_layer(i):
    if i not in place_cache:
        s = scenes[i]
        place_cache[i] = text_layer([(s['jp'], f_place_jp, 72, 96),
                                     (s['en'], f_place_en, 120, 98)])
    return place_cache[i]

title_layer = text_layer([(CFG['title'], f_title, OH * 0.40, None),
                          (CFG['subtitle'], f_sub, OH * 0.40 + 130, None)])

GLOW_TINT = np.float32([1.0, 0.93, 0.80])
INK = np.float32([1.0, 0.985, 0.955])

def blend_text(frame, layers, alpha, warm=1.0):
    if layers is None or alpha <= 0.002: return frame
    y0, y1, a, glow, shadow = layers
    f = frame[y0:y1]
    f *= (1 - (shadow * np.float32(0.55 * alpha))[..., None])          # 影で下地を締める
    g = np.clip((glow * np.float32(alpha * 0.55 * warm))[..., None] * GLOW_TINT, 0, 1)
    f = 1 - (1 - f) * (1 - g)                                          # 柔らかい光暈
    am = (a * np.float32(alpha))[..., None]
    frame[y0:y1] = f * (1 - am) + am * INK
    return frame

def fade(t, t0, t1, fin=0.45, fout=0.45):
    if t < t0 - fin or t > t1 + fout: return 0.0
    if t < t0: return (t - (t0 - fin)) / fin
    if t > t1: return max(0.0, 1 - (t - t1) / fout)
    return 1.0

# ---- encode ----
ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
t_start, t_end = (0.0, DUR)
if PREVIEW:
    t_start, t_end = [float(v) for v in PREVIEW.split(',')]
nframes = int((t_end - t_start) * FPS)

cmd = [ffmpeg, '-y', '-loglevel', 'error',
       '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{OW}x{OH}', '-r', str(FPS), '-i', '-',
       '-ss', str(t_start), '-i', CFG['audio'],
       '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p',
       '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', OUT]
proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

cur_scene = -1
for n in range(nframes):
    t = t_start + n / FPS
    # 找目前場景
    si = 0
    for i, s in enumerate(scenes):
        if t >= s['start']: si = i
    s = scenes[si]
    p = np.clip((t - s['start']) / max(0.1, s['end'] - s['start']), 0, 1)
    fr = np.asarray(ken_burns(imgs[s['key']], si, p)).astype(np.float32) / np.float32(255)
    # 交叉溶接
    if si + 1 < len(scenes) and t > s['end'] - XFADE:
        w = (t - (s['end'] - XFADE)) / XFADE
        s2 = scenes[si + 1]
        p2 = (t - s2['start']) / max(0.1, s2['end'] - s2['start'])
        fr2 = np.asarray(ken_burns(imgs[s2['key']], si + 1, np.clip(p2, 0, 1))).astype(np.float32) / np.float32(255)
        w = w * w * (3 - 2 * w)
        fr = fr * (1 - w) + fr2 * w
    # 音壓脈動（重拍時整體微亮）
    e = energy(t)
    fr = np.clip(fr * np.float32(0.94 + 0.13 * e), 0, 1)
    # 片頭淡入 / 片尾淡出
    if t < 1.6: fr *= np.float32(t / 1.6)
    if t > DUR - 4.0: fr *= np.float32(max(0.0, (DUR - t) / 4.0))
    # 地名字幕
    a_place = fade(t, s['start'] + 0.6, s['start'] + 4.4, 0.5, 0.9)
    if a_place > 0: fr = blend_text(fr, place_layer(si), a_place * 0.85)
    # 標題
    if t < 9.5:
        fr = blend_text(fr, title_layer, fade(t, 2.2, 7.6, 1.4, 1.6) * 0.95, warm=1.2)
    # 歌詞
    for i, (lt, txt) in enumerate(lines):
        if not txt: continue
        nt = lines[i + 1][0] if i + 1 < len(lines) else DUR
        # 句と句の間隔が短いときは淡入／淡出も詰める（重ならないように）
        span = nt - lt
        fin = min(0.42, span * 0.22); fout = min(0.50, span * 0.26)
        # 字は「歌い出しより前」には絶対に出さない：淡入は lt から始めて lt+fin で全開
        show = lt + OFFSET
        end = min(show + span - max(0.10, fout * 0.75), show + 7.5)
        if show <= t <= end + fout:
            a = fade(t, show + fin, end, fin, fout)
            fr = blend_text(fr, lyric_layer(i), a * (0.90 + 0.10 * e))
    proc.stdin.write((np.clip(fr, 0, 1) * 255).astype(np.uint8).tobytes())
    if n % 240 == 0:
        print(f"  {t:6.1f}s / {t_end:.0f}s", flush=True)
proc.stdin.close(); proc.wait()
print("done ->", OUT)
