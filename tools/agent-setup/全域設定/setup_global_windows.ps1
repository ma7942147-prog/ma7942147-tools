# setup_global_windows.ps1 — 把全域設定裝進 Windows 本機的 Claude Code
#
# 依據：3.AI_Agent_全域設定規範.md（三師爸 Sense Bar，2026-07-12）
#
# 用法（在本 repo 根目錄開 PowerShell）：
#
#   powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\tools\agent-setup\全域設定\setup_global_windows.ps1"
#
# 只檢查不安裝：加 -DryRun
# 跳過 chezmoi（不想搞跨電腦同步時）：加 -SkipChezmoi
#
# 這支腳本會做四件事：
#   1. 把 CLAUDE_global.md 裝到 ~/.claude/CLAUDE.md（覆蓋前會先備份）
#   2. 裝 edge-tts 進本 repo 的 .venv
#   3. 裝 chezmoi 並把 ~/.claude/ 的設定納入追蹤
#   4. 印出 Antigravity 要人工貼的步驟（那個沒有設定檔，腳本碰不到）

param(
    [switch]$DryRun,
    [switch]$SkipChezmoi
)

$ErrorActionPreference = "Stop"

function Say([string]$m, [string]$c = "White") { Write-Host $m -ForegroundColor $c }
function Step([string]$m) { Say "`n=== $m ===" "Cyan" }
function Ok([string]$m)   { Say "OK   $m" "Green" }
function Warn([string]$m) { Say "注意 $m" "Yellow" }
function Bad([string]$m)  { Say "失敗 $m" "Red" }

# 本腳本在 <repo>\tools\agent-setup\全域設定\ 之下，往上三層就是 repo 根目錄
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot  = (Resolve-Path (Join-Path $ScriptDir "..\..\..")).Path
$ClaudeDir = Join-Path $HOME ".claude"

Say "repo 根目錄：$RepoRoot" "Gray"
Say "全域設定目錄：$ClaudeDir" "Gray"

$results = [ordered]@{}

# ------------------------------------------------- 1. 全域 CLAUDE.md
Step "第一步：安裝全域 CLAUDE.md"

$src = Join-Path $ScriptDir "CLAUDE_global.md"
$dst = Join-Path $ClaudeDir "CLAUDE.md"

if (-not (Test-Path $src)) {
    Bad "找不到來源檔：$src"
    exit 1
}

Say "  來源：$src"
Say "  目標：$dst"

if ($DryRun) {
    Warn "DryRun：不實際寫入"
    $results["全域 CLAUDE.md"] = "DryRun"
} else {
    if (-not (Test-Path $ClaudeDir)) {
        New-Item -ItemType Directory -Path $ClaudeDir -Force | Out-Null
        Ok "建立目錄 $ClaudeDir"
    }
    # 已經有舊的就先備份，不要無聲蓋掉使用者原本寫的東西
    if (Test-Path $dst) {
        $backup = "$dst.bak-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
        Copy-Item $dst $backup
        Warn "原本已有 CLAUDE.md，已備份到：$backup"
        Say "  如果裡面有你自己加的規則，記得手動併回新檔。" "Yellow"
    }
    Copy-Item $src $dst -Force
    Ok "已寫入 $dst"
    $results["全域 CLAUDE.md"] = "已安裝"
}

# ------------------------------------------------- 2. edge-tts
Step "第二步：安裝 edge-tts（語音回覆）"

$venvPy = Join-Path $RepoRoot ".venv\Scripts\python.exe"

if (-not (Get-Command "uv" -ErrorAction SilentlyContinue)) {
    Warn "找不到 uv，先裝官方 astral-sh.uv"
    if (-not $DryRun) {
        winget install --id astral-sh.uv --accept-source-agreements --accept-package-agreements
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "User") + ";" + `
                    [System.Environment]::GetEnvironmentVariable("Path", "Machine")
    }
}

if (-not (Test-Path $venvPy)) {
    Say "  本 repo 還沒有 .venv，建立中（Python 3.12）"
    if (-not $DryRun) { uv venv (Join-Path $RepoRoot ".venv") --python 3.12 }
}

if ($DryRun) {
    Warn "DryRun：不實際安裝 edge-tts"
    $results["edge-tts"] = "DryRun"
} elseif (Test-Path $venvPy) {
    uv pip install --python $venvPy edge-tts
    if ($LASTEXITCODE -eq 0) {
        Ok "edge-tts 已裝進 $venvPy"
        $results["edge-tts"] = "已安裝"
        Say "  實測合成一句話…"
        & $venvPy (Join-Path $ScriptDir "speak.py") "語音設定完成，可以開始工作了。"
        if ($LASTEXITCODE -eq 0) { Ok "語音實測通過" } else { Warn "語音實測沒過，請把上面的錯誤訊息貼給 Claude 看" }
    } else {
        Bad "edge-tts 安裝失敗，離開碼 $LASTEXITCODE"
        $results["edge-tts"] = "失敗"
    }
} else {
    Bad "建立 .venv 失敗，跳過 edge-tts"
    $results["edge-tts"] = "失敗（無 .venv）"
}

# ------------------------------------------------- 3. chezmoi
Step "第三步：chezmoi（跨電腦同步 Claude Code 設定）"

if ($SkipChezmoi) {
    Warn "已指定 -SkipChezmoi，跳過"
    $results["chezmoi"] = "跳過"
} else {
    # chezmoi 的安裝與初始化都交給專用腳本，這裡不重複一份。
    # （原本這段假設「一定要先有 dotfiles repo 才能 init」——實測是錯的，
    #   chezmoi init 可以純本機跑，遠端之後再補。）
    $czScript = Join-Path $ScriptDir "setup_chezmoi.ps1"
    if (-not (Test-Path $czScript)) {
        Warn "找不到 $czScript，跳過 chezmoi"
        $results["chezmoi"] = "跳過（找不到腳本）"
    } else {
        $czArgs = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $czScript)
        if ($DryRun) { $czArgs += "-DryRun" }
        & powershell.exe @czArgs
        $results["chezmoi"] = if ($LASTEXITCODE -eq 0) { "已處理（見上方輸出）" } else { "失敗（離開碼 $LASTEXITCODE）" }
    }
}

# ------------------------------------------------- 4. Antigravity
Step "第四步：Antigravity（只能人工貼）"

$agFile = Join-Path $ScriptDir "antigravity_system_prompt.md"
Warn "Antigravity 沒有設定檔，腳本無法自動寫入——這一步一定要你自己做："
Say "  1. 開 Antigravity → Settings → Customizations → System Prompt / Custom Instructions"
Say "  2. 打開這個檔案，複製分隔線以下的全部內容："
Say "     $agFile" "Cyan"
Say "  3. 貼進去、存檔"
$results["Antigravity"] = "待人工貼上"

if (-not $DryRun) {
    try { Start-Process notepad.exe $agFile; Ok "已幫你開啟該檔案" } catch { Warn "自動開檔失敗，請手動打開" }
}

# ------------------------------------------------- 回報
Say "`n---------------- 全域設定安裝回報 ----------------" "Cyan"
foreach ($k in $results.Keys) { Say ("  {0,-18} {1}" -f $k, $results[$k]) }

Say "`n接下來：" "Yellow"
Say "  1. 【完全關掉 Claude Code 再重開】，全域 CLAUDE.md 才會生效。" "Yellow"
Say "  2. 重開後說一句「唸出來：設定完成」測試語音。" "Yellow"
Say "  3. Antigravity 的部分記得手動貼（見上面第四步）。" "Yellow"
