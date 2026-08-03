# 影音「選用工具」Windows 安裝腳本（yt-dlp / ffmpeg / edge-tts / 字幕）
#
# 這一份跟核心工具包是分開的。依《1.AGENT_SETUP_教學檔案處理工具包.md》規則 2，
# 選用工具與系統工具「除非使用者明確點名用途，否則不要裝」——所以這支腳本
# 不會被 install_windows.ps1 自動呼叫，一定要你自己決定要不要跑。
#
# 用法（在本 repo 根目錄，且已先跑過 install_windows.ps1）：
#
#   # 只下載影片：yt-dlp + ffmpeg
#   powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\install_optional_media.ps1"
#
#   # edu-video-maker 整條線：再加文字轉語音
#   powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\install_optional_media.ps1" -EdgeTts
#
#   # 只想抓 YouTube 既有字幕（不需要 ffmpeg）
#   powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\install_optional_media.ps1" -TranscriptOnly
#
# 全部裝進核心那個同一個 .venv，不另開環境、不裝到全域 Python。

[CmdletBinding()]
param(
    # 加裝 edge-tts（文字轉語音，會連線到微軟雲端服務）
    [switch]$EdgeTts,

    # 只裝 youtube-transcript-api：抓「影片本來就有的字幕」，不下載影音、不需要 ffmpeg
    [switch]$TranscriptOnly,

    # 跳過 ffmpeg（例如你已經自己裝過，或暫時不想動系統工具）
    [switch]$SkipFfmpeg
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RepoRoot

$VenvPath = Join-Path $RepoRoot ".venv"
$VenvPython = Join-Path $VenvPath "Scripts\python.exe"

Write-Host "專案根目錄：$RepoRoot" -ForegroundColor Cyan
Write-Host ""

# --------------------------------------------------- 0. 必須先有核心 .venv
if (-not (Test-Path $VenvPython)) {
    Write-Host "[X] 找不到 $VenvPython" -ForegroundColor Red
    Write-Host "    這支腳本是「加裝」用的，要先把核心工具包裝起來："
    Write-Host '    powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\install_windows.ps1"'
    exit 1
}
Write-Host "[OK] 找到核心環境：$VenvPath" -ForegroundColor Green

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "[X] 找不到 uv。請先跑 install_windows.ps1（它會裝 uv），或關掉終端機重開再試。" -ForegroundColor Red
    exit 1
}

# ------------------------------------------------- 1. 決定這次要裝哪些套件
if ($TranscriptOnly) {
    $Packages = @("youtube-transcript-api")
    $NeedFfmpeg = $false
    Write-Host "模式：只抓 YouTube 既有字幕（不下載影音，不需要 ffmpeg）" -ForegroundColor Cyan
} else {
    $Packages = @("yt-dlp")
    $NeedFfmpeg = -not $SkipFfmpeg
    if ($EdgeTts) { $Packages += "edge-tts" }
    Write-Host "模式：下載影音$(if ($EdgeTts) { ' + 文字轉語音' })" -ForegroundColor Cyan
}

Write-Host "要裝的 pip 套件：$($Packages -join ', ')"
Write-Host ""

# ------------------------------------------------------- 2. 裝進同一個 .venv
Write-Host "安裝 pip 套件到 $VenvPath ..." -ForegroundColor Cyan
uv pip install --python $VenvPython @Packages
if ($LASTEXITCODE -ne 0) {
    Write-Host "[X] 套件安裝失敗，請把上面的原始錯誤回報給 Agent。" -ForegroundColor Red
    exit 1
}

# ------------------------------------------------------------- 3. ffmpeg
# ffmpeg 不是 pip 套件，是系統工具。沒有它，yt-dlp 抓高畫質影片會失敗：
# YouTube 的影像和聲音是分開兩軌，合併那一步就是 ffmpeg 在做。
$ffmpegStatus = "未安裝（本次略過）"
$ffmpegJustInstalled = $false

if ($NeedFfmpeg) {
    Write-Host ""
    if (Get-Command ffmpeg -ErrorAction SilentlyContinue) {
        $ffmpegStatus = "已存在"
        Write-Host "[OK] ffmpeg：已存在" -ForegroundColor Green
    } else {
        Write-Host "找不到 ffmpeg，正在用 WinGet 安裝 Gyan.FFmpeg ..." -ForegroundColor Yellow

        if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
            Write-Host "[X] 這台電腦沒有 WinGet，無法自動安裝 ffmpeg。" -ForegroundColor Red
            Write-Host "    yt-dlp 已裝好，但沒有 ffmpeg 就只能下載單軌、無法合併高畫質影音。"
            Write-Host "    請到 https://www.gyan.dev/ffmpeg/builds/ 手動安裝後重開終端機。"
            exit 1
        }

        winget install --id Gyan.FFmpeg -e --source winget `
            --accept-package-agreements --accept-source-agreements
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[X] ffmpeg 安裝失敗，請把上面的原始錯誤回報給 Agent。" -ForegroundColor Red
            Write-Host "    不要用系統管理員權限反覆重跑。"
            exit 1
        }
        $ffmpegStatus = "已安裝"
        $ffmpegJustInstalled = $true
    }
}

# --------------------------------------------------------------- 4. 驗證
Write-Host ""
Write-Host "驗證 ..." -ForegroundColor Cyan

$importMap = @{
    "yt-dlp"                 = "yt_dlp"
    "edge-tts"               = "edge_tts"
    "youtube-transcript-api" = "youtube_transcript_api"
}

$failed = @()
foreach ($pkg in $Packages) {
    $mod = $importMap[$pkg]
    & $VenvPython -c "import $mod" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] $pkg（import $mod）" -ForegroundColor Green
    } else {
        Write-Host "  [X]  $pkg（import $mod）匯入失敗" -ForegroundColor Red
        $failed += $pkg
    }
}

Write-Host ""
Write-Host "選用工具安裝回報：" -ForegroundColor Cyan
Write-Host "  環境：$VenvPath（與核心共用，正確）"
Write-Host "  pip 套件：$($Packages.Count - $failed.Count)/$($Packages.Count) 匯入成功"
if ($NeedFfmpeg) { Write-Host "  ffmpeg：$ffmpegStatus" }

if ($ffmpegJustInstalled) {
    Write-Host ""
    Write-Host "⚠️  ffmpeg 剛裝好，這個視窗的 PATH 還是舊的。" -ForegroundColor Yellow
    Write-Host "    請「關掉終端機重開」，再執行 yt-dlp，否則合併影音那步會失敗。" -ForegroundColor Yellow
}

if ($failed.Count -gt 0) { exit 1 }

Write-Host ""
Write-Host "下一步：用 .\.venv\Scripts\python.exe -m yt_dlp <網址> 下載" -ForegroundColor Green
Write-Host "（走 .venv 裡的 Python，不要用全域 yt-dlp）"
