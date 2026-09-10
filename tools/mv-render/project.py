# -*- coding: utf-8 -*-
"""選定要處理哪一個專案，並提供共用路徑。

每個專案是 projects/<名稱>/，裡面有：
  timeline.py     段落時間、歌詞時間碼、分鏡
  assets/         song.(mp3|flac) 與圖片、影片
  build/          產出（不進 repo）
  tap_times.json  手動打點結果（可選，存在時優先於偵測值）

用法：所有工具都吃 --project <名稱>，預設讀環境變數 MV_PROJECT，
再預設 one_and_only。
"""
import importlib.util
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))


def _pick():
    for i, a in enumerate(sys.argv):
        if a == "--project" and i + 1 < len(sys.argv):
            return sys.argv[i + 1]
        if a.startswith("--project="):
            return a.split("=", 1)[1]
    return os.environ.get("MV_PROJECT", "one_and_only")


NAME = _pick()
DIR = os.path.join(ROOT, "projects", NAME)
ASSETS = os.path.join(DIR, "assets")
BUILD = os.path.join(DIR, "build")
TAP_FILE = os.path.join(DIR, "tap_times.json")

if not os.path.isdir(DIR):
    raise SystemExit(f"找不到專案 {NAME}（{DIR}）")


def audio():
    """專案的音檔，副檔名不限。"""
    for ext in ("mp3", "flac", "wav", "m4a"):
        p = os.path.join(ASSETS, "song." + ext)
        if os.path.exists(p):
            return p
    raise SystemExit(f"{ASSETS} 裡找不到 song.mp3 / song.flac")


def timeline():
    """載入該專案的 timeline.py。"""
    path = os.path.join(DIR, "timeline.py")
    spec = importlib.util.spec_from_file_location(f"timeline_{NAME}", path)
    mod = importlib.util.module_from_spec(spec)
    mod.TAP_FILE = TAP_FILE
    spec.loader.exec_module(mod)
    mod.TAP_FILE = TAP_FILE
    return mod
