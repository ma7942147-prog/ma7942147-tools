# setup_chezmoi.ps1 — 安裝 chezmoi 並把 Claude Code 設定納入跨電腦同步
#
# 用法（在 repo 根目錄）：
#   powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\tools\agent-setup\全域設定\setup_chezmoi.ps1"
#
#   -DotfilesRepo <url>   順便設好遠端（例：https://github.com/你的帳號/dotfiles.git）
#   -DryRun               只看會做什麼，不實際動手
#
# 這支腳本的流程是在 Linux 容器裡用 chezmoi v2.72.0 實跑驗證過的，不是照文件寫的。
# 驗證到的重點都寫在對應的步驟註解裡。

param(
    [string]$DotfilesRepo,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

function Say([string]$m, [string]$c = "White") { Write-Host $m -ForegroundColor $c }
function Step([string]$m) { Say "`n=== $m ===" "Cyan" }
function Ok([string]$m)   { Say "OK   $m" "Green" }
function Warn([string]$m) { Say "注意 $m" "Yellow" }
function Bad([string]$m)  { Say "失敗 $m" "Red" }

function Refresh-Path {
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + `
                [System.Environment]::GetEnvironmentVariable("Path", "User")
}

$ClaudeDir = Join-Path $HOME ".claude"
$report = [ordered]@{}

# ------------------------------------------------- 1. 安裝 chezmoi
Step "第一步：安裝 chezmoi"

$cz = Get-Command chezmoi -ErrorAction SilentlyContinue
if ($cz) {
    Ok "已安裝：$(& chezmoi --version)"
    $report["chezmoi"] = "已存在"
} elseif ($DryRun) {
    Warn "DryRun：不實際安裝"
    $report["chezmoi"] = "DryRun"
} else {
    $installed = $false

    # 先試 winget。套件 ID 是 twpayne.chezmoi（發行者.套件名）。
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Say "  試 winget..."
        winget install --id twpayne.chezmoi --accept-source-agreements --accept-package-agreements 2>&1 | Out-Host
        Refresh-Path
        $installed = [bool](Get-Command chezmoi -ErrorAction SilentlyContinue)
    }

    # winget 沒有或 ID 對不上就用官方安裝腳本，這是 chezmoi 文件寫的 Windows 裝法
    if (-not $installed) {
        Warn "winget 沒裝成，改用官方安裝腳本 get.chezmoi.io/ps1"
        $bin = Join-Path $env:LOCALAPPDATA "chezmoi"
        New-Item -ItemType Directory -Path $bin -Force | Out-Null
        try {
            Invoke-Expression "&{$(Invoke-RestMethod 'https://get.chezmoi.io/ps1')} -b '$bin'"
            # 官方腳本只把執行檔丟進資料夾，不會自己加 PATH
            $userPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
            if ($userPath -notlike "*$bin*") {
                [System.Environment]::SetEnvironmentVariable("Path", "$userPath;$bin", "User")
                Say "  已把 $bin 加進使用者 PATH" "Gray"
            }
            Refresh-Path
            $installed = [bool](Get-Command chezmoi -ErrorAction SilentlyContinue)
        } catch {
            Bad "官方安裝腳本也失敗：$($_.Exception.Message)"
        }
    }

    if (-not $installed) {
        Bad "chezmoi 裝不起來。請把上面的錯誤訊息貼回來。"
        Say "  也可以手動下載：https://github.com/twpayne/chezmoi/releases" "Yellow"
        exit 1
    }
    Ok "已安裝：$(& chezmoi --version)"
    $report["chezmoi"] = "已安裝"
}

if ($DryRun) {
    Warn "`nDryRun 到此為止。拿掉 -DryRun 才會真的初始化。"
    exit 0
}

# ------------------------------------------------- 2. 初始化
Step "第二步：初始化 chezmoi"

# 實測確認：chezmoi init 不需要先有 dotfiles repo。
# 它會建好本機的 source 目錄並在裡面 git init，遠端之後再補就好。
$sourcePath = & chezmoi source-path 2>$null
if ($LASTEXITCODE -eq 0 -and $sourcePath -and (Test-Path $sourcePath)) {
    Ok "已初始化過：$sourcePath"
    $report["初始化"] = "已存在"
} else {
    chezmoi init
    if ($LASTEXITCODE -ne 0) { Bad "chezmoi init 失敗"; exit 1 }
    $sourcePath = & chezmoi source-path
    Ok "已初始化：$sourcePath"
    $report["初始化"] = "已完成"
}
$report["source 目錄"] = $sourcePath

# ------------------------------------------------- 3. 納入追蹤
Step "第三步：把 Claude Code 設定納入追蹤"

if (-not (Test-Path $ClaudeDir)) {
    Warn "$ClaudeDir 不存在——你還沒裝全域設定。"
    Say "  先跑：.\tools\agent-setup\全域設定\setup_global_windows.ps1" "Yellow"
    Say "  或等裝好之後再跑一次這支腳本。" "Yellow"
    $report["追蹤檔案"] = "無（~/.claude 不存在）"
} else {
    # settings.local.json 常含 API key 之類，預設不收進來
    $added = @()
    foreach ($n in @("CLAUDE.md", "settings.json")) {
        $f = Join-Path $ClaudeDir $n
        if (Test-Path $f) {
            chezmoi add $f
            if ($LASTEXITCODE -eq 0) { Ok "已追蹤 .claude\$n"; $added += $n }
            else { Warn "chezmoi add 失敗：$n" }
        }
    }
    if (-not $added) { Warn "$ClaudeDir 裡沒有 CLAUDE.md 或 settings.json" }
    $report["追蹤檔案"] = if ($added) { $added -join ", " } else { "無" }

    $local = Join-Path $ClaudeDir "settings.local.json"
    if (Test-Path $local) {
        Warn "偵測到 settings.local.json，**沒有**收進 chezmoi（裡面常有 API key）。"
        Say "  真的要同步再自己跑：chezmoi add --encrypt `"$local`"" "Yellow"
    }
}

Say "`n目前追蹤中的檔案："
chezmoi managed

# ------------------------------------------------- 4. git commit
Step "第四步：在 source 目錄裡 commit"

# 實測確認：chezmoi init 已經在 source 目錄做過 git init，直接 commit 即可
Push-Location $sourcePath
try {
    git add -A
    $pending = git status --porcelain
    if ($pending) {
        git commit -q -m "同步 Claude Code 設定（$(Get-Date -Format 'yyyy-MM-dd HH:mm')）"
        Ok "已 commit"
        $report["commit"] = "已完成"
    } else {
        Ok "沒有新變動，不用 commit"
        $report["commit"] = "無變動"
    }

    if ($DotfilesRepo) {
        $existing = git remote get-url origin 2>$null
        if ($existing) {
            Warn "origin 已經是 $existing，不覆蓋"
        } else {
            git remote add origin $DotfilesRepo
            Ok "已設定 origin：$DotfilesRepo"
            $branch = git branch --show-current
            Say "  推上去：git -C `"$sourcePath`" push -u origin $branch" "Gray"
            $report["遠端"] = $DotfilesRepo
        }
    } else {
        $existing = git remote get-url origin 2>$null
        if ($existing) {
            $report["遠端"] = $existing
        } else {
            Warn "還沒設遠端——目前只存在這台電腦，換電腦拿不到。"
            $report["遠端"] = "未設定"
        }
    }
} finally { Pop-Location }

# ------------------------------------------------- 回報
Say "`n---------------- chezmoi 設定完成 ----------------" "Cyan"
foreach ($k in $report.Keys) { Say ("  {0,-14} {1}" -f $k, $report[$k]) }

Say "`n日常會用到的四個指令：" "Yellow"
Say "  chezmoi status              看哪些設定被改過但還沒收進來" "Gray"
Say "  chezmoi re-add              把改過的設定收回 chezmoi" "Gray"
Say "  chezmoi cd                  跳到 source 目錄（然後 git push）" "Gray"
Say "  chezmoi apply --force       從 chezmoi 還原設定到家目錄" "Gray"

if (-not $DotfilesRepo -and -not (git -C $sourcePath remote get-url origin 2>$null)) {
    Say "`n還缺一步：建一個 dotfiles repo 才能跨電腦同步" "Yellow"
    Say "  1. 去 GitHub 開一個空 repo，取名 dotfiles，**建議設 private**" "Yellow"
    Say "     （~/.claude 裡可能有 token，公開會外流）" "Yellow"
    Say "  2. 回來跑：" "Yellow"
    Say "     .\tools\agent-setup\全域設定\setup_chezmoi.ps1 -DotfilesRepo https://github.com/你的帳號/dotfiles.git" "Gray"
}

Say "`n換到另一台電腦時，一行就還原：" "Yellow"
Say "  chezmoi init --apply https://github.com/你的帳號/dotfiles.git" "Gray"
