#!/usr/bin/env python3
"""
照片轉幻燈片影片工具。

用法：
    python3 build_slideshow.py config.json

設定檔格式與範例見同目錄 README.md 與 examples/。
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

DEFAULT_FONT = "Noto Sans CJK TC"
DEFAULT_CANVAS = {"width": 1080, "height": 1350, "fps": 25}
DEFAULT_IMAGE_DURATION = 3.0
DEFAULT_XFADE_DURATION = 0.6


def die(msg):
    print(f"錯誤：{msg}", file=sys.stderr)
    sys.exit(1)


def check_requirements():
    if shutil.which("ffmpeg") is None:
        die(
            "找不到 ffmpeg。請先安裝：\n"
            "  sudo apt-get install -y ffmpeg fonts-noto-cjk"
        )


def resolve(base_dir, path):
    if not path:
        return path
    return path if os.path.isabs(path) else os.path.normpath(os.path.join(base_dir, path))


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


def make_card(out_path, bg_source, card, canvas, font):
    w, h = canvas["width"], canvas["height"]
    dim = card.get("dim", 0.5)
    vf = (
        f"scale={w}:{h}:force_original_aspect_ratio=increase,"
        f"crop={w}:{h},"
        f"boxblur=25:2,"
        f"eq=brightness=-{dim}"
    )
    draws = []
    lines = card["lines"]
    sizes = card.get("sizes", [48] * len(lines))
    colors = card.get("colors", ["white"] * len(lines))
    ys = card.get("y", [f"h*0.4+{i*70}" for i in range(len(lines))])
    for text, size, color, y in zip(lines, sizes, colors, ys):
        safe = text.replace(":", r"\:").replace("'", r"\'")
        draws.append(
            f"drawtext=font='{font}':text='{safe}':fontcolor={color}:fontsize={size}:"
            f"x=(w-text_w)/2:y={y}:borderw=2:bordercolor=black@0.5"
        )
    vf = vf + "," + ",".join(draws) + ",format=yuv420p"
    run(["ffmpeg", "-y", "-i", bg_source, "-vf", vf, "-frames:v", "1", "-update", "1", out_path])


def build(config_path, output_override=None):
    check_requirements()

    config_path = os.path.abspath(config_path)
    base_dir = os.path.dirname(config_path)
    with open(config_path, encoding="utf-8") as f:
        cfg = json.load(f)

    canvas = {**DEFAULT_CANVAS, **cfg.get("canvas", {})}
    w, h, fps = canvas["width"], canvas["height"], canvas["fps"]
    img_dur = cfg.get("image_duration", DEFAULT_IMAGE_DURATION)
    xfade = cfg.get("xfade_duration", DEFAULT_XFADE_DURATION)
    font = cfg.get("font", DEFAULT_FONT)
    caption = cfg.get("caption", "")

    images = [resolve(base_dir, p) for p in cfg.get("images", [])]
    for p in images:
        if not os.path.isfile(p):
            die(f"找不到照片：{p}")
    if not images:
        die("設定檔的 images 是空的，至少要放一張照片")

    output = output_override or cfg.get("output", "output/slideshow.mp4")
    output = resolve(base_dir, output)
    os.makedirs(os.path.dirname(output) or ".", exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="slideshow_") as tmp:
        clips = []
        durs = []

        title_card = cfg.get("title_card")
        if title_card:
            bg = resolve(base_dir, title_card["background"])
            card_path = os.path.join(tmp, "title.jpg")
            make_card(card_path, bg, title_card, canvas, font)
            clips.append(card_path)
            durs.append(title_card.get("duration", 3.2))

        for p in images:
            clips.append(p)
            durs.append(img_dur)

        end_card = cfg.get("end_card")
        if end_card:
            bg = resolve(base_dir, end_card["background"])
            card_path = os.path.join(tmp, "end.jpg")
            make_card(card_path, bg, end_card, canvas, font)
            clips.append(card_path)
            durs.append(end_card.get("duration", 3.6))

        card_paths = {clips[i] for i in range(len(clips)) if clips[i].startswith(tmp)}

        inputs = []
        for c, d in zip(clips, durs):
            inputs += ["-loop", "1", "-t", f"{d + xfade:.2f}", "-i", c]

        filter_parts = []
        labels = []
        for idx, c in enumerate(clips):
            if c in card_paths:
                chain = (
                    f"[{idx}:v]scale={w}:{h}:force_original_aspect_ratio=decrease,"
                    f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=black,"
                    f"setsar=1,fps={fps},format=yuv420p[v{idx}]"
                )
            else:
                cap_filter = ""
                if caption:
                    safe_caption = caption.replace(":", r"\:").replace("'", r"\'")
                    cap_filter = (
                        f",drawtext=font='{font}':text='{safe_caption}':fontcolor=white@0.85:"
                        f"fontsize=26:x=40:y=h-70:box=1:boxcolor=black@0.35:boxborderw=12"
                    )
                chain = (
                    f"[{idx}:v]split=2[bg{idx}][fg{idx}];"
                    f"[bg{idx}]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},"
                    f"boxblur=20:2,eq=brightness=-0.15[bgb{idx}];"
                    f"[fg{idx}]scale={w}:{h}:force_original_aspect_ratio=decrease[fgs{idx}];"
                    f"[bgb{idx}][fgs{idx}]overlay=(W-w)/2:(H-h)/2{cap_filter},"
                    f"setsar=1,fps={fps},format=yuv420p[v{idx}]"
                )
            filter_parts.append(chain)
            labels.append(f"v{idx}")

        if len(labels) == 1:
            filter_complex = ";".join(filter_parts)
            final_label = labels[0]
        else:
            xfade_parts = []
            cum = durs[0]
            prev = labels[0]
            for i in range(1, len(labels)):
                outlab = f"x{i}" if i < len(labels) - 1 else "vout"
                offset = cum - xfade
                xfade_parts.append(
                    f"[{prev}][{labels[i]}]xfade=transition=fade:duration={xfade:.2f}:"
                    f"offset={offset:.2f}[{outlab}]"
                )
                prev = outlab
                cum = cum + durs[i] - xfade
            filter_complex = ";".join(filter_parts + xfade_parts)
            final_label = "vout"

        total = sum(durs) - xfade * (len(durs) - 1) if len(durs) > 1 else durs[0]

        audio = cfg.get("audio")
        cmd = ["ffmpeg", "-y", *inputs]
        if audio:
            audio_file = resolve(base_dir, audio["file"])
            if not os.path.isfile(audio_file):
                die(f"找不到配樂檔案：{audio_file}")
            vol = audio.get("volume", 1.0)
            fade_out = audio.get("fade_out", 2.0)
            audio_idx = len(clips)
            cmd += ["-i", audio_file]
            fade_start = max(total - fade_out, 0)
            audio_filter = (
                f"[{audio_idx}:a]atrim=0:{total:.3f},asetpts=PTS-STARTPTS,"
                f"afade=t=out:st={fade_start:.3f}:d={fade_out:.3f},volume={vol}[aout]"
            )
            filter_complex = filter_complex + ";" + audio_filter
            cmd += [
                "-filter_complex", filter_complex,
                "-map", f"[{final_label}]", "-map", "[aout]",
                "-r", str(fps),
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "medium",
                "-c:a", "aac", "-b:a", "192k",
                "-shortest",
                output,
            ]
        else:
            cmd += [
                "-filter_complex", filter_complex,
                "-map", f"[{final_label}]",
                "-r", str(fps),
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "medium",
                output,
            ]
        run(cmd)

    print(f"完成：{output}（約 {total:.1f} 秒）")


def main():
    parser = argparse.ArgumentParser(description="把一組照片做成幻燈片影片")
    parser.add_argument("config", help="設定檔路徑（JSON）")
    parser.add_argument("-o", "--output", help="輸出檔路徑，覆蓋設定檔裡的 output")
    args = parser.parse_args()
    build(args.config, args.output)


if __name__ == "__main__":
    main()
