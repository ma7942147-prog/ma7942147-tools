# 教學檔案處理「核心工具包」Windows 安裝腳本
# 依《1.AGENT_SETUP_教學檔案處理工具包.md》：
#   1. 找到 uv；沒有就用 WinGet 裝官方 astral-sh.uv
#   2. 以 Python 3.12 建立「本 repo 專用」的 .venv（本機沒有 3.12 由 uv 下載）
#   3. 依 requirements-core.txt 一次裝完核心套件
#   4. 跑 verify_core.py 做一次匯入驗證
#
# 用法（在本 repo 根目錄）：
#   powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\install_windows.ps1"
#
# 設計原則：絕不 pip install 到全域、失敗最多重試一次、不自動裝選用套件補救。

$ErrorActionPreference = "Stop"

# 一律以本腳本所在資料夾為專案根目錄，不去翻其他磁碟
$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RepoRoot

Write-Host "專案根目錄：$RepoRoot" -ForegroundColor Cyan
Write-Host ""

function Update-PathFromRegistry {
    # winget 裝完後，目前這個 PowerShell 視窗抓的還是舊 PATH，必須重讀
    $machine = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $user = [Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = ($machine, $user, "$env:USERPROFILE\.local\bin" -join ";")
}

# ---------------------------------------------------------------- 1. uv
$uvStatus = "已存在"
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "找不到 uv，正在用 WinGet 安裝官方 astral-sh.uv ..." -ForegroundColor Yellow

    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        Write-Host ""
        Write-Host "[X] 這台電腦沒有 WinGet，無法自動安裝 uv。" -ForegroundColor Red
        Write-Host "    請先更新「應用程式安裝程式」(App Installer)，或到 https://docs.astral.sh/uv/ 手動安裝 uv 後再跑一次。"
        exit 1
    }

    winget install --id astral-sh.uv -e --source winget `
        --accept-package-agreements --accept-source-agreements
    Update-PathFromRegistry
    $uvStatus = "已安裝"

    # 依「最多重試一次」原則：重讀 PATH 後再找一次，還是沒有就停手回報
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        Write-Host ""
        Write-Host "[X] uv 裝完了但這個視窗還是找不到它。" -ForegroundColor Red
        Write-Host "    這是 PATH 沒更新的典型狀況：請「關掉終端機重開」再跑一次本腳本即可。"
        exit 1
    }
}
Write-Host "[OK] uv：$uvStatus（$(uv --version)）" -ForegroundColor Green

# ------------------------------------------------- 2. 建立本 repo 的 .venv
$VenvPath = Join-Path $RepoRoot ".venv"
$VenvPython = Join-Path $VenvPath "Scripts\python.exe"

Write-Host ""
Write-Host "建立 Python 3.12 虛擬環境：$VenvPath" -ForegroundColor Cyan
uv venv --python 3.12 $VenvPath
if ($LASTEXITCODE -ne 0) {
    Write-Host "[X] 建立 .venv 失敗，請把上面的原始錯誤回報給 Agent。" -ForegroundColor Red
    exit 1
}

# ------------------------------------------------------- 3. 安裝核心套件
Write-Host ""
Write-Host "安裝核心套件（來源：requirements-core.txt）..." -ForegroundColor Cyan
uv pip install --python $VenvPython -r (Join-Path $RepoRoot "requirements-core.txt")
if ($LASTEXITCODE -ne 0) {
    Write-Host "[X] 套件安裝失敗，請把上面的原始錯誤回報給 Agent。" -ForegroundColor Red
    Write-Host "    不要自動改裝選用套件或用系統管理員權限重跑。"
    exit 1
}

# ----------------------------------------------------------- 4. 匯入驗證
Write-Host ""
Write-Host "驗證核心套件是否都能匯入 ..." -ForegroundColor Cyan
& $VenvPython (Join-Path $RepoRoot "verify_core.py")
$verifyExit = $LASTEXITCODE

$pythonVersion = (& $VenvPython -c "import sys; print('.'.join(map(str, sys.version_info[:3])))")

Write-Host ""
Write-Host "核心安裝完成回報：" -ForegroundColor Cyan
Write-Host "  uv：$uvStatus"
Write-Host "  Python：$pythonVersion"
Write-Host "  環境：$VenvPath"
if ($verifyExit -eq 0) {
    Write-Host "  核心套件：10/10 匯入成功" -ForegroundColor Green
    Write-Host "  選用套件：未安裝（正確）"
    Write-Host ""
    Write-Host "下一步：請使用 .\.venv\Scripts\python.exe 執行本 repo 的 Python 程式" -ForegroundColor Green
} else {
    Write-Host "  核心套件：有匯入失敗，清單見上方" -ForegroundColor Red
}

exit $verifyExit
