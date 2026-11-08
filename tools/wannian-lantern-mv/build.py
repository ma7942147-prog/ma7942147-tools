#!/usr/bin/env python3
"""萬年殿花燈夜 MV 產生器：照片 + captions.json → 有字幕、運鏡、配樂的 MP4。

用法：
  python3 build.py <照片資料夾> <輸出資料夾> [--layouts landscape,portrait] [--audio 自備音樂.mp3]

- 照片檔名需包含 captions.json 裡的 id（例如 IMG_20261107_211604.jpg 含 211604）
- 不給 --audio 時，用內建程式合成一段五聲音階的輕音樂（僅作暫代，建議之後換成 Suno 歌曲）
- 需要：ffmpeg、Python 3 + Pillow + numpy、中文字型（預設 WenQuanYi Zen Hei）
"""
import argparse, glob, json, math, os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

FONT = os.environ.get("MV_FONT", "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc")
FPS, CLIP, FADE = 30, 4.2, 0.8
TITLE_DUR, END_DUR = 5.0, 5.0
LAYOUTS = {"landscape": (1920, 1080), "portrait": (1080, 1920)}


def font(size):
    return ImageFont.truetype(FONT, size)


def wrap(draw, text, fnt, maxw):
    lines, cur = [], ""
    for ch in text:
        if ch == "\n":
            lines.append(cur); cur = ""; continue
        if draw.textlength(cur + ch, font=fnt) > maxw:
            lines.append(cur); cur = ch
        else:
            cur += ch
    if cur:
        lines.append(cur)
    return lines


def bg_cover(img, W, H):
    bg = ImageOps.fit(img, (W, H), Image.LANCZOS).filter(ImageFilter.GaussianBlur(40))
    return Image.blend(bg, Image.new("RGB", (W, H), (0, 0, 0)), 0.45)


def make_base(path, W, H, S=2):
    img = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    w, h = W * S, H * S
    canvas = bg_cover(img, w, h)
    fg = img.copy()
    fg.thumbnail((int(w * 0.94), int(h * 0.90)), Image.LANCZOS)
    canvas.paste(fg, ((w - fg.width) // 2, (h - fg.height) // 2 - int(h * 0.02)))
    return canvas


def make_caption(name, desc, conf, W, H, idx, total):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bar_h = int(H * (0.20 if W > H else 0.14))
    grad = Image.new("RGBA", (W, bar_h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    for y in range(bar_h):
        gd.line([(0, y), (W, y)], fill=(0, 0, 0, int(200 * (y / bar_h) ** 1.3)))
    layer.alpha_composite(grad, (0, H - bar_h))
    d = ImageDraw.Draw(layer)
    big, small = int(H * (0.060 if W > H else 0.034)), int(H * (0.030 if W > H else 0.018))
    fn, fd = font(big), font(small)
    x, maxw = int(W * 0.05), int(W * 0.90)
    dl = wrap(d, desc + ("（推測）" if conf == "low" else ""), fd, maxw)
    ty = H - int(H * 0.035) - len(dl) * int(small * 1.35) - int(big * 1.25)
    d.text((x, ty), name, font=fn, fill=(255, 226, 150, 255), stroke_width=2, stroke_fill=(0, 0, 0, 255))
    for i, ln in enumerate(dl):
        d.text((x, ty + int(big * 1.25) + i * int(small * 1.35)), ln, font=fd, fill=(255, 255, 255, 255),
               stroke_width=1, stroke_fill=(0, 0, 0, 255))
    tag = f"{idx}/{total}"
    d.text((W - x - d.textlength(tag, font=fd), int(H * 0.03)), tag, font=fd, fill=(255, 255, 255, 200),
           stroke_width=1, stroke_fill=(0, 0, 0, 255))
    return layer


def make_card(lines, sub, W, H, bg_img):
    img = bg_cover(bg_img, W, H).filter(ImageFilter.GaussianBlur(8))
    img = Image.blend(img, Image.new("RGB", (W, H), (10, 5, 0)), 0.35)
    d = ImageDraw.Draw(img)
    big, small = int(min(W, H) * 0.12), int(min(W, H) * 0.045)
    fb, fs = font(big), font(small)
    y = H // 2 - int(big * 0.9 * len(lines) / 1.2)
    for ln in lines:
        w = d.textlength(ln, font=fb)
        d.text(((W - w) / 2, y), ln, font=fb, fill=(255, 226, 150), stroke_width=3, stroke_fill=(0, 0, 0))
        y += int(big * 1.3)
    if sub:
        w = d.textlength(sub, font=fs)
        d.text(((W - w) / 2, y + int(small * 0.8)), sub, font=fs, fill=(255, 255, 255),
               stroke_width=1, stroke_fill=(0, 0, 0))
    return img


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"ffmpeg failed:\n{' '.join(cmd)}\n{r.stderr[-1500:]}")


def clip_from(base_png, cap_png, out, W, H, dur, zoom_in=True):
    frames = int(dur * FPS)
    step = 0.07 / frames
    z = f"min(zoom+{step:.6f},1.07)" if zoom_in else f"if(eq(on,1),1.07,max(zoom-{step:.6f},1.0))"
    fc = (f"[0:v]zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps={FPS},format=yuv420p[v];"
          f"[1:v]format=rgba,fade=t=in:st=0.4:d=0.5:alpha=1,fade=t=out:st={dur-0.7:.2f}:d=0.5:alpha=1[c];"
          f"[v][c]overlay=format=auto,format=yuv420p[o]") if cap_png else \
         (f"[0:v]zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps={FPS},format=yuv420p[o]")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", base_png]
    if cap_png:
        cmd += ["-loop", "1", "-i", cap_png]
    cmd += ["-filter_complex", fc, "-map", "[o]", "-t", f"{dur}", "-r", str(FPS), "-c:v", "libx264",
            "-preset", "veryfast", "-crf", "20", out]
    run(cmd)


def synth_music(path, seconds, sr=44100):
    """五聲音階輕音樂：C–Am–F–G 和弦鋪底 + 撥弦旋律 + 簡單回音。"""
    rng = np.random.default_rng(7)
    bpm = 84; beat = 60 / bpm
    t = np.arange(int(seconds * sr)) / sr
    out = np.zeros_like(t)
    hz = lambda m: 440 * 2 ** ((m - 69) / 12)
    chords = [(48, [60, 64, 67]), (45, [57, 60, 64]), (53, [57, 60, 65]), (55, [59, 62, 67])]
    penta = {0: [60, 62, 64, 67, 69, 72, 74], 1: [57, 60, 62, 64, 67, 69, 72],
             2: [60, 62, 65, 67, 69, 72, 74], 3: [59, 62, 64, 67, 71, 74, 76]}
    bar = 4 * beat
    nbars = int(seconds / bar) + 1
    for b in range(nbars):
        root, tri = chords[b % 4]
        s0 = b * bar
        i0, i1 = int(s0 * sr), min(len(t), int((s0 + bar) * sr))
        tt = t[i0:i1] - s0
        env = np.minimum(1, tt / 0.4) * np.minimum(1, (bar - tt) / 0.6)
        for m in [root] + tri:
            out[i0:i1] += 0.05 * env * (np.sin(2 * np.pi * hz(m) * tt) + 0.3 * np.sin(4 * np.pi * hz(m) * tt))
        for k in range(8):  # 八分音符撥弦旋律
            if rng.random() < 0.18:
                continue
            m = int(rng.choice(penta[b % 4]))
            ns = s0 + k * beat / 2
            j0, j1 = int(ns * sr), min(len(t), int((ns + 1.2) * sr))
            if j1 <= j0:
                continue
            tn = t[j0:j1] - ns
            pluck = np.exp(-tn * 3.2)
            out[j0:j1] += 0.11 * pluck * (np.sin(2 * np.pi * hz(m + 12) * tn) + 0.4 * np.sin(4 * np.pi * hz(m + 12) * tn))
    d = int(0.33 * sr)
    echo = np.copy(out)
    for n, g in ((1, 0.35), (2, 0.18), (3, 0.09)):
        echo[n * d:] += g * out[:-n * d]
    echo *= min(1.0, 0.8 / max(1e-6, np.abs(echo).max()))
    fade = np.minimum(1, t / 2.0) * np.minimum(1, (seconds - t) / 3.0)
    pcm = (echo * fade * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm.tobytes())


def build(photos, outdir, layout, audio):
    W, H = LAYOUTS[layout]
    cfg = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "captions.json"), encoding="utf-8"))
    work = os.path.join(outdir, f"work_{layout}"); os.makedirs(work, exist_ok=True)
    slides = cfg["slides"]
    files = []
    for s in slides:
        m = [f for f in glob.glob(os.path.join(photos, "*")) if s["id"] in os.path.basename(f)]
        if not m:
            sys.exit(f"找不到照片 id={s['id']}")
        files.append(m[0])
    clips = []
    # 片頭
    hero = ImageOps.exif_transpose(Image.open(files[0])).convert("RGB")
    p = os.path.join(work, "title.png")
    make_card([cfg["title"]], cfg["subtitle"], W * 2, H * 2, hero).save(p)
    clips.append((p, None, TITLE_DUR))
    for i, (s, f) in enumerate(zip(slides, files), 1):
        bp = os.path.join(work, f"b{i:02d}.png"); cp = os.path.join(work, f"c{i:02d}.png")
        make_base(f, W, H).save(bp)
        make_caption(s["name"], s["desc"], s["conf"], W, H, i, len(slides)).save(cp)
        clips.append((bp, cp, CLIP))
    hero2 = ImageOps.exif_transpose(Image.open(files[-3])).convert("RGB")
    p = os.path.join(work, "end.png")
    make_card(cfg["ending"].split("\n"), None, W * 2, H * 2, hero2).save(p)
    clips.append((p, None, END_DUR))

    outs = []
    for n, (b, c, dur) in enumerate(clips):
        o = os.path.join(work, f"clip{n:02d}.mp4")
        clip_from(b, c, o, W, H, dur, zoom_in=(n % 2 == 0))
        outs.append((o, dur))

    # xfade 串接
    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    for o, _ in outs:
        cmd += ["-i", o]
    fc, last, acc = [], "[0:v]", outs[0][1]
    for i in range(1, len(outs)):
        off = acc - FADE
        fc.append(f"{last}[{i}:v]xfade=transition=fade:duration={FADE}:offset={off:.3f}[x{i}]")
        last = f"[x{i}]"
        acc = off + outs[i][1]
    total = acc
    silent = os.path.join(work, "silent.mp4")
    run(cmd + ["-filter_complex", ";".join(fc), "-map", last, "-c:v", "libx264", "-preset", "veryfast",
               "-crf", "21", "-pix_fmt", "yuv420p", silent])

    if audio:
        a = audio
    else:
        a = os.path.join(work, "music.wav"); synth_music(a, total + 1)
    final = os.path.join(outdir, f"萬年殿花燈夜_MV_{layout}.mp4")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-i", a, "-map", "0:v", "-map", "1:a",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-af", f"afade=t=out:st={total-3:.2f}:d=3",
         "-t", f"{total:.2f}", "-movflags", "+faststart", final])
    print(f"完成：{final}（{total:.1f} 秒）")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("photos"); ap.add_argument("outdir")
    ap.add_argument("--layouts", default="landscape,portrait")
    ap.add_argument("--audio")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    for lay in a.layouts.split(","):
        build(a.photos, a.outdir, lay, a.audio)
