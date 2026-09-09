# 知库每日备份：content/ 变更自动 commit + push
# 由 Windows 计划任务每日 09:00 调用；无变更时静默退出。
# v2（2026-09-09）：根路径由 $PSScriptRoot 推导（原版硬编码 E:\chen\code\knowledge，换机必失败）；
#   push 失败如实记日志并以 exit 1 退出（计划任务可感知）；EAP=Continue——PS 5.1 下 EAP=Stop 会使
#   「git push 2>&1」的 stderr 直接抛异常走 catch，日志只留残缺首行（实测触发）。
# 备份范围说明：_inbox/ 与 _trash/ 在 .gitignore 中，git add 会静默跳过——它们不在本备份覆盖内，冷备份另行处理。
# 注册（等用户在场监督时执行，路径换成实际克隆位置）：
#   schtasks /Create /F /TN "KnowledgeDailyBackup" /TR "powershell.exe -NoProfile -ExecutionPolicy Bypass -File E:\GitHub\knowledge\scripts\daily_backup.ps1" /SC DAILY /ST 09:00
$ErrorActionPreference = "Continue"
# 注：不用 Stop——native 命令 stderr 重定向(2>&1)在 Stop 下会抛假异常；git 结果一律用 $LASTEXITCODE 判定，
# 真正的 .NET 异常（路径不存在等）仍由下方 try/catch 兜底

# 脚本位于 scripts\ 下，仓库根 = 父目录（$PSScriptRoot 为空时回退 MyInvocation，防特殊调用上下文）
$scriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
$root = Split-Path -Parent $scriptDir
$log = Join-Path $root "indexes\backup.log"
# indexes/ 是可随时删除的派生缓存目录，日志写入前确保存在
if (-not (Test-Path (Split-Path $log))) { New-Item -ItemType Directory -Force -Path (Split-Path $log) | Out-Null }

function Log($m) {
    $line = "{0} {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $m
    $line | Out-File $log -Append -Encoding utf8
}

try {
    Push-Location $root
    # content/ 中被 .gitignore 排除的 _inbox/_trash 不会进入本备份（git add 静默跳过 ignored 路径）
    git add content/ 2>$null
    $diff = git diff --cached --quiet; $code = $LASTEXITCODE
    if ($code -ne 0) {
        $msg = "auto-backup: content sync {0}" -f (Get-Date -Format "yyyy-MM-dd")
        git commit -m $msg 2>$null | Out-Null
        if ($LASTEXITCODE -ne 0) { Log "ERROR: git commit failed (exit $LASTEXITCODE)"; exit 1 }
        $pushOut = git push 2>&1
        if ($LASTEXITCODE -eq 0) { Log "committed+pushed: $msg" }
        else { Log ("push FAILED after commit '{0}': {1}" -f $msg, ($pushOut -join " ")); exit 1 }
    } else {
        # 无新提交也尝试 push（可能存在昨日未推成功的本地提交）
        $ahead = git rev-list "@{u}..HEAD" --count 2>$null
        if ($ahead -and [int]$ahead -gt 0) {
            $pushOut = git push 2>&1
            if ($LASTEXITCODE -eq 0) { Log "pushed $ahead pending commit(s)" }
            else { Log ("push FAILED ({0} pending): {1}" -f $ahead, ($pushOut -join " ")); exit 1 }
        } else {
            Log "no changes"
        }
    }
} catch {
    Log "ERROR: $($_.Exception.Message)"
    exit 1
} finally {
    Pop-Location
}
