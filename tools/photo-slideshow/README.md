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
| `audio` | 選填，配樂（見下） | 無 |

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

`audio` 欄位：

| 欄位 | 說明 | 預設 |
|---|---|---|
| `file` | 配樂檔路徑（wav/mp3 都可） | 必填（給這個欄位的話） |
| `volume` | 音量倍率，1.0 是原音量 | 1.0 |
| `fade_out` | 影片結束前淡出秒數 | 2.0 |

配樂會自動裁切到跟影片一樣長，超過的部分會被切掉，不夠長會提早結束（沒有自動循環，要循環請先用 `compose_music.py` 或自己用 ffmpeg 的 `-stream_loop` 處理成剛好的長度）。

## 沒有現成音樂可用時：合成一段原創配樂

`compose_music.py` 用正弦波合成一段音樂盒風格的原創小旋律（不是抓網路上的音樂，也不是模仿任何卡通主題曲，純自創、沒有版權疑慮），適合展覽/活動影片墊個輕快底樂：

```
python3 compose_music.py --duration 37.4 --out music.wav
```

`--duration` 建議跟 `build_slideshow.py` 印出來的「約 N 秒」對齊，這樣配樂會剛好淡出在影片結尾。想換旋律就用 `--melody 你的旋律.json`（格式是 `[["C4", 0.5], ["D4", 0.5], ...]`，音名+拍數），或用 `--tempo` 調快慢。做好的 `music.wav` 填進設定檔的 `audio.file` 就能用。

**注意**：這個工具不會、也不能幫你抓現成卡通主題曲的音檔或旋律來用——那些通常有版權。想要那種「聽起來很熟悉」的配樂，只能自己合法取得授權音樂，或像上面這樣用原創旋律代替。

## 照片不進 Git

這個 repo 是公開的，所以照片本身（`photos/` 資料夾）**不要 commit 進來**，用完就留在你自己電腦或 GDrive 工作桌就好。工具資料夾裡已經用 `.gitignore` 擋掉常見的圖片格式與 `output/`。

## 已知案例

- `examples/snoopy-songshan.config.json`：史努比 75 週年快閃展（松山文創園區），敘事順序是入口 → 展場 → 5 幅畫作 → 3 張海報 → 公仔周邊 → 裝置 → 巨型充氣史努比壓軸，無配樂。
- `examples/maruko-songshan.config.json`：櫻桃小丸子小小畫家彩繪特展（松山文創園區 5 號倉庫），敘事順序是展牆全覽 → 兩位配角肖像（丸尾／穗波）→ 一連串小丸子肖像／馬戲團特寫 → 回到主視覺海報收尾，配上 `compose_music.py` 產生的原創音樂盒旋律當配樂。要重現的話記得先跑 `python3 compose_music.py --duration <影片秒數> --out music.wav`，`music.wav` 才會存在。

之後想比照哪個風格剪別的展覽影片，直接複製對應那份改圖片路徑跟文字即可。

## 目前限制

- 轉場目前只有淡入淡出一種（`xfade=fade`），夠用但不炫技；想要別的轉場效果可以改 `build_slideshow.py` 裡 `xfade=transition=fade` 那一行，ffmpeg 支援的轉場清單見 `ffmpeg -h filter=xfade`。
- `compose_music.py` 合成的是單旋律線的音樂盒音色，適合當輕量底樂，不是完整編曲；旋律循環播放，長影片聽久了會覺得重複。
