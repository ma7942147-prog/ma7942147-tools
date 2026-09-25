#!/usr/bin/env python3
"""
用 ffmpeg 合成一段原創、無版權疑慮的配樂（音樂盒風格的正弦波旋律），
給沒有現成音樂素材、又不想用受版權保護歌曲的情況使用。

用法：
    python3 compose_music.py --duration 37.4 --out music.wav
    python3 compose_music.py --melody my_melody.json --tempo 100 --duration 60 --out music.wav

melody JSON 格式：[["C4", 0.5], ["D4", 0.5], ...]，音名 + 拍數（配合 --tempo 換算秒數）。
不給 --melody 就用內建的預設可愛五聲音階小旋律。
"""

import argparse
import json
import os
import subprocess
import tempfile

SR = 44100
NOTE_BASE = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}

DEFAULT_MELODY = [
    ["C4", 0.5], ["D4", 0.5], ["E4", 0.5], ["G4", 0.5],
    ["A4", 1.0], ["G4", 0.5], ["E4", 0.5],
    ["D4", 0.5], ["C4", 1.0],
    ["E4", 0.5], ["G4", 0.5], ["A4", 0.5], ["C5", 0.5],
    ["D5", 1.0], ["C5", 0.5], ["A4", 0.5],
    ["G4", 0.5], ["E4", 1.0],
    ["D4", 0.5], ["C4", 0.5], ["D4", 0.5], ["E4", 0.5],
    ["D4", 0.5], ["C4", 1.5],
]


def note_freq(note):
    name = note[:-1]
    octave = int(note[-1])
    semitone = NOTE_BASE[name] + (octave - 4) * 12
    return 261.6255653005986 * (2 ** (semitone / 12.0))


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


def build_phrase(melody, tempo, out_path):
    beat = 60.0 / tempo
    inputs = []
    filters = []
    labels = []
    for i, (note, beats) in enumerate(melody):
        dur = beats * beat
        f0 = note_freq(note)
        f1 = f0 * 2
        inputs += ["-f", "lavfi", "-i", f"sine=frequency={f0:.3f}:sample_rate={SR}:duration={dur:.3f}"]
        inputs += ["-f", "lavfi", "-i", f"sine=frequency={f1:.3f}:sample_rate={SR}:duration={dur:.3f}"]
        fade_start = max(dur * 0.35, 0.02)
        fade_dur = max(dur - fade_start - 0.005, 0.02)
        mi, hi = 2 * i, 2 * i + 1
        filters.append(
            f"[{mi}:a]afade=t=in:st=0:d=0.01,afade=t=out:st={fade_start:.3f}:d={fade_dur:.3f},volume=0.9[m{i}]"
        )
        filters.append(
            f"[{hi}:a]afade=t=in:st=0:d=0.01,afade=t=out:st={fade_start:.3f}:d={fade_dur:.3f},volume=0.22[h{i}]"
        )
        filters.append(f"[m{i}][h{i}]amix=inputs=2:duration=first:dropout_transition=0[n{i}]")
        labels.append(f"n{i}")

    concat_in = "".join(f"[{l}]" for l in labels)
    filters.append(f"{concat_in}concat=n={len(labels)}:v=0:a=1[phrase]")
    filter_complex = ";".join(filters)

    cmd = [
        "ffmpeg", "-y", *inputs,
        "-filter_complex", filter_complex,
        "-map", "[phrase]",
        "-ar", str(SR), "-ac", "2",
        out_path,
    ]
    run(cmd)


def loop_to_length(phrase_path, out_path, total_seconds, fade_in, fade_out):
    cmd = [
        "ffmpeg", "-y",
        "-stream_loop", "-1", "-i", phrase_path,
        "-t", f"{total_seconds:.3f}",
        "-af", (
            f"afade=t=in:st=0:d={fade_in},"
            f"afade=t=out:st={max(total_seconds - fade_out, 0):.3f}:d={fade_out},volume=0.85"
        ),
        "-ar", str(SR), "-ac", "2",
        out_path,
    ]
    run(cmd)


def main():
    parser = argparse.ArgumentParser(description="合成一段原創配樂")
    parser.add_argument("--melody", help="旋律 JSON 檔路徑，不給就用內建預設旋律")
    parser.add_argument("--tempo", type=float, default=120.0, help="速度 BPM，預設 120")
    parser.add_argument("--duration", type=float, required=True, help="輸出總長度（秒），通常等於影片長度")
    parser.add_argument("--fade-in", type=float, default=1.5)
    parser.add_argument("--fade-out", type=float, default=2.5)
    parser.add_argument("--out", default="music.wav")
    args = parser.parse_args()

    melody = DEFAULT_MELODY
    if args.melody:
        with open(args.melody, encoding="utf-8") as f:
            melody = json.load(f)

    with tempfile.TemporaryDirectory(prefix="compose_music_") as tmp:
        phrase_path = os.path.join(tmp, "phrase.wav")
        build_phrase(melody, args.tempo, phrase_path)
        loop_to_length(phrase_path, args.out, args.duration, args.fade_in, args.fade_out)
    print(f"完成：{args.out}")


if __name__ == "__main__":
    main()
