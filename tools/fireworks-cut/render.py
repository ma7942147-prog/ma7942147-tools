# -*- coding: utf-8 -*-
"""把煙火素材依 edl.py 剪成一支成品。

用法：
  python3 render.py --src <素材資料夾> --out <輸出資料夾> [--portrait|--landscape|--both]

直式（1080x1920）是素材的原生比例，滿版不裁切；
橫式（1920x1080）給 YouTube 主站用，兩側以自己的放大模糊版填滿。
"""
import argparse
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import edl

FONT_SANS = "Noto Sans CJK TC"
FONT_SERIF = "Noto Serif CJK TC"


def esc(text):
    """drawtext 的 text 值要跳脫：冒號是參數分隔符，不跳脫會被當成選項邊界
    （「攝於 20:30-20:35」會只剩下 "35"）。反斜線和單引號也要處理。"""
    return (text.replace("\\", "\\\\")
                .replace(":", r"\:")
                .replace("'", r"\'")
                .replace("%", r"\%"))


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        sys.stderr.write(" ".join(cmd[:14]) + " ...\n" + p.stderr[-2500:] + "\n")
        raise SystemExit(f"ffmpeg 失敗（{p.returncode}）")


def shot_path(outdir, i, tag):
    # 直式與橫式的中間檔要分開，否則同名會互相覆蓋
    return os.path.join(outdir, "shots", f"{tag}_s{i:02d}.mp4")


def render_shot(i, shot, srcdir, outdir, W, H, tag):
    src, a, b, speed, _ = shot
    dur = (b - a) / speed
    if i < len(edl.SHOTS) - 1:
        dur += edl.XFADE
    src_dur = dur * speed
    path = shot_path(outdir, i, tag)
    if os.path.exists(path):
        return path

    # 直式素材進橫式畫面：模糊放大版填兩側，原片等比置中
    if W > H:
        fit = (f"split=2[bg][fg];"
               f"[bg]scale={W}:{H}:force_original_aspect_ratio=increase,"
               f"crop={W}:{H},boxblur=luma_radius=40:luma_power=2,"
               f"eq=brightness=-0.12:saturation=0.6[bgo];"
               f"[fg]scale={W}:{H}:force_original_aspect_ratio=decrease[fgo];"
               f"[bgo][fgo]overlay=(W-w)/2:(H-h)/2")
    else:
        fit = (f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}")

    vf = [fit, f"fps={edl.FPS}", "setsar=1"]
    af = []
    if speed != 1.0:
        vf.insert(0, f"setpts={1/speed:.6f}*PTS")
        # atempo 下限 0.5，0.25 要串兩層；音高不變，聽起來像慢下來的轟鳴
        r = speed
        while r < 0.5:
            af.append("atempo=0.5")
            r *= 2
        if abs(r - 1.0) > 1e-6:
            af.append(f"atempo={r:.6f}")
    af.append(f"afade=t=in:st=0:d=0.08")

    run(["ffmpeg", "-y", "-v", "error",
         "-ss", f"{a:.3f}", "-t", f"{src_dur:.3f}", "-i", os.path.join(srcdir, src + ".mp4"),
         "-vf", ",".join(vf), "-af", ",".join(af),
         "-r", str(edl.FPS), "-c:v", "libx264", "-preset", "fast", "-crf", "17",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
         "-ac", "2", path])
    return path


def build_endcard(outdir, W, H, tag):
    """片尾字卡：黑底，廟宇／日期／地點。"""
    path = os.path.join(outdir, "shots", f"{tag}_end.mp4")
    if os.path.exists(path):
        return path
    e = edl.EVENT
    big = int(H * 0.055)
    mid = int(H * 0.030)
    sml = int(H * 0.022)
    def dt(text, font, size, y, color="white", alpha="1"):
        return (f"drawtext=font='{font}':text='{esc(text)}':fontcolor={color}@{alpha}"
                f":fontsize={size}:x=(w-tw)/2:y={y}")
    layers = ",".join([
        dt(f"{e['temple']}　煙火", FONT_SERIF, big, f"h*0.36"),
        dt(f"{e['date']}（{e['weekday']}）", FONT_SANS, mid, f"h*0.47"),
        dt(e["place_full"], FONT_SANS, mid, "h*0.53"),
        dt(f"攝於 {e['shot_from']}–{e['shot_to']}", FONT_SANS, sml, "h*0.60",
           "white", "0.65"),
    ])
    run(["ffmpeg", "-y", "-v", "error",
         "-f", "lavfi", "-i", f"color=c=black:s={W}x{H}:r={edl.FPS}:d={edl.ENDCARD}",
         "-f", "lavfi", "-i", f"anullsrc=channel_layout=stereo:sample_rate=48000",
         "-vf", layers + f",fade=t=in:st=0:d=0.8,fade=t=out:st={edl.ENDCARD-1.2}:d=1.2",
         "-t", str(edl.ENDCARD), "-c:v", "libx264", "-preset", "medium", "-crf", "20",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
         "-ac", "2", path])
    return path


def xfade_chain(inputs, offsets, dst, W, H):
    args = []
    for p in inputs:
        args += ["-i", p]
    v, a = "0:v", "0:a"
    parts = []
    for k in range(1, len(inputs)):
        vo, ao = f"v{k}", f"a{k}"
        parts.append(f"[{v}][{k}:v]xfade=transition=fade:"
                     f"duration={edl.XFADE}:offset={offsets[k]:.3f}[{vo}]")
        parts.append(f"[{a}][{k}:a]acrossfade=d={edl.XFADE}:c1=tri:c2=tri[{ao}]")
        v, a = vo, ao
    run(["ffmpeg", "-y", "-v", "error", *args,
         "-filter_complex", ";".join(parts), "-map", f"[{v}]", "-map", f"[{a}]",
         "-r", str(edl.FPS), "-c:v", "libx264", "-preset", "fast", "-crf", "17",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k", dst])
    return dst


def overlays(W, H, total):
    """片頭字卡 + 各段時刻標，回傳 drawtext 濾鏡字串。"""
    e = edl.EVENT
    L = []
    t0, t1 = edl.TITLE_IN, edl.TITLE_OUT
    fade = (f"if(lt(t,{t0}),0,"
            f"if(lt(t,{t0+1.0}),(t-{t0})/1.0,"
            f"if(lt(t,{t1-1.2}),1,"
            f"if(lt(t,{t1}),({t1}-t)/1.2,0))))")
    big = int(H * 0.052)
    sub = int(H * 0.026)
    L.append(f"drawtext=font='{FONT_SERIF}':text='{esc(e['temple'] + chr(0x3000) + '煙火')}'"
             f":fontcolor=white:alpha='{fade}':fontsize={big}"
             f":shadowcolor=black@0.7:shadowx=3:shadowy=3"
             f":x=(w-tw)/2:y=h*0.13")
    for n, txt in enumerate([e["place_short"], f"{e['date']}（{e['weekday']}）"]):
        L.append(f"drawtext=font='{FONT_SANS}':text='{esc(txt)}'"
                 f":fontcolor=white:alpha='{fade}':fontsize={sub}"
                 f":shadowcolor=black@0.7:shadowx=2:shadowy=2"
                 f":x=(w-tw)/2:y=h*0.13+{int(big * 1.5 + n * sub * 1.45)}")

    # 時刻標：每當換到新的拍攝時間就在左下角帶出 3 秒
    chip = int(H * 0.019)
    cur = 0.0
    for i, (src, a, b, speed, stamp) in enumerate(edl.SHOTS):
        seg = (b - a) / speed
        if stamp:
            s, en = cur + 0.35, cur + 3.35
            af = (f"if(lt(t,{s}),0,if(lt(t,{s+0.5}),(t-{s})/0.5,"
                  f"if(lt(t,{en-0.5}),1,if(lt(t,{en}),({en}-t)/0.5,0))))")
            L.append(f"drawtext=font='{FONT_SANS}':text='{esc(stamp)}'"
                     f":fontcolor=white:alpha='{af}':fontsize={chip}"
                     f":box=1:boxcolor=black@0.35:boxborderw={int(chip*0.5)}"
                     f":x=w*0.055:y=h-h*0.075")
        cur += seg - (edl.XFADE if i < len(edl.SHOTS) - 1 else 0)
    return ",".join(L)


def build(srcdir, outdir, W, H, tag, relabel=False):
    """relabel=True：沿用既有的串接檔，只重做字卡（改字幕時用，省掉整輪重剪）。"""
    os.makedirs(os.path.join(outdir, "shots"), exist_ok=True)
    joined_exists = os.path.exists(os.path.join(outdir, f"joined_{tag}.mp4"))
    paths, offs, cur = [], [], 0.0
    for i, sh in enumerate(edl.SHOTS):
        if not (relabel and joined_exists):
            print(f"  鏡頭 {i:02d}  {sh[0]}  {sh[1]:.1f}-{sh[2]:.1f}s  x{sh[3]}", flush=True)
            paths.append(render_shot(i, sh, srcdir, outdir, W, H, tag))
        offs.append(cur)
        cur += (sh[2] - sh[1]) / sh[3] - edl.XFADE
    body_len = cur + edl.XFADE
    if not (relabel and joined_exists):
        paths.append(build_endcard(outdir, W, H, tag))
    offs.append(body_len - edl.XFADE)

    joined = os.path.join(outdir, f"joined_{tag}.mp4")
    if os.path.exists(joined):
        print("  串接檔已存在，沿用", flush=True)
    else:
        print("  串接 ...", flush=True)
        xfade_chain(paths, offs, joined, W, H)

    print("  上字卡 ...", flush=True)
    total = body_len + edl.ENDCARD - edl.XFADE
    out = os.path.join(outdir, f"文聖堂煙火_{tag}.mp4")
    run(["ffmpeg", "-y", "-v", "error", "-i", joined,
         "-vf", overlays(W, H, total) + ",fade=t=in:st=0:d=1.0",
         "-c:v", "libx264", "-preset", "slow", "-crf", "19",
         "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.2",
         "-movflags", "+faststart",
         "-c:a", "aac", "-b:a", "256k", "-ar", "48000", out])
    # joined 留著：只改字卡時可以直接重跑上字卡那一步，不用重剪
    for p in paths:
        if os.path.exists(p):
            os.remove(p)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--portrait", action="store_true")
    ap.add_argument("--landscape", action="store_true")
    ap.add_argument("--relabel", action="store_true",
                    help="沿用既有串接檔，只重做字卡")
    args = ap.parse_args()
    todo = []
    if args.portrait or not args.landscape:
        todo.append((1080, 1920, "直式1080x1920"))
    if args.landscape:
        todo.append((1920, 1080, "橫式1920x1080"))
    for W, H, tag in todo:
        print(f"== {tag} ==", flush=True)
        print("完成：", build(args.src, args.out, W, H, tag, args.relabel), flush=True)
