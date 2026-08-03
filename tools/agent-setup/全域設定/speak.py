#!/usr/bin/env python3
"""用 Edge-TTS 合成中文語音並行內播放。

依《AI Agent 全域設定規範》：統一用 Edge-TTS，不用 SAPI，不開外部播放器視窗。

用法：
    python speak.py "要唸的內容"
    python speak.py "要唸的內容" --voice zh-TW-HsiaoChenNeural
    python speak.py --list-voices
    echo "從 stdin 來的文字" | python speak.py

沒裝 edge-tts 的話：
    uv pip install --python .\\.venv\\Scripts\\python.exe edge-tts
"""

import argparse
import asyncio
import os
import subprocess
import sys
import tempfile

DEFAULT_VOICE = "zh-TW-YunJheNeural"  # 男聲、穩重、適合教學

# 規範裡列的台灣中文聲音
VOICES = {
    "zh-TW-YunJheNeural": "男／穩重、適合教學（預設）",
    "zh-TW-HsiaoChenNeural": "女／活潑、清晰",
    "zh-TW-HsiaoYuNeural": "女／溫柔、柔和",
}


def die(msg, code=1):
    print(msg, file=sys.stderr)
    sys.exit(code)


try:
    import edge_tts
except ImportError:
    die(
        "找不到 edge_tts 套件。請先安裝：\n"
        "    uv pip install --python .\\.venv\\Scripts\\python.exe edge-tts",
        2,
    )


async def synthesize(text, voice, output):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output)


def play(path):
    """行內播放，不開外部播放器視窗。"""
    if sys.platform == "win32":
        # 用 .NET MediaPlayer 播放，播完才返回。-NoProfile 避免吃到使用者 profile 拖慢啟動。
        ps = (
            "Add-Type -AssemblyName PresentationCore;"
            "$p = New-Object System.Windows.Media.MediaPlayer;"
            f"$p.Open([Uri]::new('{path}'));"
            # Open 是非同步的，要等它把長度讀出來才知道要睡多久
            "while (-not $p.NaturalDuration.HasTimeSpan) { Start-Sleep -Milliseconds 50 };"
            "$dur = $p.NaturalDuration.TimeSpan.TotalSeconds;"
            "$p.Play();"
            "Start-Sleep -Seconds ([math]::Ceiling($dur) + 1);"
            "$p.Close()"
        )
        cmd = ["powershell.exe", "-NoProfile", "-Command", ps]
    elif sys.platform == "darwin":
        cmd = ["afplay", path]
    else:
        for player in ("ffplay", "mpv", "aplay"):
            if subprocess.run(["which", player], capture_output=True).returncode == 0:
                cmd = (
                    [player, "-nodisp", "-autoexit", "-loglevel", "quiet", path]
                    if player == "ffplay"
                    else [player, path]
                )
                break
        else:
            print(f"找不到可用的播放器，語音檔留在：{path}", file=sys.stderr)
            return False

    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        print(
            f"播放失敗（{result.returncode}）：{result.stderr.decode(errors='replace')[:300]}",
            file=sys.stderr,
        )
        return False
    return True


async def list_voices():
    voices = await edge_tts.list_voices()
    for v in sorted(voices, key=lambda x: x["ShortName"]):
        if v["Locale"].startswith("zh-"):
            print(f"{v['ShortName']:<32} {v['Gender']:<8} {v['Locale']}")


def main():
    parser = argparse.ArgumentParser(description="Edge-TTS 語音回覆")
    parser.add_argument("text", nargs="*", help="要唸的內容（省略則從 stdin 讀）")
    parser.add_argument("--voice", default=DEFAULT_VOICE, help=f"聲音代碼（預設 {DEFAULT_VOICE}）")
    parser.add_argument("--output", help="存成指定檔案，不播放")
    parser.add_argument("--list-voices", action="store_true", help="列出所有中文聲音")
    args = parser.parse_args()

    if args.list_voices:
        asyncio.run(list_voices())
        return

    text = " ".join(args.text).strip() or sys.stdin.read().strip()
    if not text:
        die("沒有可唸的內容。")

    if args.voice not in VOICES and args.voice.startswith("zh-TW-"):
        print(f"注意：{args.voice} 不在規範列出的聲音裡，仍會嘗試合成。", file=sys.stderr)

    if args.output:
        asyncio.run(synthesize(text, args.voice, args.output))
        print(f"語音已儲存：{args.output}")
        return

    # 播完就刪，不在硬碟留一堆 temp_speech.mp3
    fd, path = tempfile.mkstemp(suffix=".mp3", prefix="speak_")
    os.close(fd)
    try:
        asyncio.run(synthesize(text, args.voice, path))
        if play(path):
            print("語音已播放")
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


if __name__ == "__main__":
    main()
