# photo-slideshow

把一組照片做成有轉場、標題卡、字幕的直式（或任意尺寸）影片。原本是為了把逛「史努比 75 週年快閃展（松山文創園區）」拍的照片剪成影片而寫，後來抽成通用工具，之後逛展覽、辦活動想留紀錄都能重複用。

## 需要先裝的東西（每台電腦第一次用時）

```
sudo apt-get install -y ffmpeg fonts-noto-cjk
```

- `ffmpeg`：實際做影片轉場、疊字的引擎
- `fonts-noto-cjk`：讓標題卡、字幕能正確顯示中文（沒裝的話中文字會變方框或報錯）

## 用法

1. 把照片放進一個資料夾，例如 `photos/`
2. 複製 `examples/example.config.json` 改成自己的設定檔（欄位說明見下）
3. 執行：
   ```
   python3 build_slideshow.py 你的設定檔.json
   ```
4. 影片會輸出到設定檔 `output` 指定的路徑

## 設定檔欄位

| 欄位 | 說明 | 預設 |
|---|---|---|
| `output` | 輸出影片路徑（相對於設定檔所在資料夾） | `output/slideshow.mp4` |
| `canvas.width` / `height` | 畫布尺寸。直式社群貼文建議 `1080x1350`（4:5） | 1080×1350 |
| `canvas.fps` | 影格率 | 25 |
| `image_duration` | 每張照片停留秒數 | 3.0 |
| `xfade_duration` | 轉場（淡入淡出）秒數 | 0.6 |
| `font` | 疊字用的字型名稱（用 `fc-list` 查系統有哪些字型） | `Noto Sans CJK TC` |
| `caption` | 燒在每張照片左下角的小字幕，留空字串就不顯示 | 無 |
| `images` | 照片路徑陣列，依此順序播放 | 必填 |
| `title_card` | 選填，開場字卡（見下） | 無 |
| `end_card` | 選填，結尾字卡，格式同 `title_card` | 無 |

`title_card` / `end_card` 欄位：

| 欄位 | 說明 |
|---|---|
| `background` | 背景圖片路徑，會自動模糊＋調暗當底圖 |
| `duration` | 這張卡停留秒數 |
| `dim` | 調暗程度，0~1，數字越大越暗 |
| `lines` | 要顯示的每一行文字（陣列） |
| `sizes` | 對應每行的字級 |
| `colors` | 對應每行的顏色（`white`、`0xF6C945` 這種十六進位都可以） |
| `y` | 對應每行的垂直位置，可用 ffmpeg 的 `h`（畫布高度）表達式，例如 `"h*0.35+110"` |

照片不論直式橫式都會「置中滿版＋背景模糊放大填滿」，不會出現黑邊。

## 照片不進 Git

這個 repo 是公開的，所以照片本身（`photos/` 資料夾）**不要 commit 進來**，用完就留在你自己電腦或 GDrive 工作桌就好。工具資料夾裡已經用 `.gitignore` 擋掉常見的圖片格式與 `output/`。

## 已知案例：史努比松菸快閃展

`examples/snoopy-songshan.config.json` 是實際做過的那支影片的設定檔，記錄了敘事順序（入口 → 展場 → 5 幅畫作 → 3 張海報 → 公仔周邊 → 裝置 → 巨型充氣史努比壓軸）跟字卡文案，之後想比照這個風格剪別的展覽影片，直接複製這份改圖片路徑跟文字即可。

## 目前限制

- 沒有配樂功能。要加音樂的話，先用這個工具產出無聲影片，再自己疊一軌，或之後有需要再回來加 `-i 音樂檔` 的參數。
- 轉場目前只有淡入淡出一種（`xfade=fade`），夠用但不炫技；想要別的轉場效果可以改 `build_slideshow.py` 裡 `xfade=transition=fade` 那一行，ffmpeg 支援的轉場清單見 `ffmpeg -h filter=xfade`。
