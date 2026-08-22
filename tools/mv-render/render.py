# -*- coding: utf-8 -*-
"""把 assets/ 的圖片與影片、音檔、歌詞合成一支 1080p MV。

流程：
  1. 每個分鏡各自渲染成一段無聲 mp4（Ken Burns 推軌 + 模糊填邊）
  2. 用 xfade 串接所有分鏡（轉場起點對齊分鏡邊界）
  3. 燒上 ASS 字幕、混入原始音檔，輸出最終 mp4

用法： python3 render.py [--shots-only] [--fast]
"""
import os
import subprocess
import sys

import timeline as T

ROOT = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(ROOT, "assets")
BUILD = os.path.join(ROOT, "build")
SHOTDIR = os.path.join(BUILD, "shots")
AUDIO = os.path.join(ASSETS, "song.mp3")
OUT = os.path.join(BUILD, "MV_The_One_and_Only.mp4")

SS = 2  # supersample 倍率：先在 2x 解析度做推軌再縮回 1080p，畫面較穩
CW, CH = T.W * SS, T.H * SS
CRF = "16"


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        sys.stderr.write(" ".join(cmd[:12]) + " ...\n" + p.stderr[-3000:] + "\n")
        raise SystemExit(f"ffmpeg failed ({p.returncode})")


def canvas_filter(crop):
    """裁切 → 2x 畫布（模糊背景填滿 + 原圖等比置中）。"""
    pre = ""
    if crop and crop != (0.0, 0.0, 1.0, 1.0):
        x, y, w, h = crop
        pre = f"crop=iw*{w}:ih*{h}:iw*{x}:ih*{y},"
    return (
        f"[0:v]{pre}split=2[a][b];"
        f"[a]scale={CW}:{CH}:force_original_aspect_ratio=increase,"
        f"crop={CW}:{CH},boxblur=luma_radius=48:luma_power=2,"
        f"eq=brightness=-0.09:saturation=0.75[bg];"
        f"[b]scale={CW}:{CH}:force_original_aspect_ratio=decrease[fg];"
        f"[bg][fg]overlay=(W-w)/2:(H-h)/2[cv]"
    )


def kenburns(z0, z1, px0, py0, px1, py1, nframes):
    n = max(nframes - 1, 1)
    z = f"{z0}+({z1 - z0})*on/{n}"
    x = f"(iw-iw/zoom)*({px0}+({px1 - px0})*on/{n})"
    y = f"(ih-ih/zoom)*({py0}+({py1 - py0})*on/{n})"
    return (f"zoompan=z='{z}':x='{x}':y='{y}':d=1:s={T.W}x{T.H}:fps={T.FPS}")


def render_shot(i, shot):
    start, end, src, crop, a, b, px0, py0, px1, py1 = shot
    dur = end - start
    if i < len(T.SHOTS) - 1:
        dur += T.XFADE                      # 多渲染一段供轉場吃掉
    path = os.path.join(SHOTDIR, f"shot{i:02d}.mp4")
    if os.path.exists(path):
        return path
    common = ["-r", str(T.FPS), "-c:v", "libx264", "-preset", "medium",
              "-crf", CRF, "-pix_fmt", "yuv420p", "-an", "-threads", "2", path]

    if src.endswith(".mp4"):
        trim = crop[0]
        vf = (f"scale={T.W}:{T.H}:force_original_aspect_ratio=increase,"
              f"crop={T.W}:{T.H},setsar=1,fps={T.FPS},"
              f"eq=saturation=1.05:contrast=1.03")
        run(["ffmpeg", "-y", "-v", "error", "-ss", f"{trim:.3f}", "-t", f"{dur:.3f}",
             "-i", os.path.join(ASSETS, src), "-vf", vf, *common])
    else:
        nf = int(round(dur * T.FPS))
        vf = canvas_filter(crop) + ";[cv]fps=%d,%s,setsar=1[v]" % (
            T.FPS, kenburns(a, b, px0, py0, px1, py1, nf))
        run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-t", f"{dur:.3f}",
             "-i", os.path.join(ASSETS, src),
             "-filter_complex", vf, "-map", "[v]", *common])
    return path


def concat_shots(paths):
    master = os.path.join(BUILD, "master.mp4")
    inputs = []
    for p in paths:
        inputs += ["-i", p]
    parts = []
    cur = "0:v"
    for k in range(1, len(paths)):
        off = T.SHOTS[k][0]                 # 轉場起點 = 分鏡邊界（絕對時間）
        lab = f"x{k}"
        parts.append(f"[{cur}][{k}:v]xfade=transition=fade:"
                     f"duration={T.XFADE}:offset={off:.3f}[{lab}]")
        cur = lab
    fg = ";".join(parts)
    run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", fg,
         "-map", f"[{cur}]", "-r", str(T.FPS), "-c:v", "libx264",
         "-preset", "medium", "-crf", CRF, "-pix_fmt", "yuv420p", "-an", master])
    return master


def finish(master):
    ass = os.path.join(BUILD, "lyrics.ass").replace(":", r"\:")
    vf = (f"subtitles='{ass}':fontsdir=/usr/share/fonts,"
          f"fade=t=in:st=0:d=1.5,fade=t=out:st=271.4:d=1.24")
    run(["ffmpeg", "-y", "-v", "error", "-i", master, "-i", AUDIO,
         "-vf", vf, "-map", "0:v", "-map", "1:a",
         "-c:v", "libx264", "-preset", "slow", "-crf", "18",
         "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.1",
         "-movflags", "+faststart",
         "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
         "-shortest", OUT])
    return OUT


if __name__ == "__main__":
    os.makedirs(SHOTDIR, exist_ok=True)
    import make_subs
    make_subs.main(os.path.join(BUILD, "lyrics.ass"))
    from concurrent.futures import ThreadPoolExecutor
    def job(t):
        i, s = t
        print(f"  shot {i:02d}  {s[0]:7.2f}-{s[1]:7.2f}  {s[2]}", flush=True)
        return render_shot(i, s)
    with ThreadPoolExecutor(max_workers=3) as ex:
        paths = list(ex.map(job, list(enumerate(T.SHOTS))))
    if "--shots-only" in sys.argv:
        raise SystemExit(0)
    print("  concat + xfade ...", flush=True)
    m = concat_shots(paths)
    print("  subtitles + audio ...", flush=True)
    print("DONE:", finish(m))
