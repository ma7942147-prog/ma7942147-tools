#!/usr/bin/env python3
r"""極簡可愛動物桌布產生器。

用 Pillow 純程式畫出來，不從網路抓圖——沒有版權問題，解析度想要多大就多大。

用法：
    .\.venv\Scripts\python.exe tools\wallpaper\make_wallpaper.py
    .\.venv\Scripts\python.exe tools\wallpaper\make_wallpaper.py --size 3840x2160
    .\.venv\Scripts\python.exe tools\wallpaper\make_wallpaper.py --animal cat --theme 奶茶
    .\.venv\Scripts\python.exe tools\wallpaper\make_wallpaper.py --contact-sheet

圖會輸出到 tools/wallpaper/out/。
"""

import argparse
import os
import sys

from PIL import Image, ImageDraw

SS = 4        # 超取樣倍率：先畫 4 倍大再縮小，邊緣才不會有鋸齒
U = 1000      # 動物圖層的邏輯座標系（0..1000 的正方形）

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")


# --------------------------------------------------------------- 配色
# 每組：背景上、背景下（做極淡漸層）、主色、深色、腮紅
THEMES = {
    "奶茶":   dict(bg=("#F3E7DA", "#EADBCA"), main="#C89B7B", dark="#5E4636", blush="#E8A9A0"),
    "霧藍":   dict(bg=("#E3EBF1", "#D2DEE8"), main="#8FAFC4", dark="#3E5566", blush="#E3A9A2"),
    "抹茶":   dict(bg=("#E8EEDD", "#D9E3C9"), main="#9DB183", dark="#4A5740", blush="#DFA79E"),
    "櫻花":   dict(bg=("#F7E6E6", "#F0D5D6"), main="#DDA0A6", dark="#6B4750", blush="#D98C93"),
    "薰衣草": dict(bg=("#EAE5F0", "#DCD4E6"), main="#A99AC0", dark="#4C4159", blush="#DDA0AC"),
    "夜": dict(bg=("#2B3040", "#1E2230"), main="#8B93AD", dark="#F0EDE6", blush="#C98A85"),
}
DEFAULT_THEME = "奶茶"


def hx(c):
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def s(v):
    """邏輯座標 → 超取樣後的實際像素"""
    return int(round(v * SS))


def box(cx, cy, rx, ry=None):
    """以中心點 + 半徑描述橢圓，比 Pillow 的左上右下好讀"""
    ry = rx if ry is None else ry
    return [s(cx - rx), s(cy - ry), s(cx + rx), s(cy + ry)]


def poly(pts):
    return [(s(x), s(y)) for x, y in pts]


def smile(d, cx, cy, w, h, color, width=14):
    """往下彎的弧線——當閉眼或嘴巴用"""
    d.arc(box(cx, cy, w, h), start=200, end=340, fill=color, width=s(width))


def blush(d, cx, cy, color, r=52):
    d.ellipse(box(cx, cy, r, r * 0.68), fill=color + (110,))


# --------------------------------------------------------------- 動物
# 每個函式都在 0..1000 的正方形裡畫一隻，回傳 RGBA 圖層

def _tile():
    img = Image.new("RGBA", (U * SS, U * SS), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def cat(t):
    img, d = _tile()
    main, dark, bl = hx(t["main"]), hx(t["dark"]), hx(t["blush"])
    # 耳朵（先畫，才會被頭蓋住底部）
    d.polygon(poly([(300, 330), (355, 140), (500, 265)]), fill=main)
    d.polygon(poly([(700, 330), (645, 140), (500, 265)]), fill=main)
    d.polygon(poly([(345, 305), (378, 210), (455, 280)]), fill=bl)
    d.polygon(poly([(655, 305), (622, 210), (545, 280)]), fill=bl)
    # 頭
    d.ellipse(box(500, 520, 265, 245), fill=main)
    # 閉著的笑眼
    smile(d, 405, 470, 52, 40, dark)
    smile(d, 595, 470, 52, 40, dark)
    # 鼻子 + 嘴
    d.polygon(poly([(470, 570), (530, 570), (500, 600)]), fill=dark)
    d.arc(box(468, 600, 32, 26), start=340, end=170, fill=dark, width=s(11))
    d.arc(box(532, 600, 32, 26), start=10, end=200, fill=dark, width=s(11))
    blush(d, 320, 560, bl)
    blush(d, 680, 560, bl)
    # 鬍鬚
    for dy, ln in ((-18, 150), (14, 145)):
        d.line([(s(245), s(545 + dy)), (s(245 - ln), s(525 + dy))], fill=dark + (150,), width=s(9))
        d.line([(s(755), s(545 + dy)), (s(755 + ln), s(525 + dy))], fill=dark + (150,), width=s(9))
    # 身體：一小截，讓構圖不會浮空
    d.ellipse(box(500, 880, 210, 150), fill=main)
    return img


def bear(t):
    img, d = _tile()
    main, dark, bl = hx(t["main"]), hx(t["dark"]), hx(t["blush"])
    d.ellipse(box(315, 300, 92), fill=main)
    d.ellipse(box(685, 300, 92), fill=main)
    d.ellipse(box(315, 300, 48), fill=bl)
    d.ellipse(box(685, 300, 48), fill=bl)
    d.ellipse(box(500, 530, 262, 240), fill=main)
    d.ellipse(box(500, 610, 118, 88), fill=bl + (150,))
    smile(d, 408, 490, 48, 38, dark)
    smile(d, 592, 490, 48, 38, dark)
    d.ellipse(box(500, 578, 36, 27), fill=dark)
    d.line([(s(500), s(600)), (s(500), s(628))], fill=dark, width=s(11))
    d.arc(box(470, 628, 30, 24), start=340, end=170, fill=dark, width=s(11))
    d.arc(box(530, 628, 30, 24), start=10, end=200, fill=dark, width=s(11))
    blush(d, 300, 585, bl)
    blush(d, 700, 585, bl)
    d.ellipse(box(500, 890, 205, 145), fill=main)
    return img


def bunny(t):
    img, d = _tile()
    main, dark, bl = hx(t["main"]), hx(t["dark"]), hx(t["blush"])
    d.ellipse(box(408, 245, 62, 190), fill=main)
    d.ellipse(box(592, 245, 62, 190), fill=main)
    d.ellipse(box(408, 258, 31, 140), fill=bl)
    d.ellipse(box(592, 258, 31, 140), fill=bl)
    d.ellipse(box(500, 570, 250, 228), fill=main)
    smile(d, 410, 535, 50, 38, dark)
    smile(d, 590, 535, 50, 38, dark)
    d.polygon(poly([(474, 620), (526, 620), (500, 648)]), fill=bl)
    d.line([(s(500), s(648)), (s(500), s(668))], fill=dark, width=s(10))
    d.arc(box(472, 668, 28, 22), start=340, end=170, fill=dark, width=s(10))
    d.arc(box(528, 668, 28, 22), start=10, end=200, fill=dark, width=s(10))
    blush(d, 312, 620, bl)
    blush(d, 688, 620, bl)
    d.ellipse(box(500, 905, 195, 132), fill=main)
    return img


def fox(t):
    img, d = _tile()
    main, dark, bl = hx(t["main"]), hx(t["dark"]), hx(t["blush"])
    d.polygon(poly([(272, 355), (330, 128), (498, 288)]), fill=main)
    d.polygon(poly([(728, 355), (670, 128), (502, 288)]), fill=main)
    d.polygon(poly([(322, 320), (355, 198), (452, 300)]), fill=dark)
    d.polygon(poly([(678, 320), (645, 198), (548, 300)]), fill=dark)
    # 臉：上寬下窄的圓角三角
    d.ellipse(box(500, 505, 258, 218), fill=main)
    d.polygon(poly([(262, 530), (738, 530), (500, 812)]), fill=main)
    # 白色口鼻
    muzzle = (252, 249, 244, 235)
    d.polygon(poly([(372, 585), (628, 585), (500, 800)]), fill=muzzle)
    d.ellipse(box(500, 600, 128, 62), fill=muzzle)
    smile(d, 398, 490, 50, 38, dark)
    smile(d, 602, 490, 50, 38, dark)
    d.ellipse(box(500, 742, 38, 30), fill=dark)
    blush(d, 300, 560, bl)
    blush(d, 700, 560, bl)
    return img


def panda(t):
    img, d = _tile()
    bl = hx(t["blush"])
    # 貓熊是黑白的，配色固定——跟著主題的 dark 走會讓牠在深色主題整隻變白
    dark = (46, 42, 40)
    white = (252, 250, 246)
    d.ellipse(box(318, 292, 96), fill=dark)
    d.ellipse(box(682, 292, 96), fill=dark)
    d.ellipse(box(500, 530, 268, 245), fill=white)
    # 眼圈：稍微斜一點比較有表情
    d.ellipse(box(388, 505, 78, 92), fill=dark)
    d.ellipse(box(612, 505, 78, 92), fill=dark)
    d.ellipse(box(390, 492, 30, 33), fill=white)
    d.ellipse(box(610, 492, 30, 33), fill=white)
    d.ellipse(box(500, 610, 40, 29), fill=dark)
    d.line([(s(500), s(634)), (s(500), s(658))], fill=dark, width=s(11))
    d.arc(box(472, 658, 30, 24), start=340, end=170, fill=dark, width=s(11))
    d.arc(box(528, 658, 30, 24), start=10, end=200, fill=dark, width=s(11))
    blush(d, 292, 592, bl)
    blush(d, 708, 592, bl)
    d.ellipse(box(500, 895, 208, 145), fill=white)
    return img


ANIMALS = {"cat": cat, "bear": bear, "bunny": bunny, "fox": fox, "panda": panda}
ZH = {"cat": "貓", "bear": "熊", "bunny": "兔", "fox": "狐狸", "panda": "貓熊"}


# --------------------------------------------------------------- 合成
def gradient(size, top, bottom):
    """先做一張很小的漸層再放大——比逐像素快幾百倍，而且夠平滑"""
    g = Image.new("RGB", (1, 256))
    for y in range(256):
        f = y / 255
        g.putpixel((0, y), tuple(int(top[i] + (bottom[i] - top[i]) * f) for i in range(3)))
    return g.resize(size, Image.LANCZOS)


def compose(animal, theme_name, size, layout="desktop"):
    t = THEMES[theme_name]
    w, h = size
    canvas = gradient((w, h), hx(t["bg"][0]), hx(t["bg"][1]))

    tile = ANIMALS[animal](t)

    # 動物佔畫面高度的比例：留白多才像極簡風
    frac = 0.52 if layout == "desktop" else 0.46
    side = int(h * frac)
    tile = tile.resize((side, side), Image.LANCZOS)

    cx = w // 2
    # 桌面：稍微偏上，避開工作列；鎖定畫面：往下壓，把上方留給時鐘
    cy = int(h * 0.46) if layout == "desktop" else int(h * 0.60)
    canvas.paste(tile, (cx - side // 2, cy - side // 2), tile)
    return canvas


def contact_sheet(size=(520, 293)):
    """把所有動物 × 所有配色排成一張總覽圖，方便一次挑"""
    names = list(ANIMALS)
    themes = list(THEMES)
    pad = 12
    w, h = size
    sheet = Image.new("RGB", (w * len(names) + pad * (len(names) + 1),
                              h * len(themes) + pad * (len(themes) + 1)), (255, 255, 255))
    for r, th in enumerate(themes):
        for c, an in enumerate(names):
            sheet.paste(compose(an, th, size), (pad + c * (w + pad), pad + r * (h + pad)))
    return sheet


def main():
    p = argparse.ArgumentParser(description="極簡可愛動物桌布產生器")
    p.add_argument("--animal", choices=list(ANIMALS) + ["all"], default="all")
    p.add_argument("--theme", choices=list(THEMES) + ["all"], default="all")
    p.add_argument("--size", default="2560x1440", help="例如 1920x1080、3840x2160")
    p.add_argument("--layout", choices=["desktop", "lock", "both"], default="both")
    p.add_argument("--contact-sheet", action="store_true", help="只產生總覽圖")
    p.add_argument("--out", default=OUT_DIR)
    a = p.parse_args()

    os.makedirs(a.out, exist_ok=True)

    if a.contact_sheet:
        f = os.path.join(a.out, "總覽.png")
        contact_sheet().save(f)
        print(f"總覽圖：{f}")
        return

    try:
        w, h = (int(x) for x in a.size.lower().split("x"))
    except ValueError:
        print(f"--size 格式不對：{a.size}（要像 1920x1080）", file=sys.stderr)
        return 1

    animals = list(ANIMALS) if a.animal == "all" else [a.animal]
    themes = list(THEMES) if a.theme == "all" else [a.theme]
    layouts = ["desktop", "lock"] if a.layout == "both" else [a.layout]

    n = 0
    for an in animals:
        for th in themes:
            for lay in layouts:
                img = compose(an, th, (w, h), lay)
                f = os.path.join(a.out, f"{ZH[an]}_{th}_{lay}_{w}x{h}.png")
                img.save(f)
                n += 1
    print(f"已產生 {n} 張，位置：{a.out}")


if __name__ == "__main__":
    sys.exit(main() or 0)
