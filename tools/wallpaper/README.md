# wallpaper — 極簡可愛動物桌布

用 Pillow 純程式畫的桌布，**不從網路抓圖**——沒有版權問題，解析度可以剛好對上你的螢幕。

5 種動物（貓、熊、兔、狐狸、貓熊）× 6 種配色（奶茶、霧藍、抹茶、櫻花、薰衣草、夜）
× 2 種構圖（桌面／鎖定畫面）＝ 60 張，都在 `out/`。

總覽圖：[`out/總覽.png`](out/總覽.png)

## 套用

在 repo 根目錄開 **Windows PowerShell**（就是 `powershell.exe`，不是 `pwsh.exe`）：

```powershell
# 預設：貓 + 奶茶色
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\tools\wallpaper\set_wallpaper.ps1"

# 換一組
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\tools\wallpaper\set_wallpaper.ps1" -Animal panda -Theme 夜

# 看有哪些選項
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\tools\wallpaper\set_wallpaper.ps1" -List

# 只換桌布，不動鎖定畫面
... -DesktopOnly
```

腳本會：

1. 抓你螢幕的**原生解析度**
2. 有 `.venv` 就照那個解析度**現場重畫**（最清晰）；沒有就用 `out/` 裡現成的 2560×1440
3. 把圖複製到 `%LOCALAPPDATA%\ma7942147-wallpaper\`
4. 設桌布（登錄檔 + `SystemParametersInfo`）
5. 設鎖定畫面（WinRT `LockScreen.SetImageFileAsync`）

**圖片為什麼不直接指向 repo？** 因為 repo 在 Google Drive 上。桌布的登錄檔存的是絕對路徑，
Drive 路徑或同步狀態一變，桌布就會變黑。所以複製一份到 `LOCALAPPDATA` 再指過去。

## 自己產圖

```powershell
# 全部 60 張
.\.venv\Scripts\python.exe tools\wallpaper\make_wallpaper.py

# 指定尺寸（4K）
.\.venv\Scripts\python.exe tools\wallpaper\make_wallpaper.py --size 3840x2160

# 單一組合
.\.venv\Scripts\python.exe tools\wallpaper\make_wallpaper.py --animal fox --theme 抹茶 --layout desktop

# 總覽圖
.\.venv\Scripts\python.exe tools\wallpaper\make_wallpaper.py --contact-sheet
```

要改顏色就改 `make_wallpaper.py` 最上面的 `THEMES`；要改造型就改各動物的函式，
座標是 0..1000 的正方形，好算。

## 三件事先講清楚

**1. 「開機圖片」有三層，只有兩層換得掉。**

| 畫面 | 換得掉嗎 |
|------|----------|
| 廠商 LOGO（Dell／ASUS／MSI，開機最先出現那個） | ❌ 主機板韌體畫的，Windows 管不到 |
| 鎖定畫面（`Win`+`L`、睡醒看到的） | ✅ 這支腳本會換 |
| 登入畫面（輸入密碼那頁） | ✅ 預設跟著鎖定畫面走 |

**2. 鎖定畫面沒變的話，多半是「Windows 焦點」還開著。**
設定 → 個人化 → 鎖定畫面 → 把「個人化鎖定畫面」從「Windows 焦點」改成「圖片」。

**3. 一定要用 Windows PowerShell 5.1。**
PowerShell 7（`pwsh.exe`）預設不支援 WinRT，換不了鎖定畫面。腳本偵測到會直接告訴你。

## 沒有在 Windows 上實測過

`make_wallpaper.py` 產圖的部分在 Linux 容器裡完整跑過、圖也一張張看過。
但 `set_wallpaper.ps1` **沒辦法在這裡測**——容器裡沒有 Windows。
登錄檔路徑、`SystemParametersInfo` 的參數、WinRT 的呼叫方式都是照文件寫的，
第一次跑如果有狀況，把錯誤訊息貼回來就好。

腳本本身不會做破壞性的事：只寫 `HKCU`（你自己的使用者設定，不用系統管理員），
不碰 `HKLM`，也不用 PersonalizationCSP 那種會把「設定」裡的選項鎖死的做法。
不喜歡隨時能在「設定 → 個人化」自己改回去。
