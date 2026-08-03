# install_windows.ps1 — 教學檔案處理「核心工具包」一鍵安裝
#
# 來源：4.20260721,Agent_一鍵安裝檔.docx（三師爸 Sense Bar EP03）
#
# 用法（在本 repo 根目錄）：
#   powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\install_windows.ps1"
#
# 只檢查不安裝：加 -DryRun
#
# 這支腳本嚴格照原始檔案的規則寫：
#   - 只裝核心 10 個套件，不碰選用套件、不碰系統工具（Tesseract/Poppler/ffmpeg）
#   - 不用全域 pip install，一律裝進本 repo 的 .venv
#   - 失敗最多重試一次，然後回報原始錯誤，不自動提權、不自動改用 WSL

param(
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

function Say([string]$m, [string]$c = "White") { Write-Host $m -ForegroundColor $c }
function Step([string]$m) { Say "`n=== $m ===" "Cyan" }
function Ok([string]$m)   { Say "OK   $m" "Green" }
function Warn([string]$m) { Say "注意 $m" "Yellow" }
function Bad([string]$m)  { Say "失敗 $m" "Red" }

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvDir  = Join-Path $RepoRoot ".venv"
$VenvPy   = Join-Path $VenvDir "Scripts\python.exe"
$ReqFile  = Join-Path $RepoRoot "requirements-core.txt"
$Verify   = Join-Path $RepoRoot "verify_core.py"

Say "repo 根目錄：$RepoRoot" "Gray"

foreach ($f in @($ReqFile, $Verify)) {
    if (-not (Test-Path $f)) { Bad "找不到 $f"; exit 1 }
}

function Refresh-Path {
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + `
                [System.Environment]::GetEnvironmentVariable("Path", "User")
}

$report = [ordered]@{}

# ------------------------------------------------- 1. uv
Step "第一步：確認 uv"

$uv = Get-Command "uv" -ErrorAction SilentlyContinue
if ($uv) {
    $uvVer = (& uv --version 2>&1 | Select-Object -First 1)
    Ok "$uvVer（已存在）"
    $report["uv"] = "已存在"
} else {
    Say "  找不到 uv，用 WinGet 安裝官方 astral-sh.uv"
    if ($DryRun) {
        Warn "DryRun：不實際安裝"
        $report["uv"] = "DryRun"
    } else {
        winget install --id astral-sh.uv --accept-source-agreements --accept-package-agreements
        Refresh-Path
        $uv = Get-Command "uv" -ErrorAction SilentlyContinue
        if (-not $uv) {
            Bad "裝完仍找不到 uv。多半是 PATH 還沒更新——請【關掉這個 PowerShell 視窗、重開一個】再跑一次。"
            exit 1
        }
        Ok "uv 已安裝：$(& uv --version)"
        $report["uv"] = "已安裝"
    }
}

# ------------------------------------------------- 2. .venv
Step "第二步：建立 .venv（Python 3.12）"

if ($DryRun) {
    Warn "DryRun：不實際建立"
    $report["Python"] = "DryRun"
} elseif (Test-Path $VenvPy) {
    $pyVer = (& $VenvPy --version 2>&1 | Select-Object -First 1)
    Ok "$pyVer（.venv 已存在，直接沿用）"
    $report["Python"] = "$pyVer"
} else {
    # 本機沒有 3.12 時 uv 會自己下載，不用先裝 Python
    uv venv $VenvDir --python 3.12
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $VenvPy)) {
        Bad "建立 .venv 失敗，離開碼 $LASTEXITCODE"
        exit 1
    }
    $pyVer = (& $VenvPy --version 2>&1 | Select-Object -First 1)
    Ok "$pyVer"
    $report["Python"] = "$pyVer"
}
$report["環境"] = $VenvDir

# ------------------------------------------------- 3. 核心套件
Step "第三步：安裝核心套件（10 個）"

Say "  依 requirements-core.txt 一次裝完，版本交給 uv 解析。"
Say "  不裝選用套件（pandas / pdfplumber / ocrmypdf / yt-dlp…），不裝系統工具。" "Gray"

if ($DryRun) {
    Warn "DryRun：不實際安裝"
    Get-Content $ReqFile | Where-Object { $_ -and $_ -notmatch '^\s*#' } | ForEach-Object { Say "    $_" "Gray" }
    $report["核心套件"] = "DryRun"
} else {
    uv pip install --python $VenvPy -r $ReqFile
    if ($LASTEXITCODE -ne 0) {
        # 規則：最多重試一次。加 --no-cache 排除快取壞掉這個最常見的原因。
        Warn "第一次安裝失敗（離開碼 $LASTEXITCODE），清快取重試一次…"
        uv pip install --python $VenvPy --no-cache -r $ReqFile
        if ($LASTEXITCODE -ne 0) {
            Bad "重試仍失敗（離開碼 $LASTEXITCODE）。"
            Say "  請把上面 uv 印出的原始錯誤完整貼給 Claude 看。" "Yellow"
            Say "  不要自己反覆重裝、也不要改用系統管理員權限硬幹。" "Yellow"
            exit 1
        }
    }
    Ok "核心套件安裝完成"
    $report["核心套件"] = "已安裝"
}

# ------------------------------------------------- 4. 驗證
Step "第四步：匯入驗證"

if ($DryRun) {
    Warn "DryRun：跳過驗證"
} else {
    & $VenvPy $Verify
    $verifyCode = $LASTEXITCODE
    if ($verifyCode -eq 0) { $report["匯入驗證"] = "10/10 成功" }
    else { $report["匯入驗證"] = "有失敗（見上方清單）" }
}

# ------------------------------------------------- 回報
Say "`n核心安裝完成回報：" "Cyan"
foreach ($k in $report.Keys) { Say ("  {0,-12} {1}" -f $k, $report[$k]) }
Say "  選用套件      未安裝（正確）"
Say "  系統工具      未安裝（正確）"

Say "`n下一步：請用 .\.venv\Scripts\python.exe 執行本 repo 的 Python 程式" "Yellow"
Say "例如：.\.venv\Scripts\python.exe verify_core.py" "Gray"

if (-not $DryRun -and $verifyCode -ne 0) { exit 1 }
