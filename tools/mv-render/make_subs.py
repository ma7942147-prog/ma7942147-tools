# -*- coding: utf-8 -*-
"""產生 ASS 字幕檔（含主歌詞、片頭字卡、片尾字卡）。"""
import project

T = project.timeline()


def ts(sec):
    if sec < 0:
        sec = 0
    h = int(sec // 3600); sec -= h * 3600
    m = int(sec // 60);   sec -= m * 60
    s = int(sec)
    cs = int(round((sec - s) * 100))
    if cs == 100:
        cs = 0; s += 1
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


HEADER = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {T.W}
PlayResY: {T.H}
WrapStyle: 2
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Lyric,Noto Sans CJK TC,62,&H00FFFFFF,&H00FFFFFF,&HC0201028,&HB4000000,-1,0,0,0,100,100,2,0,1,3,2,2,120,120,86,1
Style: Title,Noto Serif CJK TC,86,&H00FFFFFF,&H00FFFFFF,&HC0201028,&HB4000000,-1,0,0,0,100,100,6,0,1,3,3,5,120,120,0,1
Style: Sub,Noto Sans CJK TC,40,&H00E8DCFF,&H00E8DCFF,&HC0201028,&HB4000000,0,0,0,0,100,100,8,0,1,2,2,5,120,120,0,1
Style: Outro,Noto Serif CJK TC,58,&H00FFFFFF,&H00FFFFFF,&HC0201028,&HB4000000,0,0,0,0,100,100,4,0,1,3,2,5,120,120,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

FADE = r"{\fad(150,220)}"


def main(path=None):
    path = path or __import__("os").path.join(project.BUILD, "lyrics.ass")
    ev = []

    # 片頭字卡
    ts0, te0, tlines = T.TITLE_CARD
    ev.append((ts0, te0, "Title", r"{\fad(900,900)\pos(960,470)}" + tlines[0]))
    ev.append((ts0 + 0.7, te0, "Sub", r"{\fad(900,900)\pos(960,585)}" + tlines[1]))

    # 主歌詞
    for s, e, text in T.build_lines():
        ev.append((s, e, "Lyric", FADE + text))

    # 片尾字卡（沒有就跳過）
    card = getattr(T, "OUTRO_CARD", None)
    if card:
        os_, oe, olines = card
        ev.append((os_, oe, "Outro",
                   r"{\fad(700,1200)\pos(960,540)}" + r"\N".join(olines)))

    ev.sort(key=lambda x: x[0])
    with open(path, "w", encoding="utf-8") as f:
        f.write(HEADER)
        for s, e, style, text in ev:
            f.write(f"Dialogue: 0,{ts(s)},{ts(e)},{style},,0,0,0,,{text}\n")
    print(f"wrote {path}  ({len(ev)} events)")


if __name__ == "__main__":
    import os
    os.makedirs(project.BUILD, exist_ok=True)
    main()
