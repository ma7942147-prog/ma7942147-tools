# mv-render — 歌詞 MV 合成器

把「一首歌 + 幾張圖 / 短影片 + 一份歌詞」合成一支 1080p 的歌詞 MV。
第一支作品：**《The One and Only》**（1993 中壢、野狼、中山北路）。

## 為什麼要自己算時間軸

Suno 產出的歌不會附時間碼，如果照歌詞平均分配，字幕常常會「跑在人聲前面」。
所以這個工具不用猜的，直接分析音檔：

| 訊號 | 做法 | 用途 |
|---|---|---|
| 曲速 | onset flux 自相關 | 95.5 BPM，1 小節 ≈ 2.513s |
| 段落邊界 | 24 頻帶對數頻譜的 novelty curve（前後 4 秒餘弦距離） | 找 Verse / Chorus / Bridge 的切點 |
| 人聲活動 | mid/side 抵消：`v = E_mid(250–4kHz) − 1.6·E_side` | 分辨「中置人聲」與「純演奏」 |

關鍵觀察：這首歌的副歌是 wall of sound + 雙軌人聲，聲像很開，
所以 **`v ≈ 0` 但總能量 `e` 很高的區段就是副歌**，
而 `v` 高、`e` 低的區段是主歌 / Bridge（編曲稀疏、人聲裸露）。
靠這組規則就能把整首歌的段落切乾淨。

分析結果與所有時間碼都寫在 `timeline.py` 的註解裡。

## 不讓歌詞早於人聲的三道保險

1. 每句起點一律 **+0.30s** 安全延遲（`timeline.LAG`）——寧可晚，不可早。
2. 字幕再加 280ms 淡入，實際看清楚的時間又往後 0.28s。
3. 句子時間只在**已確認的段落邊界內**分配，永遠不會溢出到前一段。

## 用法

```bash
# 需要 ffmpeg 與 CJK 字型
apt-get install -y ffmpeg fonts-noto-cjk

# 素材放進 assets/：song.mp3 + 圖片 + clip01.mp4
python3 render.py            # 完整輸出 build/MV_The_One_and_Only.mp4
python3 render.py --shots-only   # 只渲染分鏡，方便單獨檢查
python3 make_subs.py         # 只重產 build/lyrics.ass
```

## 檔案

| 檔案 | 內容 |
|---|---|
| `timeline.py` | 段落時間、45 句歌詞時間碼、24 個分鏡（Ken Burns 參數） |
| `make_subs.py` | 產生 ASS 字幕（歌詞 / 片頭字卡 / 片尾字卡） |
| `render.py` | 分鏡渲染 → xfade 串接 → 燒字幕 + 混音 |
| `assets/`, `build/` | 素材與產出，**不進 git**（個人內容） |

## 分鏡設計

24 個鏡頭，0.7s 交叉淡入淡出，轉場起點對齊段落邊界：

- Intro（0–16.3s）片頭字卡 + 書桌鏡頭慢推
- Verse 1 / 2 房間、電話、特寫，慢速推軌
- Pre-Chorus → Chorus 星空、城市夜景、雪中牽手影片
- Pre-Chorus 2 / 間奏 婚禮四格漫畫逐格帶出（呼應「到白頭」）
- Bridge 回到特寫，編曲變薄、鏡頭收窄
- 尾奏 婚禮全頁由上而下慢移，最後回到第一個鏡頭收尾

直式圖片用「模糊背景填滿 + 原圖等比置中」處理，不會有黑邊。
推軌先在 2x 解析度（3840×2160）算完再縮回 1080p，避免 zoompan 的抖動。

## 已知取捨

- `img5_lyriccard.jpg` **沒有用進 MV**：那張圖上燒死了另一首歌的歌詞
  （「因為妳是我唯一 One and Only 的奇蹟」），會和本片字幕打架。
- `img4_stars.jpg` 有裁掉上方 24%，把右上角的舊歌詞裁乾淨後才使用。
