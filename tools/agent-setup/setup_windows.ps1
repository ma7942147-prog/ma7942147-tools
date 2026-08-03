# setup_windows.ps1 — 在 Windows 本機 Claude Code 接上 Obsidian 與 Firebase
#
# 依據：2.AGENT_SETUP_外部工具連接指南.md（三師爸 Sense Bar EP04）
# 用法（在本 repo 根目錄開 PowerShell）：
#
#   powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\tools\agent-setup\setup_windows.ps1" `
#       -VaultPath "C:\Users\你的帳號\Documents\第二大腦"
#
# 只想檢查環境、不真的安裝：加上 -DryRun
#
# 這支腳本刻意「半自動」：每個安裝動作前先印出要做什麼，失敗就停下來回報原始錯誤，
# 不會反覆重試、不會自動要系統管理員權限、不會自動改用 WSL。

param(
    [string]$VaultPath = "",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

function Say([string]$msg, [string]$color = "White") {
    Write-Host $msg -ForegroundColor $color
}
function Step([string]$msg) { Say "`n=== $msg ===" "Cyan" }
function Ok([string]$msg)   { Say "OK   $msg" "Green" }
function Warn([string]$msg) { Say "注意 $msg" "Yellow" }
function Bad([string]$msg)  { Say "失敗 $msg" "Red" }

function Get-Version([string]$exe, [string]$verArg) {
    try { return (& $exe $verArg 2>&1 | Select-Object -First 1) } catch { return $null }
}

$results = [ordered]@{}

# ---------------------------------------------------------------- 第一步：環境檢查
Step "第一步：新電腦檢查（基礎工具）"

$node = Get-Version "node" "--version"
if ($node) {
    Ok "Node.js $node"
    $results["Node.js"] = "$node"
} else {
    Bad "找不到 Node.js。本地 MCP server 靠 npx 啟動，沒有 Node 一定接不起來。"
    Say "  請先裝 Node.js LTS：https://nodejs.org/  裝完【重開終端機】再跑一次這支腳本。" "Yellow"
    exit 1
}

$git = Get-Version "git" "--version"
if ($git) { Ok "$git"; $results["Git"] = "$git" }
else { Warn "找不到 Git（同步 repo 會用到，但不影響 MCP 安裝）"; $results["Git"] = "未安裝" }

$claude = Get-Command "claude" -ErrorAction SilentlyContinue
if ($claude) {
    Ok "Claude Code CLI：$($claude.Source)"
    $results["Claude Code CLI"] = "已安裝"
} else {
    Bad "找不到 claude 指令。請確認 Claude Code 已安裝且在 PATH 裡。"
    exit 1
}

# ---------------------------------------------------------------- 第二步：Obsidian
Step "第二步：接 Obsidian（MCP／本地 stdio／免鑰匙）"

if (-not $VaultPath) {
    Warn "沒有給 -VaultPath，跳過 Obsidian。"
    Say "  vault 路徑就是你 Obsidian 左下角『管理保管庫』看到的那個資料夾，例如：" "Gray"
    Say "  -VaultPath `"C:\Users\你的帳號\Documents\第二大腦`"" "Gray"
    $results["Obsidian MCP"] = "跳過（未指定 vault 路徑）"
} elseif (-not (Test-Path $VaultPath)) {
    Bad "vault 路徑不存在：$VaultPath"
    $results["Obsidian MCP"] = "失敗（路徑不存在）"
} else {
    # 指南安全守則 #5：優先官方專案。Obsidian vault 就是一堆 .md 檔的資料夾，
    # 用官方 @modelcontextprotocol/server-filesystem 指到 vault 即可，不必裝來路不明的第三方 server。
    $vaultFull = (Resolve-Path $VaultPath).Path
    Say "  要裝：@modelcontextprotocol/server-filesystem（官方 MCP server）"
    Say "  指向：$vaultFull"
    Say "  權限：可讀寫這個資料夾裡的檔案（Claude 會幫你改筆記，所以是寫入權限）" "Yellow"

    if ($DryRun) {
        Warn "DryRun：不實際執行"
        $results["Obsidian MCP"] = "DryRun"
    } else {
        # Windows 必須包一層 cmd /c，否則會顯示已安裝但永遠連不上
        claude mcp remove obsidian --scope user 2>&1 | Out-Null
        claude mcp add obsidian --scope user -- cmd /c npx -y `@modelcontextprotocol/server-filesystem $vaultFull
        if ($LASTEXITCODE -eq 0) { Ok "obsidian MCP 已加入（scope: user，每個資料夾都能用）"; $results["Obsidian MCP"] = "已安裝" }
        else { Bad "claude mcp add 失敗，離開碼 $LASTEXITCODE"; $results["Obsidian MCP"] = "失敗" }
    }
}

# ---------------------------------------------------------------- 第三步：Firebase
Step "第三步：接 Firebase（CLI + MCP／登入式 OAuth）"

$fb = Get-Version "firebase" "--version"
if ($fb) {
    Ok "firebase-tools $fb（已安裝）"
} else {
    Say "  要裝：firebase-tools（官方 CLI，全域 npm 套件）"
    if ($DryRun) {
        Warn "DryRun：不實際執行"
    } else {
        npm install -g firebase-tools
        if ($LASTEXITCODE -ne 0) {
            Bad "npm install -g firebase-tools 失敗，離開碼 $LASTEXITCODE"
            Say "  常見原因：權限不足。請用系統管理員身分開 PowerShell 再試一次。" "Yellow"
            $results["Firebase CLI"] = "失敗"
        } else {
            $fb = Get-Version "firebase" "--version"
            Ok "firebase-tools $fb"
        }
    }
}
if ($fb) { $results["Firebase CLI"] = "$fb" }

if ($fb -and -not $DryRun) {
    # Firebase 官方 MCP server 內建在 firebase-tools 裡，不用另外裝套件
    Say "  要裝：firebase experimental:mcp（官方內建 MCP，讀寫專案 my-teaching-tools-77014）"
    claude mcp remove firebase --scope user 2>&1 | Out-Null
    claude mcp add firebase --scope user -- cmd /c firebase experimental:mcp
    if ($LASTEXITCODE -eq 0) { Ok "firebase MCP 已加入"; $results["Firebase MCP"] = "已安裝" }
    else { Bad "claude mcp add firebase 失敗，離開碼 $LASTEXITCODE"; $results["Firebase MCP"] = "失敗" }
} elseif ($DryRun) {
    $results["Firebase MCP"] = "DryRun"
}

# ---------------------------------------------------------------- 第四步：驗收
Step "第四步：驗收"

if (-not $DryRun) {
    Say "目前 MCP 清單："
    claude mcp list
}

Say "`n---------------- 安裝完成回報 ----------------" "Cyan"
foreach ($k in $results.Keys) { Say ("  {0,-18} {1}" -f $k, $results[$k]) }

Say "`n接下來你要做的三件事：" "Yellow"
Say "  1. 【完全關掉 Claude Code 再重開】——不重啟，MCP 不會生效。" "Yellow"
Say "  2. 重開後問 Claude：「你現在看得到哪些 MCP 工具？」應該要看得到 obsidian 和 firebase。" "Yellow"
Say "  3. Firebase 第一次用要登入：在終端機跑 firebase login，瀏覽器授權一次即可。" "Yellow"
Say "`n若 claude mcp list 有項目顯示 failed，八成是 cmd /c 沒包到——本腳本已包，" "Gray"
Say "請把完整錯誤訊息貼給 Claude 看，不要自己反覆重裝。" "Gray"
