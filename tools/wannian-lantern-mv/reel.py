#!/usr/bin/env python3
"""萬年殿花燈夜 → IG Reels 短片（9:16、約 55 秒、卡拍點剪接）。

用法：
  python3 reel.py <照片資料夾> <輸出資料夾> [--audio 自備音樂.mp3]

重點設計
- 只用 reel_plan.json 挑出的畫面，其餘淘汰（原因記在 rejected）
- 照片全幅填滿 9:16，暖色調 + 高光柔光 + 暗角；每段緩推／緩拉，寬幅畫面用橫移
- 每段 4 拍（90 BPM ≈ 2.67 秒），轉場落在拍點上
- 字幕避開 IG 介面遮擋區（上 220px、下 420px）
- 沒給 --audio 時合成輕快五聲音階配樂（暫代，建議換成有授權的曲子）
"""
import argparse, glob, json, os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.environ.get("MV_FONT", "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc")
W, H, S, FPS = 1080, 1920, 2, 30
SAFE_BOTTOM = 430


def font(px):
    return ImageFont.truetype(FONT, px)


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"ffmpeg failed:\n{' '.join(cmd)}\n{r.stderr[-1500:]}")


# ---------- 調光 ----------
def grade(img):
    a = np.asarray(img.convert("RGB"), dtype=np.float32) / 255.0
    a[..., 0] *= 1.04; a[..., 2] *= 0.96                      # 暖色
    a = np.clip((a - 0.5) * 1.08 + 0.51, 0, 1) ** 0.93         # 對比 + 提亮暗部
    lum = (a * [0.299, 0.587, 0.114]).sum(-1, keepdims=True)
    a = np.clip(lum + (a - lum) * 1.12, 0, 1)                  # 飽和
    mask = np.clip((lum - 0.70) / 0.30, 0, 1)
    hl = Image.fromarray((a * mask * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(34))
    hl = np.asarray(hl, dtype=np.float32) / 255.0
    a = 1 - (1 - a) * (1 - 0.40 * hl)                          # 柔光（screen）
    h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    r = ((xx / w - 0.5) ** 2 + (yy / h - 0.5) ** 2) / 0.5
    a *= (1 - 0.32 * np.clip(r, 0, 1) ** 1.2)[..., None]       # 暗角
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))


def load(path):
    im = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    return im.crop((0, 0, im.width, int(im.height * 0.945)))   # 裁掉手機燒錄的機型／日期浮水印


def base_zoom(path, fx, fy):
    return grade(ImageOps.fit(load(path), (W * S, H * S), Image.LANCZOS, centering=(fx, fy)))


def base_pan(path):
    im = load(path)
    w = int(H * S * im.width / im.height)
    return grade(im.resize((w, H * S), Image.LANCZOS))


# ---------- 字幕 ----------
def shadowed(layer, draw_fn):
    sh = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(sh), (0, 0, 0, 200))
    sh = sh.filter(ImageFilter.GaussianBlur(9))
    layer.alpha_composite(sh); layer.alpha_composite(sh)
    draw_fn(ImageDraw.Draw(layer), None)


def lower_third(name, desc):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fn, fd = font(66), font(34)
    x, y = 72, H - SAFE_BOTTOM - 150
    top, bot = y - 190, H - SAFE_BOTTOM + 90                      # 柔和暗色漸層，亮背景上也讀得清
    scrim = Image.new("RGBA", (W, bot - top), (0, 0, 0, 0))
    sd = ImageDraw.Draw(scrim)
    for i in range(bot - top):
        q = i / (bot - top)
        sd.line([(0, i), (W, i)], fill=(0, 0, 0, int(165 * np.sin(np.pi * q) ** 1.2)))
    layer.alpha_composite(scrim, (0, top))

    def draw(d, shadow):
        c1 = shadow or (255, 255, 255, 255)
        c2 = shadow or (255, 238, 205, 255)
        cg = shadow or (240, 190, 90, 255)
        d.rectangle([x, y - 26, x + 64, y - 22], fill=cg)
        d.text((x, y), name, font=fn, fill=c1)
        d.text((x, y + 92), desc, font=fd, fill=c2)
    shadowed(layer, draw)
    return layer


def centered(lines, sub, y0, big=104, small=40):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fb, fs = font(big), font(small)

    def draw(d, shadow):
        c1 = shadow or (255, 244, 220, 255)
        c2 = shadow or (255, 226, 160, 255)
        y = y0
        for ln in lines:
            d.text(((W - d.textlength(ln, font=fb)) / 2, y), ln, font=fb, fill=c1)
            y += int(big * 1.25)
        if sub:
            d.rectangle([W / 2 - 40, y + 6, W / 2 + 40, y + 9], fill=shadow or (240, 190, 90, 255))
            d.text(((W - d.textlength(sub, font=fs)) / 2, y + 36), sub, font=fs, fill=c2)
    shadowed(layer, draw)
    return layer


def title_block(lines, sub, x=72, y=270, big=128, small=40):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    top = Image.new("RGBA", (W, 760), (0, 0, 0, 0))
    td = ImageDraw.Draw(top)
    for i in range(760):
        td.line([(0, i), (W, i)], fill=(0, 0, 0, int(150 * (1 - i / 760) ** 1.4)))
    layer.alpha_composite(top, (0, 0))
    fb, fs = font(big), font(small)

    def draw(d, shadow):
        c1 = shadow or (255, 244, 220, 255)
        c2 = shadow or (255, 226, 160, 255)
        yy = y
        for ln in lines:
            d.text((x, yy), ln, font=fb, fill=c1)
            yy += int(big * 1.2)
        d.rectangle([x, yy + 8, x + 72, yy + 12], fill=shadow or (240, 190, 90, 255))
        d.text((x, yy + 36), sub, font=fs, fill=c2)
    shadowed(layer, draw)
    return layer


# ---------- 片段 ----------
def render_clip(base_png, cap_png, out, dur, hold, mode, opts, fade_in=False, fade_out=False):
    N = int(round(dur * FPS))
    p = f"(on/{N})"
    e = f"({p}*{p}*(3-2*{p}))"
    if mode == "pan":
        a, b = opts["pan"]
        pt = f"(min(t/{dur:.3f},1))"
        et = f"({pt}*{pt}*(3-2*{pt}))"
        vf = (f"crop=w={W*S}:h={H*S}:x='(iw-{W*S})*({a}+({b}-{a})*{et})':y=0,"
              f"scale={W}:{H}:flags=lanczos,format=yuv420p")
    else:
        z = f"1+0.10*{e}" if mode == "in" else f"1.10-0.10*{e}"
        dx = 0.025 if mode == "in" else -0.025
        x = f"max(0,min(iw-iw/zoom,iw*({opts['fx']}+{dx}*{e})-iw/zoom/2))"
        y = f"max(0,min(ih-ih/zoom,ih*{opts['fy']}-ih/zoom/2))"
        vf = f"zoompan=z='{z}':x='{x}':y='{y}':d={N}:s={W}x{H}:fps={FPS},format=yuv420p"
    tail = []
    if fade_in:
        tail.append("fade=t=in:st=0:d=0.5")
    if fade_out:
        tail.append(f"fade=t=out:st={dur-0.9:.2f}:d=0.9")
    post = ("," + ",".join(tail)) if tail else ""
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-loop", "1", "-i", base_png]
    if cap_png:
        cmd += ["-loop", "1", "-i", cap_png]
        fc = (f"[0:v]{vf}[v];"
              f"[1:v]format=rgba,fade=t=in:st=0.35:d=0.5:alpha=1,fade=t=out:st={hold-0.35:.2f}:d=0.4:alpha=1[c];"
              f"[v][c]overlay=x=0:y='22*(1-min(max(t-0.35,0)/0.55,1))'{post}[o]")
    else:
        fc = f"[0:v]{vf}{post}[o]"
    cmd += ["-filter_complex", fc, "-map", "[o]", "-t", f"{dur:.3f}", "-r", str(FPS), "-c:v", "libx264",
            "-preset", "veryfast", "-crf", "19", out]
    run(cmd)


# ---------- 配樂 ----------
def synth_music(path, seconds, bpm, sr=44100):
    rng = np.random.default_rng(11)
    beat = 60 / bpm
    n = int(seconds * sr)
    t = np.arange(n) / sr
    hz = lambda m: 440 * 2 ** ((m - 69) / 12)
    mix = np.zeros(n)
    chords = [(48, [60, 64, 67], [60, 62, 64, 67, 69, 72]),   # C
              (43, [59, 62, 67], [59, 62, 64, 67, 71, 74]),   # G
              (45, [57, 60, 64], [57, 60, 62, 64, 67, 69]),   # Am
              (41, [57, 60, 65], [60, 62, 65, 67, 69, 72])]   # F
    bar = 4 * beat

    def add(start, sig):
        i = int(start * sr)
        j = min(n, i + len(sig))
        if i < n:
            mix[i:j] += sig[: j - i]

    def tone(m, dur, amp, decay, harm=(1, 0.35, 0.12)):
        tt = np.arange(int(dur * sr)) / sr
        s = sum(g * np.sin(2 * np.pi * hz(m) * (k + 1) * tt) for k, g in enumerate(harm))
        return amp * s * np.exp(-tt * decay) * np.minimum(1, tt / 0.004)

    for b in range(int(seconds / bar) + 1):
        root, tri, pen = chords[b % 4]
        s0 = b * bar
        for m in tri:                                           # 鋪底和弦
            tt = np.arange(int(bar * sr)) / sr
            env = np.minimum(1, tt / 0.5) * np.minimum(1, (bar - tt) / 0.7)
            add(s0, 0.035 * env * np.sin(2 * np.pi * hz(m) * tt))
        for k in (0, 2):                                        # 低音
            add(s0 + k * beat, tone(root, beat * 1.8, 0.16, 2.2, (1, 0.2)))
        add(s0, tone(36, 0.5, 0.20, 9, (1,)))                   # 柔和底鼓
        for k in range(8):                                      # 撥弦旋律
            if rng.random() < 0.22:
                continue
            m = int(rng.choice(pen)) + (12 if rng.random() < 0.5 else 0)
            add(s0 + k * beat / 2, tone(m, 1.0, 0.09, 4.0))
        for k in range(8):                                      # 沙鈴
            nz = rng.standard_normal(int(0.05 * sr))
            nz = np.diff(nz, prepend=0)                          # 高通
            env = np.exp(-np.arange(len(nz)) / sr * 70)
            add(s0 + k * beat / 2 + (beat / 2 if False else 0), (0.035 if k % 2 else 0.02) * nz * env)
    tail = np.copy(mix)
    d = int(0.28 * sr)
    for k, g in ((1, 0.30), (2, 0.16), (3, 0.08)):
        tail[k * d:] += g * mix[: n - k * d]
    tail /= max(1e-6, np.abs(tail).max()) / 0.85
    fade = np.minimum(1, t / 0.4) * np.minimum(1, (seconds - t) / 3.0)
    tail *= fade
    hd = int(0.012 * sr)
    left, right = tail, np.concatenate([np.zeros(hd), tail[:-hd]])
    pcm = (np.stack([left, right], 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm.tobytes())


def find(photos, pid):
    m = [f for f in glob.glob(os.path.join(photos, "*")) if pid in os.path.basename(f)]
    if not m:
        sys.exit(f"找不到照片 {pid}")
    return m[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("photos"); ap.add_argument("outdir"); ap.add_argument("--audio")
    a = ap.parse_args()
    plan = json.load(open(os.path.join(HERE, "reel_plan.json"), encoding="utf-8"))
    beat, F = 60 / plan["bpm"], plan["fade"]
    work = os.path.join(a.outdir, "work_reel"); os.makedirs(work, exist_ok=True)

    items = []   # (base, cap, beats, mode, opts, fade_in, fade_out)
    clips = plan["clips"]
    for i, c in enumerate(clips):
        path = find(a.photos, c["id"])
        bp = os.path.join(work, f"b{i:02d}.png")
        (base_pan(path) if c["mode"] == "pan" else base_zoom(path, c["fx"], c["fy"])).save(bp)
        cp = os.path.join(work, f"c{i:02d}.png")
        if c.get("hook"):
            title_block(plan["title"].split("・"), plan["title_sub"]).save(cp)
        else:
            lower_third(c["name"], c["desc"]).save(cp)
        items.append((bp, cp, c["beats"], c["mode"], c, i == 0, False))
    # 片尾：回到開場那匹飛馬，壓暗後放字
    hook = find(a.photos, clips[0]["id"])
    ep = os.path.join(work, "end_base.png")
    dim = base_zoom(hook, clips[0]["fx"], clips[0]["fy"]).point(lambda v: int(v * 0.40))
    dim.save(ep)
    ec = os.path.join(work, "end_cap.png")
    centered([plan["end_title"]], plan["end_sub"], 760).save(ec)
    items.append((ep, ec, plan["end_beats"], "in", {"fx": 0.5, "fy": 0.5}, False, True))

    durs = [it[2] * beat for it in items]
    outs = []
    for i, (bp, cp, beats, mode, opts, fi, fo) in enumerate(items):
        o = os.path.join(work, f"clip{i:02d}.mp4")
        dur = durs[i] + F
        render_clip(bp, cp, o, dur, durs[i], mode, opts, fi, fo)
        outs.append(o)

    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    for o in outs:
        cmd += ["-i", o]
    fc, last, acc = [], "[0:v]", 0.0
    for i in range(1, len(outs)):
        acc += durs[i - 1]
        fc.append(f"{last}[{i}:v]xfade=transition=fade:duration={F}:offset={acc:.3f}[x{i}]")
        last = f"[x{i}]"
    total = sum(durs) + F
    silent = os.path.join(work, "silent.mp4")
    run(cmd + ["-filter_complex", ";".join(fc), "-map", last, "-c:v", "libx264", "-preset", "medium",
               "-crf", "19", "-pix_fmt", "yuv420p", silent])
    audio = a.audio
    if not audio:
        audio = os.path.join(work, "music.wav"); synth_music(audio, total + 0.5, plan["bpm"])
    final = os.path.join(a.outdir, "萬年殿花燈夜_IG_Reels.mp4")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-i", audio, "-map", "0:v", "-map", "1:a",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", f"{total:.2f}",
         "-af", f"afade=t=out:st={total-3:.2f}:d=3", "-movflags", "+faststart", final])
    # IG 封面（標題放在中間 3:4 區域內，個人頁格子裁切也看得到）
    cover = base_zoom(hook, clips[0]["fx"], clips[0]["fy"]).resize((W, H), Image.LANCZOS).convert("RGBA")
    cover.alpha_composite(title_block(plan["title"].split("・"), plan["title_sub"], y=330))
    cover.convert("RGB").save(os.path.join(a.outdir, "萬年殿花燈夜_IG封面.png"))
    print(f"完成：{final}（{total:.1f} 秒）")


if __name__ == "__main__":
    main()
