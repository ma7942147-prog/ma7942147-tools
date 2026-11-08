# -*- coding: utf-8 -*-
"""把 reel.py 的剪輯表算成一支 1080x1920 的 IG 短片。

用法： python3 render.py --photos <照片夾> --video <煙火素材夾> --out <輸出夾>
"""
import argparse
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reel as R

SANS = "Noto Sans CJK TC"
SERIF = "Noto Serif CJK TC"
SS = 2                      # 推軌先在 2x 解析度算再縮回，避免 zoompan 抖動
CW, CH = R.OUT_W * SS, R.OUT_H * SS


def esc(t):
    """drawtext 的 text 值：冒號是參數分隔符，不跳脫會被吃掉。"""
    return (t.replace("\\", "\\\\").replace(":", r"\:")
             .replace("'", r"\'").replace("%", r"\%"))


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        sys.stderr.write(" ".join(cmd[:12]) + " ...\n" + p.stderr[-2500:] + "\n")
        raise SystemExit(f"ffmpeg 失敗（{p.returncode}）")


def photo_shot(i, spec, photodir, outdir):
    """一張照片 → 一段帶 Ken Burns 的影片（無聲）。"""
    name, dur, z0, z1, y0, y1 = spec
    dst = os.path.join(outdir, "shots", f"p{i:02d}.mp4")
    if os.path.exists(dst):
        return dst, dur
    nf = max(2, int(round(dur * R.FPS)))
    n = nf - 1
    # 3:4 的直幅照片填進 9:16：以高度為準放大，左右各裁掉一些
    base = (f"scale={CW}:{CH}:force_original_aspect_ratio=increase,"
            f"crop={CW}:{CH},setsar=1")
    z = f"{z0}+({z1 - z0})*on/{n}"
    x = f"(iw-iw/zoom)/2"
    y = f"(ih-ih/zoom)*({y0}+({y1 - y0})*on/{n})"
    kb = (f"zoompan=z='{z}':x='{x}':y='{y}':d=1"
          f":s={R.OUT_W}x{R.OUT_H}:fps={R.FPS}")
    run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-t", f"{dur:.3f}",
         "-i", os.path.join(photodir, name + ".jpg"),
         "-vf", f"{base},fps={R.FPS},{kb},setsar=1",
         "-r", str(R.FPS), "-c:v", "libx264", "-preset", "fast", "-crf", "17",
         "-pix_fmt", "yuv420p", "-an", dst])
    return dst, dur


def fw_shot(i, spec, viddir, outdir):
    """一段煙火（保留現場原音）。"""
    name, a, b = spec
    dur = b - a
    dst = os.path.join(outdir, "shots", f"f{i:02d}.mp4")
    if os.path.exists(dst):
        return dst, dur
    # 煙火素材是 1080x1920 直式（檔案 1920x1080 + rotation -90，解碼時轉正）
    run(["ffmpeg", "-y", "-v", "error", "-ss", f"{a:.3f}", "-t", f"{dur:.3f}",
         "-i", os.path.join(viddir, name + ".mp4"),
         "-vf", (f"scale={R.OUT_W}:{R.OUT_H}:force_original_aspect_ratio=increase,"
                 f"crop={R.OUT_W}:{R.OUT_H},setsar=1,fps={R.FPS},"
                 f"eq=saturation=1.06:contrast=1.03"),
         "-af", "afade=t=in:st=0:d=0.10",
         "-r", str(R.FPS), "-c:v", "libx264", "-preset", "fast", "-crf", "17",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k",
         "-ar", "48000", "-ac", "2", dst])
    return dst, dur


def endcard(outdir):
    dst = os.path.join(outdir, "shots", "end.mp4")
    if os.path.exists(dst):
        return dst, R.ENDCARD
    big, mid, sml = int(R.OUT_H * .044), int(R.OUT_H * .026), int(R.OUT_H * .020)
    def dt(t, font, size, y, alpha="1"):
        return (f"drawtext=font='{font}':text='{esc(t)}':fontcolor=white@{alpha}"
                f":fontsize={size}:x=(w-tw)/2:y={y}")
    layers = ",".join([
        dt("台南 · 灣裡", SERIF, big, "h*0.40"),
        dt("萬年殿花燈", SANS, mid, "h*0.48"),
        dt("文聖堂煙火", SANS, mid, "h*0.525"),
        dt(R.DATE, SANS, sml, "h*0.585", "0.7"),
    ])
    run(["ffmpeg", "-y", "-v", "error",
         "-f", "lavfi", "-i", f"color=c=black:s={R.OUT_W}x{R.OUT_H}:r={R.FPS}:d={R.ENDCARD}",
         "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
         "-vf", layers + f",fade=t=in:st=0:d=0.7,fade=t=out:st={R.ENDCARD-1.1}:d=1.1",
         "-t", str(R.ENDCARD), "-c:v", "libx264", "-preset", "medium", "-crf", "20",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k",
         "-ar", "48000", "-ac", "2", dst])
    return dst, R.ENDCARD


def silence(outdir, dur, idx):
    """照片段沒有聲音，補等長的無聲軌，讓影音兩條鏈長度一致。"""
    dst = os.path.join(outdir, "shots", f"sil{idx:02d}.m4a")
    if not os.path.exists(dst):
        run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
             "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
             "-t", f"{dur:.3f}", "-c:a", "aac", "-b:a", "256k", dst])
    return dst


def add_silent_audio(path, dur, outdir, idx):
    """給無聲的照片段接上空音軌（acrossfade 需要兩邊都有聲音流）。"""
    dst = path.replace(".mp4", "_a.mp4")
    if os.path.exists(dst):
        return dst
    sil = silence(outdir, dur + 0.5, idx)
    run(["ffmpeg", "-y", "-v", "error", "-i", path, "-i", sil,
         "-map", "0:v", "-map", "1:a", "-c:v", "copy",
         "-c:a", "aac", "-b:a", "256k", "-shortest", dst])
    return dst


def _chain1(items, dst):
    """一段 xfade/acrossfade 鏈。每段都不多渲染轉場長度，xfade 直接吃掉
    尾端，影像與聲音兩條鏈的算式才一致（多渲染會讓聲音每段多前進一個
    轉場長度，累積成不同步）。"""
    args = []
    for p, _, _ in items:
        args += ["-i", p]
    parts, v, a, cur = [], "0:v", "0:a", 0.0
    for k in range(1, len(items)):
        d = items[k][2]
        cur += items[k - 1][1] - d
        vo, ao = f"v{k}", f"a{k}"
        parts.append(f"[{v}][{k}:v]xfade=transition=fade:duration={d}"
                     f":offset={cur:.3f}[{vo}]")
        parts.append(f"[{a}][{k}:a]acrossfade=d={d}:c1=tri:c2=tri[{ao}]")
        v, a = vo, ao
    if not parts:
        run(["ffmpeg", "-y", "-v", "error", "-i", items[0][0], "-c", "copy", dst])
        return dst
    run(["ffmpeg", "-y", "-v", "error", *args, "-filter_complex", ";".join(parts),
         "-map", f"[{v}]", "-map", f"[{a}]", "-r", str(R.FPS),
         "-c:v", "libx264", "-preset", "fast", "-crf", "17",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k", dst])
    return dst


def chain(items, outdir, dst, group=6):
    """分批串接。一次把 25 個 1080x1920 的輸入餵進同一個 filter 鏈，
    ffmpeg 會被 OOM killer 幹掉（產出 0 byte、而且不留錯誤訊息）。
    先每 group 段接成一塊，再把各塊接起來；兩層用同一套算式。
    """
    if len(items) <= group:
        return _chain1(items, dst)
    parts = []
    for gi, g0 in enumerate(range(0, len(items), group)):
        chunk = items[g0:g0 + group]
        sub = os.path.join(outdir, f"part{gi:02d}.mp4")
        print(f"    part {gi}: {g0}-{g0 + len(chunk) - 1}", flush=True)
        if not os.path.exists(sub):
            _chain1(chunk, sub)
        # 這一塊的長度 = 各段長度和 - 內部轉場；對外仍用下一塊的轉場長度
        dur = sum(c[1] for c in chunk) - sum(c[2] for c in chunk[1:])
        parts.append((sub, dur, chunk[0][2]))
    # 塊與塊之間的轉場，沿用每塊第一段的設定
    for i in range(1, len(parts)):
        parts[i] = (parts[i][0], parts[i][1], items[i * group][2])
    print("    合併各段 ...", flush=True)
    return _chain1(parts, dst)


def overlays():
    L = []
    big, sub = int(R.OUT_H * .042), int(R.OUT_H * .022)
    t0, t1 = 0.8, 5.6
    fade = (f"if(lt(t,{t0}),0,if(lt(t,{t0+0.8}),(t-{t0})/0.8,"
            f"if(lt(t,{t1-1.0}),1,if(lt(t,{t1}),({t1}-t)/1.0,0))))")
    L.append(f"drawtext=font='{SERIF}':text='{esc(R.TITLE)}':fontcolor=white"
             f":alpha='{fade}':fontsize={big}:shadowcolor=black@0.75:shadowx=3:shadowy=3"
             f":x=(w-tw)/2:y=h*0.11")
    L.append(f"drawtext=font='{SANS}':text='{esc(R.DATE)}':fontcolor=white"
             f":alpha='{fade}':fontsize={sub}:shadowcolor=black@0.75:shadowx=2:shadowy=2"
             f":x=(w-tw)/2:y=h*0.11+{int(big*1.5)}")
    cap = int(R.OUT_H * .024)
    for st, dur, txt, pos in R.CAPS:
        en = st + dur
        af = (f"if(lt(t,{st}),0,if(lt(t,{st+0.45}),(t-{st})/0.45,"
              f"if(lt(t,{en-0.45}),1,if(lt(t,{en}),({en}-t)/0.45,0))))")
        y = "h*0.845" if pos == "bottom" else "h*0.10"
        L.append(f"drawtext=font='{SANS}':text='{esc(txt)}':fontcolor=white"
                 f":alpha='{af}':fontsize={cap}"
                 f":box=1:boxcolor=black@0.30:boxborderw={int(cap*0.55)}"
                 f":x=(w-tw)/2:y={y}")
    return ",".join(L)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--photos", required=True)
    ap.add_argument("--video", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(os.path.join(a.out, "shots"), exist_ok=True)

    items = []
    for i, spec in enumerate(R.FW):
        print(f"  煙火 {spec[0]} {spec[1]}-{spec[2]}", flush=True)
        p, d = fw_shot(i, spec, a.video, a.out)
        items.append((p, d, R.FW_XFADE))
    for i, spec in enumerate(R.P):
        print(f"  照片 {spec[0]}  {spec[1]}s", flush=True)
        p, d = photo_shot(i, spec, a.photos, a.out)
        items.append((add_silent_audio(p, d, a.out, i), d, R.XFADE))
    p, d = endcard(a.out)
    items.append((p, d, R.XFADE))

    print("  串接 ...", flush=True)
    joined = os.path.join(a.out, "joined.mp4")
    if not os.path.exists(joined):
        chain(items, a.out, joined)

    print("  上字幕 ...", flush=True)
    out = os.path.join(a.out, "灣裡的一個晚上.mp4")
    run(["ffmpeg", "-y", "-v", "error", "-i", joined,
         "-vf", overlays() + ",fade=t=in:st=0:d=0.8",
         "-af", "volume=1.0",
         "-c:v", "libx264", "-preset", "slow", "-crf", "19",
         "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.1",
         "-movflags", "+faststart",
         "-c:a", "aac", "-b:a", "256k", "-ar", "48000", out])
    print("完成：", out, flush=True)
