# set_wallpaper.ps1 — 套用桌布與鎖定畫面（Windows 11）
#
# 用法（在 repo 根目錄）：
#   powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\tools\wallpaper\set_wallpaper.ps1"
#   ... -Animal panda -Theme 夜
#   ... -DesktopOnly          只換桌布，不動鎖定畫面
#   ... -List                 只列出有哪些動物和配色
#
# 動物：cat bear bunny fox panda
# 配色：奶茶 霧藍 抹茶 櫻花 薰衣草 夜
#
# 注意：一定要用 Windows PowerShell 5.1（就是「powershell.exe」）。
# PowerShell 7（pwsh.exe）預設沒有 WinRT，換不了鎖定畫面。

param(
    [ValidateSet("cat", "bear", "bunny", "fox", "panda")] [string]$Animal = "cat",
    [ValidateSet("奶茶", "霧藍", "抹茶", "櫻花", "薰衣草", "夜")] [string]$Theme = "奶茶",
    [switch]$DesktopOnly,
    [switch]$List
)

$ErrorActionPreference = "Stop"

function Say([string]$m, [string]$c = "White") { Write-Host $m -ForegroundColor $c }
function Ok([string]$m)   { Say "OK   $m" "Green" }
function Warn([string]$m) { Say "注意 $m" "Yellow" }
function Bad([string]$m)  { Say "失敗 $m" "Red" }

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot  = (Resolve-Path (Join-Path $ScriptDir "..\..")).Path
$OutDir    = Join-Path $ScriptDir "out"
$VenvPy    = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$Generator = Join-Path $ScriptDir "make_wallpaper.py"

$ZH = @{ cat = "貓"; bear = "熊"; bunny = "兔"; fox = "狐狸"; panda = "貓熊" }

if ($List) {
    Say "動物：cat(貓) bear(熊) bunny(兔) fox(狐狸) panda(貓熊)"
    Say "配色：奶茶 霧藍 抹茶 櫻花 薰衣草 夜"
    Say "`n例：.\tools\wallpaper\set_wallpaper.ps1 -Animal panda -Theme 夜"
    exit 0
}

# 圖片放進 LOCALAPPDATA，不要直接指向 repo 裡的檔案——
# repo 在 Google Drive 上，路徑或同步狀態一變，桌布就會變黑。
$ImgDir = Join-Path $env:LOCALAPPDATA "ma7942147-wallpaper"
New-Item -ItemType Directory -Path $ImgDir -Force | Out-Null

# ---------------------------------------------- 取得螢幕原生解析度
$w, $h = 2560, 1440
try {
    $mon = Get-CimInstance Win32_VideoController |
           Where-Object { $_.CurrentHorizontalResolution } |
           Select-Object -First 1
    if ($mon) {
        $w = [int]$mon.CurrentHorizontalResolution
        $h = [int]$mon.CurrentVerticalResolution
        Say "偵測到螢幕解析度：${w}x${h}" "Gray"
    }
} catch { Warn "抓不到螢幕解析度，用預設 ${w}x${h}" }

# ---------------------------------------------- 準備圖片
# 有 .venv 就現場照你的解析度重畫（最清晰）；沒有就用 repo 裡現成的 2560x1440
function Get-Image([string]$layout) {
    $name = "$($ZH[$Animal])_${Theme}_${layout}_${w}x${h}.png"
    $target = Join-Path $ImgDir $name

    if ((Test-Path $VenvPy) -and (Test-Path $Generator)) {
        & $VenvPy $Generator --animal $Animal --theme $Theme --size "${w}x${h}" --layout $layout --out $ImgDir 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0 -and (Test-Path $target)) { return $target }
        Warn "現場產生失敗，改用 repo 內建的圖"
    }

    $fallback = Join-Path $OutDir "$($ZH[$Animal])_${Theme}_${layout}_2560x1440.png"
    if (-not (Test-Path $fallback)) { Bad "找不到圖片：$fallback"; exit 1 }
    $target = Join-Path $ImgDir (Split-Path $fallback -Leaf)
    Copy-Item $fallback $target -Force
    return $target
}

# ---------------------------------------------- 1. 桌面桌布
Say "`n=== 換桌布 ===" "Cyan"

$desktopImg = Get-Image "desktop"
Say "  圖片：$desktopImg" "Gray"

Set-ItemProperty "HKCU:\Control Panel\Desktop" -Name Wallpaper      -Value $desktopImg
Set-ItemProperty "HKCU:\Control Panel\Desktop" -Name WallpaperStyle -Value "10"  # 10 = 填滿
Set-ItemProperty "HKCU:\Control Panel\Desktop" -Name TileWallpaper  -Value "0"

if (-not ("Wp" -as [type])) {
    Add-Type -TypeDefinition @"
using System.Runtime.InteropServices;
public static class Wp {
    [DllImport("user32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    public static extern bool SystemParametersInfo(int uAction, int uParam, string lpvParam, int fuWinIni);
}
"@
}
# 20 = SPI_SETDESKWALLPAPER，3 = 寫進設定檔 + 立刻通知所有視窗
$null = [Wp]::SystemParametersInfo(20, 0, $desktopImg, 3)
Ok "桌布已套用（$($ZH[$Animal]) / $Theme）"

# ---------------------------------------------- 2. 鎖定畫面
if ($DesktopOnly) {
    Warn "已指定 -DesktopOnly，跳過鎖定畫面"
} else {
    Say "`n=== 換鎖定畫面 ===" "Cyan"

    if ($PSVersionTable.PSEdition -eq "Core") {
        Bad "你現在跑的是 PowerShell 7（pwsh），它沒有 WinRT，換不了鎖定畫面。"
        Say "  請改用 Windows PowerShell 5.1 重跑：" "Yellow"
        Say "    powershell.exe -NoProfile -ExecutionPolicy Bypass -File `".\tools\wallpaper\set_wallpaper.ps1`" -Animal $Animal -Theme $Theme" "Yellow"
    } else {
        $lockImg = Get-Image "lock"
        Say "  圖片：$lockImg" "Gray"
        try {
            # WinRT 的非同步 API 在 PowerShell 裡要自己包一層等待
            [Windows.System.UserProfile.LockScreen, Windows.System.UserProfile, ContentType = WindowsRuntime] | Out-Null
            [Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime] | Out-Null

            $asTaskT = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
                $_.Name -eq "AsTask" -and $_.GetParameters().Count -eq 1 -and
                $_.GetParameters()[0].ParameterType.Name -eq "IAsyncOperation``1" })[0]
            $asTaskA = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
                $_.Name -eq "AsTask" -and $_.GetParameters().Count -eq 1 -and
                -not $_.IsGenericMethod })[0]

            $op   = [Windows.Storage.StorageFile]::GetFileFromPathAsync($lockImg)
            $task = $asTaskT.MakeGenericMethod([Windows.Storage.StorageFile]).Invoke($null, @($op))
            $task.Wait(-1) | Out-Null
            $file = $task.Result

            $act  = [Windows.System.UserProfile.LockScreen]::SetImageFileAsync($file)
            $t2   = $asTaskA.Invoke($null, @($act))
            $t2.Wait(-1) | Out-Null

            Ok "鎖定畫面已套用（登入畫面預設也會跟著變）"
        } catch {
            Bad "鎖定畫面設定失敗：$($_.Exception.Message)"
            Say "  手動改：設定 → 個人化 → 鎖定畫面 → 個人化鎖定畫面選「圖片」→ 瀏覽相片" "Yellow"
            Say "  圖片位置：$lockImg" "Yellow"
        }
    }
}

# ---------------------------------------------- 收尾
Say "`n---------------- 完成 ----------------" "Cyan"
Say "  動物   $($ZH[$Animal]) ($Animal)"
Say "  配色   $Theme"
Say "  解析度 ${w}x${h}"
Say "  圖片   $ImgDir"

Say "`n換一組：" "Yellow"
Say "  .\tools\wallpaper\set_wallpaper.ps1 -Animal panda -Theme 夜" "Gray"
Say "  .\tools\wallpaper\set_wallpaper.ps1 -List        # 看全部選項" "Gray"

Say "`n兩件事先講在前面：" "Yellow"
Say "  1. 鎖定畫面若沒變，多半是「Windows 焦點」還開著——" "Yellow"
Say "     設定 → 個人化 → 鎖定畫面 → 把「個人化鎖定畫面」從「Windows 焦點」改成「圖片」。" "Yellow"
Say "  2. 開機時廠商 LOGO（Dell/ASUS 那個）是主機板韌體畫的，Windows 換不掉。" "Yellow"
