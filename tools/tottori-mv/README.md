# tottori-mv — 《金蓮》鳥取風景 MV

用 Python 程式「畫」出鳥取縣 17 處名勝（新海誠風的天空／逆光／雲隙光／鏡面水面），
再跟歌曲、歌詞合成成一支 1920×1080 的 MV。**沒有用到任何外部素材圖，17 張圖都是程式生成的。**

```
tools/tottori-mv/
├─ index.html      場景畫廊 + 歌詞時間軸（打開就能看）
├─ sync.html       🎧 歌詞對拍器：邊聽邊按空白鍵校正每句起始時間
├─ art.py          繪圖引擎（fbm 雜訊、雲、逆光、雲隙光、山稜、水面反射、砂丘風紋、後製）
├─ scenes.py       17 個場景的構圖
├─ render.py       Ken Burns 運鏡 + 交叉溶接 + 歌詞字幕 + 音壓脈動 → mp4
├─ timings.json    ★ 歌詞／場景的時間表（要改對拍就改這個檔）
├─ analyze.py      音壓包絡
├─ structure.py    段落邊界偵測（自相似矩陣 + checkerboard novelty）
├─ beats.py        BPM / 拍點 / 小節格
├─ phrases.py      人聲樂句偵測（中央聲道抽取後找換氣點）
├─ build_sync.py   把 timings.json 的歌詞灌進 sync.html
└─ scenes/         產生好的 17 張 2560×1440 風景圖
```

## 17 景

| # | 場景 | 出現時間 |
|---|---|---|
| 01 | 東鄉湖　夜明け前 | 0:00 |
| 02 | 浦富海岸　夜の波 | 0:11 |
| 03 | 鳥取砂丘　月夜の馬の背 | 0:22 |
| 04 | 鳥取砂丘　砂嵐 | 0:33 |
| 05 | 三德山三佛寺　投入堂 | 0:44 |
| 06 | 大山　暁の黄金 | 0:55 |
| 07 | 白兔海岸　夕日の鳥居 | 1:03 |
| 08 | 雨瀧 | 1:10 |
| 09 | 大山　雪の朝 | 1:18 |
| 10 | 境港　水木しげるロード | 1:30 |
| 11 | 中海　雷鳴 | 1:42 |
| 12 | 皆生溫泉　荒波の海岸 | 1:53 |
| 13 | 鳥取砂丘　黄金の日の出 | 2:03 |
| 14 | 若櫻鐵道　夏雲の田園 | 2:10 |
| 15 | 倉吉　白壁土蔵群 | 2:17 |
| 16 | 大山　天の川 | 2:23 |
| 17 | 賀露港の朝 | 2:37 |

場景順序照著歌詞的情緒走：夜／幻滅 → 砂嵐／崩塌 → 破曉的金色（副歌）→ 雪の荒原（第二段）
→ 雷鳴與荒波 → 黃金日の出（第二次副歌）→ 天の川（Bridge 梵唱）→ 港の朝（尾奏「金蓮開在人間」）。

## 對拍怎麼做的

歌曲本身沒有時間碼，所以時間是從音訊反推的：

1. `structure.py` — 用自相似矩陣 + checkerboard kernel 找段落邊界
   → 11s / 33s / 55s / 80s / 102s / 136s / 146s / 156s
2. `beats.py` — 梳狀濾波搜出拍點（本曲約 112–127 BPM）
3. `phrases.py` — 把左右聲道相減抽出中央聲道（人聲多在正中），
   對 200–3500 Hz 的能量找換氣停頓，抓出 36 個人聲樂句
4. 用這些樂句起點當錨點，把 35 句歌詞排進 8 個段落

尾奏那三句（2:37 / 2:43 / 2:52）是偵測到的三個樂句，對得最準；
中段全編制的地方樂器蓋過人聲，偵測會漏，那幾句是按段落等分排的。

**要對得更準就用 `sync.html`**：把 `song.mp3` 放在同一層打開網頁，
按播放，聽到每句開頭就按一下空白鍵，最後按「匯出 JSON」，
把結果貼回 `timings.json` 的 `lines`，再跑一次 `render.py` 就好。

## 重新輸出

```bash
pip install numpy pillow imageio-ffmpeg
cd tools/tottori-mv
cp /path/to/你的歌.mp3 song.mp3
python3 analyze.py                # 音壓包絡（讓畫面跟著音量脈動，可略）
python3 scenes.py                 # 重畫 17 張圖 → frames/
SCENES=frames python3 render.py tottori_mv.mp4
```

只改歌詞時間的話，不用重畫圖：

```bash
python3 render.py tottori_mv.mp4          # 預設讀 scenes/ 這個資料夾
PREVIEW=53,62 python3 render.py test.mp4  # 只輸出 53–62 秒來試看
```

## 備註

- 歌曲檔（song.mp3）和輸出的 mp4 沒有進 repo（這個 repo 是公開的），只留程式和圖。
- 標題《金蓮》是從歌詞「綻放成金色金蓮」取的，要改就改 `timings.json` 的 `title`。
- 字型用 WenQuanYi Zen Hei；換成別的字型改 `render.py` 的 `FONT`。
