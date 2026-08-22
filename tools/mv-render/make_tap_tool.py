# -*- coding: utf-8 -*-
"""產生「歌詞打點工具」：一個自帶音檔的單一 HTML，用空白鍵手動對時。

打完之後把匯出的 tap_times.json 放回 tools/mv-render/，
timeline.py 會自動改用手動打的時間（人耳勝過偵測器），
再跑 render.py 就會重出 MV。

用法： python3 make_tap_tool.py [輸出路徑]
"""
import base64
import json
import os
import sys

import timeline as T

ROOT = os.path.dirname(os.path.abspath(__file__))
AUDIO = os.path.join(ROOT, "assets", "song.mp3")
TEMPLATE = os.path.join(ROOT, "tap_ui.html")


DL_BUTTON = '<button id="dl">下載 tap_times.json</button>'
DL_SCRIPT = """document.getElementById('dl').onclick = () => {
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([out.value], {type:'application/json'}));
  a.download = 'tap_times.json'; a.click();
};"""


def build(dst=os.path.join(ROOT, "build", "tap.html"), embed=True, download=True):
    """embed=True 會把 mp3 以 base64 內嵌，產出的單一 HTML 到哪都能開。

    download=False 用於發佈成 Artifact：那個檢視器不給網頁下載檔案，
    留著下載鈕只會按了沒反應，改成只留「複製全部」。
    """
    secs = T.section_onsets()
    start_at = sum(len(l) for _, _, _, l in secs[:6])   # Bridge 第一句
    data = {
        "id": "one_and_only",
        "rev": 2,
        "startAt": start_at,
        "outro": list(T.OUTRO_CARD[:2]),
        "sections": [
            {"name": name, "onsets": [round(o, 2) for o in onsets],
             "end": round(end, 2), "lines": lines}
            for name, onsets, end, lines in secs
        ],
    }
    html = open(TEMPLATE, encoding="utf-8").read()
    if embed:
        b64 = base64.b64encode(open(AUDIO, "rb").read()).decode()
        src = "data:audio/mpeg;base64," + b64
    else:
        src = os.path.basename(AUDIO)
    html = html.replace("__DATA__", json.dumps(data, ensure_ascii=False))
    html = html.replace("__AUDIO_SRC__", src)
    html = html.replace("__DL__", DL_BUTTON if download else "")
    html = html.replace("__DLJS__", DL_SCRIPT if download else "")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, "w", encoding="utf-8") as f:
        f.write(html)
    mb = os.path.getsize(dst) / 1e6
    print(f"wrote {dst}  ({mb:.1f} MB, {sum(len(s['lines']) for s in data['sections'])} 句)")
    return dst


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    build(args[0] if args else os.path.join(ROOT, "build", "tap.html"),
          download="--no-download" not in sys.argv)
