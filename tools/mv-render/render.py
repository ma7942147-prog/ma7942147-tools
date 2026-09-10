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

import project

T = project.timeline()
ASSETS = project.ASSETS
BUILD = project.BUILD
SHOTDIR = os.path.join(BUILD, "shots")
AUDIO = project.audio()
OUT = os.path.join(BUILD, f"MV_{project.NAME}.mp4")

SS = 2  # supersample 倍率：先在 2x 解析度做推軌再縮回 1080p，畫面較穩
CW, CH = T.W * SS, T.H * SS
CRF = "16"


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        sys.stderr.write(" ".join(cmd[:12]) + " ...\n" + p.stderr[-3000:] + "\n")
        raise SystemExit(f"ffmpeg failed ({p.returncode})")


def canvas_filter(crop, w=None, h=None, out="cv"):
    """裁切 → 畫布（模糊背景填滿 + 原片等比置中）。

    直式素材放進橫式畫面時，兩側用自己的放大模糊版填滿，
    比裁掉上下或留黑邊都好看。
    """
    w = w or CW
    h = h or CH
    pre = ""
    if crop and crop != (0.0, 0.0, 1.0, 1.0):
        x, y, cw, ch = crop
        pre = f"crop=iw*{cw}:ih*{ch}:iw*{x}:ih*{y},"
    blur = max(8, int(48 * w / CW))
    return (
        f"[0:v]{pre}split=2[a][b];"
        f"[a]scale={w}:{h}:force_original_aspect_ratio=increase,"
        f"crop={w}:{h},boxblur=luma_radius={blur}:luma_power=2,"
        f"eq=brightness=-0.09:saturation=0.75[bg];"
        f"[b]scale={w}:{h}:force_original_aspect_ratio=decrease[fg];"
        f"[bg][fg]overlay=(W-w)/2:(H-h)/2[{out}]"
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
    common = ["-r", str(T.FPS), "-c:v", "libx264", "-preset", "fast",
              "-crf", CRF, "-pix_fmt", "yuv420p", "-an", "-threads", "2", path]

    if src.endswith(".mp4"):
        trim = crop[0]
        fill = crop[1] if len(crop) > 1 else "blur"
        if fill == "crop":            # 素材比例接近畫面，直接放大裁切
            vf = (f"scale={T.W}:{T.H}:force_original_aspect_ratio=increase,"
                  f"crop={T.W}:{T.H},setsar=1,fps={T.FPS},"
                  f"eq=saturation=1.05:contrast=1.03")
            run(["ffmpeg", "-y", "-v", "error", "-ss", f"{trim:.3f}", "-t", f"{dur:.3f}",
                 "-i", os.path.join(ASSETS, src), "-vf", vf, *common])
        else:                          # 直式素材：模糊背景填滿 + 原片置中
            fc = (canvas_filter(None, T.W, T.H, "cv") +
                  f";[cv]fps={T.FPS},setsar=1,eq=saturation=1.05:contrast=1.03[v]")
            run(["ffmpeg", "-y", "-v", "error", "-ss", f"{trim:.3f}", "-t", f"{dur:.3f}",
                 "-i", os.path.join(ASSETS, src),
                 "-filter_complex", fc, "-map", "[v]", *common])
    else:
        nf = int(round(dur * T.FPS))
        vf = canvas_filter(crop) + ";[cv]fps=%d,%s,setsar=1[v]" % (
            T.FPS, kenburns(a, b, px0, py0, px1, py1, nf))
        run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-t", f"{dur:.3f}",
             "-i", os.path.join(ASSETS, src),
             "-filter_complex", vf, "-map", "[v]", *common])
    return path


def _xfade_chain(inputs, offsets, dst):
    """把一串片段用 xfade 接起來；offsets 是相對於第一段開頭的絕對時間。"""
    args = []
    for p in inputs:
        args += ["-i", p]
    parts, cur = [], "0:v"
    for k in range(1, len(inputs)):
        lab = f"x{k}"
        parts.append(f"[{cur}][{k}:v]xfade=transition=fade:"
                     f"duration={T.XFADE}:offset={offsets[k]:.3f}[{lab}]")
        cur = lab
    if parts:
        run(["ffmpeg", "-y", "-v", "error", *args, "-filter_complex", ";".join(parts),
             "-map", f"[{cur}]", "-r", str(T.FPS), "-c:v", "libx264",
             "-preset", "fast", "-crf", CRF, "-pix_fmt", "yuv420p", "-an", dst])
    else:
        run(["ffmpeg", "-y", "-v", "error", "-i", inputs[0], "-c", "copy", dst])
    return dst


def concat_shots(paths, group=10):
    """分批串接。一次餵 49 個輸入給 ffmpeg 太重，先每 group 個接成一段，
    再把各段接起來。轉場起點都是絕對時間，所以兩層用同一套算法。"""
    starts = [s[0] for s in T.SHOTS]
    parts, part_starts = [], []
    for g0 in range(0, len(paths), group):
        chunk = paths[g0:g0 + group]
        base = starts[g0]
        offs = [starts[g0 + i] - base for i in range(len(chunk))]
        dst = os.path.join(BUILD, f"part{g0 // group:02d}.mp4")
        print(f"    part {g0 // group}: shots {g0}-{g0 + len(chunk) - 1}", flush=True)
        parts.append(_xfade_chain(chunk, offs, dst))
        part_starts.append(base)
    master = os.path.join(BUILD, "master.mp4")
    if len(parts) == 1:
        os.replace(parts[0], master)
        return master
    print("    joining parts ...", flush=True)
    offs = [t - part_starts[0] for t in part_starts]
    return _xfade_chain(parts, offs, master)


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
