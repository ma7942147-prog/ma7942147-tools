# 教學檔案處理「核心工具包」— Windows 安裝腳本
#
# 用法（在本 repo 根目錄執行）：
#   powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\install_windows.ps1"
#
# 做的事：找 uv → 建本 repo 專用 .venv（Python 3.12）→ 裝 requirements-core.txt → 跑 verify_core.py
# 不做的事：不裝選用套件、不裝系統工具（Tesseract／Poppler／ffmpeg）、不動全域 Python

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

# --- 1. 找 uv，沒有就用 WinGet 裝官方 astral-sh.uv ---
$uvStatus = "已存在"
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        Write-Error "找不到 uv，也找不到 winget。請先手動安裝 uv：https://docs.astral.sh/uv/getting-started/installation/"
    }
    Write-Host "[1/4] 找不到 uv，透過 WinGet 安裝 astral-sh.uv ..."
    winget install --id astral-sh.uv --exact --accept-source-agreements --accept-package-agreements
    if ($LASTEXITCODE -ne 0) { Write-Error "WinGet 安裝 uv 失敗（exit code $LASTEXITCODE）。" }
    $uvStatus = "已安裝"

    # 剛裝好的 uv 還不在這個視窗的 PATH 裡，補進來
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                [Environment]::GetEnvironmentVariable("Path", "User")
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        Write-Error "uv 已安裝，但這個視窗還抓不到它。請關掉終端機、重開一個新的，再跑一次本腳本。"
    }
} else {
    Write-Host "[1/4] uv 已存在：$((Get-Command uv).Source)"
}

# --- 2. 用 Python 3.12 建本 repo 專用的 .venv（本機沒有就讓 uv 下載）---
Write-Host "[2/4] 建立 .venv（Python 3.12）..."
uv venv --python 3.12 .venv
if ($LASTEXITCODE -ne 0) { Write-Error "建立 .venv 失敗（exit code $LASTEXITCODE）。" }

# --- 3. 一次裝完核心套件 ---
Write-Host "[3/4] 安裝核心套件（requirements-core.txt）..."
uv pip install --python $venvPython -r requirements-core.txt
if ($LASTEXITCODE -ne 0) { Write-Error "安裝核心套件失敗（exit code $LASTEXITCODE）。請把上面的原始錯誤貼給 Agent 看。" }

# --- 4. 匯入驗證 ---
Write-Host "[4/4] 驗證匯入..."
& $venvPython verify_core.py
$verifyExit = $LASTEXITCODE

$pyVersion = (& $venvPython -c "import sys; print('.'.join(map(str, sys.version_info[:3])))")

Write-Host ""
Write-Host "核心安裝完成回報："
Write-Host "✅ uv：$uvStatus"
Write-Host "✅ Python：$pyVersion"
Write-Host "✅ 環境：$(Join-Path $PSScriptRoot '.venv')"
if ($verifyExit -eq 0) {
    Write-Host "✅ 核心套件：10/10 匯入成功"
} else {
    Write-Host "❌ 核心套件：有匯入失敗，請看上方清單"
}
Write-Host "💡 選用套件：未安裝（正確）"
Write-Host "下一步：請使用 .\.venv\Scripts\python.exe 執行本 repo 的 Python 程式"

exit $verifyExit
